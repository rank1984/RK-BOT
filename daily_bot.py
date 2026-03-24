import os
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

# -------------------------
# הגדרות Telegram
# -------------------------
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Telegram TOKEN או CHAT_ID לא מוגדרים!")

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=data)
        if r.status_code != 200:
            print(f"❌ שליחת הודעה נכשלה: {r.text}")
        return r.status_code
    except Exception as e:
        print(f"❌ Exception בשליחת הודעה: {e}")
        return None

# בדיקה
send_message("✅ RK-BOT מוכן! בדיקת חיבור Telegram הצליחה!")

# -------------------------
# הגדרות מסחר
# -------------------------
BUDGET = 250
TARGET_PCT = 0.12   # רווח יעד ~12%
STOP_PCT = 0.03     # סטופ לוס 3%
MAX_STOCKS = 10     # TOP מניות ל-Pre-Market

# -------------------------
# רשימת מניות זולות (לדוגמה)
# אפשר להרחיב/להחליף
# -------------------------
small_stock_list = [
    "AAPL","AMD","NVDA","INTC","TSLA","F","GE","ZM","PLTR","SQ",
    "SPCE","SIRI","GME","AMC","NOK","BB","BBBY","FUBO","XPEV","CLNE"
]

# -------------------------
# פונקציות עזר
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

def ai_score(data):
    if not data:
        return 0
    score = 50 + ((data['last']/data['high'])*25) + min(data['volume']/1_000_000,20) + (data['volatility']*20)
    return round(min(100, score),0)

def levels(last, high):
    entry = round(high*1.01,2)
    target = round(entry*(1+TARGET_PCT),2)
    stop = round(entry*(1-STOP_PCT),2)
    return entry, target, stop

# -------------------------
# Pre-Market – השוק סגור
# -------------------------
pre_market = []
for t in small_stock_list:
    data = fetch_data(t)
    if data and data['last'] <= 20:  # מניות זולות
        score = ai_score(data)
        entry, target, stop = levels(data['last'], data['high'])
        pre_market.append({
            'מניה': t,
            'דירוג': score,
            'מחיר אחרון': data['last'],
            'כניסה': entry,
            'יעד רווח': target,
            'סטופ לוס': stop
        })

if not pre_market:
    send_message("⚠️ PRE-MARKET ריק: לא נמצאו מניות מתאימות!")
else:
    df = pd.DataFrame(pre_market).sort_values(by='דירוג', ascending=False).head(MAX_STOCKS)
    msg = f"🌙 PRE-MARKET TOP {MAX_STOCKS} 🔥\n"
    for _, row in df.iterrows():
        msg += f"{row['מניה']} | דירוג: {row['דירוג']} | אחרון: {row['מחיר אחרון']} | כניסה: {row['כניסה']} | יעד: {row['יעד רווח']} | סטופ: {row['סטופ לוס']}\n"
    send_message(msg)

# -------------------------
# Live Market – בדיקה ידנית
# -------------------------
def live_update(df):
    live_msg = "⚡ עדכון LIVE ⚡\n"
    for _, row in df.iterrows():
        try:
            current_price = yf.Ticker(row['מניה']).history(period='1d')['Close'][-1]
            status = "✅ מוכן לקנייה!" if current_price >= row['כניסה'] else "⏳ ממתין לפריצה..."
            live_msg += f"{row['מניה']} | נוכחי: {current_price} | כניסה: {row['כניסה']} | יעד: {row['יעד רווח']} | סטופ: {row['סטופ לוס']} | {status}\n"
        except:
            live_msg += f"{row['מניה']} | ❌ לא ניתן לקבל נתונים\n"
    send_message(live_msg)

# להרצה ידנית: פשוט תקרא את הפונקציה אחרי פתיחת השוק
# live_update(df)
