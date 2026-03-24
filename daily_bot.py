import os
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# -------------------------
# Telegram setup
# -------------------------
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Telegram TOKEN or CHAT_ID not set!")

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=data)
        if r.status_code != 200:
            print(f"❌ Failed to send message: {r.text}")
        return r.status_code
    except Exception as e:
        print(f"❌ Exception sending message: {e}")
        return None

# Test Telegram
status = send_message("✅ RK-BOT Test message: Telegram connection OK!")
if status != 200:
    raise RuntimeError("❌ Telegram Test failed! Check TOKEN / CHAT_ID / Bot permissions.")

# -------------------------
# Trading config
# -------------------------
BUDGET = 250
TARGET_PCT = 0.12   # רווח יעד 12%
STOP_PCT = 0.03     # סטופ לוס 3%
MAX_STOCKS = 10     # מספר מניות ל-Pre-Market

# -------------------------
# Small stocks list
# -------------------------
# כאן אפשר להוסיף רשימה ידנית או ממקור חיצוני
small_stock_list = [
    "AAPL","AMD","NVDA","INTC","TSLA","F","GE","ZM","PLTR","SQ",
    "SPCE","SIRI","GME","AMC","NOK","BB","BBBY","FUBO","XPEV","CLNE"
]

# -------------------------
# Fetch stock data
# -------------------------
def fetch_data(ticker):
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period='5d', interval='1d')
        if hist.empty:
            return None
        last_price = hist['Close'][-1]
        high = hist['High'][-1]
        low = hist['Low'][-1]
        volume = hist['Volume'][-1]
        volatility = (high - low)/low
        return {'ticker': ticker, 'last': last_price, 'high': high, 'low': low, 'volume': volume, 'volatility': volatility}
    except:
        return None

# -------------------------
# AI Score
# -------------------------
def ai_score(data):
    if not data:
        return 0
    score = 50 + ((data['last']/data['high'])*25) + min(data['volume']/1_000_000,20) + (data['volatility']*20)
    return round(min(100, score),0)

# -------------------------
# Entry/Target/Stop
# -------------------------
def levels(last, high):
    entry = round(high*1.01,2)
    target = round(entry*(1+TARGET_PCT),2)
    stop = round(entry*(1-STOP_PCT),2)
    return entry, target, stop

# -------------------------
# PRE-MARKET TOP 10
# -------------------------
pre_market = []
for t in small_stock_list:
    data = fetch_data(t)
    if data and data['last'] <= 20:  # מניות זולות
        score = ai_score(data)
        entry, target, stop = levels(data['last'], data['high'])
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
    exit()

df = pd.DataFrame(pre_market).sort_values(by='Score', ascending=False).head(MAX_STOCKS)

msg = f"🔥 PRE-MARKET TOP {MAX_STOCKS} 🔥\n"
for _, row in df.iterrows():
    msg += f"{row['Ticker']} | Score: {row['Score']} | Last: {row['Last']} | Entry: {row['Entry']} | Target: {row['Target']} | Stop: {row['Stop']}\n"

send_message(msg)

# -------------------------
# LIVE SIGNALS (סימולציה)
# -------------------------
print("⏳ Waiting for market open... (simulate live trading)")
for i in range(3):  # לדוגמה: שלוש בדיקות
    time.sleep(10)  # מחכה 10 שניות
    live_msg = "⚡ LIVE SIGNALS UPDATE ⚡\n"
    for _, row in df.iterrows():
        live_msg += f"{row['Ticker']} | Entry: {row['Entry']} | Target: {row['Target']} | Stop: {row['Stop']}\n"
    send_message(live_msg)
