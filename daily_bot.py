import yfinance as yf
import pandas as pd
from datetime import datetime, time
from telegram import Bot
import os

# -------------------------
# Telegram מ-Secrets
# -------------------------
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Telegram TOKEN or CHAT_ID not set in environment variables!")

bot = Bot(token=TELEGRAM_TOKEN)

# בדיקה אם הבוט מחובר
try:
    info = bot.get_me()
    print(f"✅ Telegram Bot connected: @{info.username}")
except Exception as e:
    raise ConnectionError(f"❌ Telegram connection failed: {e}")

def send_message(text):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
        print("✅ Message sent successfully")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")

# -------------------------
# הגדרות
# -------------------------
from config import BUDGET, MAX_POSITION, TARGET_PCT, STOP_PCT, TICKERS

# -------------------------
# פונקציות עזר
# -------------------------
def fetch_data(ticker):
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period='2d', interval='5m')
        if hist.empty:
            return None
        last_price = hist['Close'][-1]
        high = hist['High'][-2]
        low = hist['Low'][-2]
        volume = hist['Volume'][-1]
        volatility = (high - low)/low
        return {'ticker': ticker, 'last': last_price, 'high': high, 'low': low, 'volume': volume, 'volatility': volatility}
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def ai_score(data):
    if not data:
        return 0
    score = 50 + ((data['last']/data['high'])*25) + min(data['volume']/1_000_000,20) + (data['volatility']*20)
    return round(min(100, score),0)

def calculate_levels(last, high):
    entry = round(high*1.01,2)
    target = round(entry*(1+TARGET_PCT),2)
    stop = round(entry*(1-STOP_PCT),2)
    return entry, target, stop

# -------------------------
# PRE-MARKET
# -------------------------
pre_market = []

for t in TICKERS:
    data = fetch_data(t)
    if data and data['last'] <= 20:
        score = ai_score(data)
        entry, target, stop = calculate_levels(data['last'], data['high'])
        pre_market.append({
            'Ticker': t,
            'Score': score,
            'Last': data['last'],
            'Entry': entry,
            'Target': target,
            'Stop': stop
        })

if not pre_market:
    send_message("⚠️ PRE-MARKET EMPTY: No suitable tickers found!")
else:
    df = pd.DataFrame(pre_market).sort_values(by='Score', ascending=False).head(10)
    msg = "🔥 PRE-MARKET TOP 10 🔥\n\n"
    for idx, row in df.iterrows():
        msg += f"{row['Ticker']} | Score: {row['Score']} | Last: {row['Last']} | Entry: {row['Entry']} | Target: {row['Target']} | Stop: {row['Stop']}\n"
    send_message(msg)

    # -------------------------
    # LIVE SIGNALS
    # -------------------------
    current_time = datetime.now().time()
    if time(16,30) <= current_time <= time(17,30):
        live_msg = "⚡ LIVE SIGNALS ⚡\n\n"
        live_table = []
        for idx, row in df.iterrows():
            live_data = fetch_data(row['Ticker'])
            if not live_data:
                continue
            live_price = live_data['last']
            status = "BUY READY" if live_price >= row['Entry'] else "WAIT"
            change_pct = round((live_price/row['Entry']-1)*100,2)
            live_table.append({
                'Ticker': row['Ticker'],
                'Entry': row['Entry'],
                'Target': row['Target'],
                'Stop': row['Stop'],
                'Live': live_price,
                'Status': status,
                'Change%': change_pct
            })
        if live_table:
            live_df = pd.DataFrame(live_table).sort_values(by='Status', ascending=False)
            live_msg += live_df.to_string(index=False)
            send_message(live_msg)
        else:
            send_message("⚠️ LIVE SIGNALS EMPTY: No data available.")
