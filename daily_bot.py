import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime, time

# -------------------------
# Telegram מ-Secrets
# -------------------------
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Telegram TOKEN or CHAT_ID not set in environment variables!")

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=data)
        if r.status_code != 200:
            print(f"❌ Failed to send message: {r.text}")
        else:
            print("✅ Message sent successfully")
    except Exception as e:
        print(f"❌ Exception sending message: {e}")

# -------------------------
# הגדרות מסחר
# -------------------------
BUDGET = 250
MAX_POSITION = 100
TARGET_PCT = 0.10   # רווח יעד ~10%
STOP_PCT = 0.03     # סטופ לוס 3%

# -------------------------
# רשימת מניות "קטנות" אוטומטית
# -------------------------
def fetch_small_stocks(limit=500):
    # כאן אנחנו נשתמש ב-yfinance כדי למשוך tickers מה-S&P500
    try:
        tickers = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
    except Exception:
        # אם דף Wikipedia חסום, נשתמש בדוגמה של כמה מניות פופולריות קטנות
        tickers = ["AAPL","MSFT","TSLA","AMD","NVDA","INTC","FB","NFLX","GOOGL","SQ"]
    small_tickers = []
    for t in tickers:
        try:
            price = yf.Ticker(t).history(period='1d')['Close'][-1]
            if price <= 20:
                small_tickers.append(t)
        except:
            continue
    return small_tickers[:limit]

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
    except:
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
small_stocks = fetch_small_stocks()
if not small_stocks:
    send_message("⚠️ PRE-MARKET EMPTY: No suitable tickers found!")
    exit()

pre_market = []
for t in small_stocks:
    data = fetch_data(t)
    if data:
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

if pre_market:
    df = pd.DataFrame(pre_market).sort_values(by='Score', ascending=False).head(10)
    msg = "🔥 PRE-MARKET TOP 10 🔥\n\n"
    for idx, row in df.iterrows():
        msg += f"{row['Ticker']} | Score: {row['Score']} | Last: {row['Last']} | Entry: {row['Entry']} | Target: {row['Target']} | Stop: {row['Stop']}\n"
    send_message(msg)
else:
    send_message("⚠️ No small stocks found today.")
