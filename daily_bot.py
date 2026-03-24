import yfinance as yf
import pandas as pd
from datetime import datetime, time
from telegram import Bot
import os

# -------------------------
# Telegram מ־Secrets
# -------------------------
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
bot = Bot(token=TELEGRAM_TOKEN)

def send_message(text):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)

# -------------------------
# הגדרות סיכון
# -------------------------
BUDGET = 250
MAX_POSITION = 100
PROFIT_PCT = 0.03
STOP_PCT = 0.02

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
        return {'ticker': ticker, 'last': last_price, 'high': high, 'low': low, 'volume': volume}
    except:
        return None

def ai_score(last, high, volume):
    score = 50 + ((last/high)*30) + min(volume/1_000_000, 20)
    return round(min(100, score),0)

def calculate_levels(last, high):
    entry = round(high*1.01, 2)
    target = round(entry*(1+PROFIT_PCT),2)
    stop = round(entry*(1-STOP_PCT),2)
    return entry, target, stop

# -------------------------
# רשימת מניות רחבה - לדוגמה
# אפשר להחליף בקובץ CSV או API
# -------------------------
tickers_list = yf.Tickers('AAPL TSLA AMC NIO GME FUBO PLTR BB SNDL NOK SPY QQQ DIA').tickers.keys()

pre_market = []
for t in tickers_list:
    data = fetch_data(t)
    if data and data['last'] <= 20:  # מניות זולות
        score = ai_score(data['last'], data['high'], data['volume'])
        entry, target, stop = calculate_levels(data['last'], data['high'])
        pre_market.append({
            'Ticker': t,
            'Score': score,
            'Last': data['last'],
            'Entry': entry,
            'Target': target,
            'Stop': stop
        })

# בוחרים 10 מניות מובילות
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
        live_price = fetch_data(row['Ticker'])['last']
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
    live_df = pd.DataFrame(live_table).sort_values(by='Status', ascending=False)
    live_msg += live_df.to_string(index=False)
    send_message(live_msg)
