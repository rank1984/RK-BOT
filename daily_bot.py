 import os
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

# -------------------------
# TELEGRAM
# -------------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# -------------------------
# הגדרות מסחר
# -------------------------
TARGET = 0.12
STOP = 0.03

# -------------------------
# רשימת מניות רחבה יותר 🔥
# -------------------------
TICKERS = [
    "AAPL","AMD","NVDA","INTC","TSLA","F","GE","PLTR","SOFI","NIO",
    "LCID","RIVN","GME","AMC","BB","NOK","SIRI","SNAP","UBER","LYFT",
    "PINS","DKNG","RIOT","MARA","CLNE","SPCE","OPEN","WISH","BBBY","FUBO",
    "XPEV","LI","BABA","JD","T","VZ","KO","PFE","CVNA","AFRM",
    "UPST","SHOP","ROKU","SQ","PYPL","DIS","BA","UAL","CCL","NCLH"
]

# -------------------------
# בדיקת שוק פתוח
# -------------------------
def is_market_open():
    now = datetime.utcnow()
    return now.weekday() < 5 and 13 <= now.hour < 20

# -------------------------
# הבאת נתונים
# -------------------------
def get_data(t):
    try:
        d = yf.Ticker(t)
        h = d.history(period="2d")
        if h.empty:
            return None
        
        price = h["Close"][-1]
        high = h["High"][-1]
        volume = h["Volume"][-1]
        open_price = h["Open"][-1]
        
        change = ((price - open_price) / open_price) * 100
        
        return price, high, volume, change
    except:
        return None

# -------------------------
# דירוג
# -------------------------
def score(price, high, volume, change):
    s = 0
    s += min(volume / 1_000_000, 30)
    s += min(change * 2, 25)
    s += (price / high) * 25
    s += min(((high - price)/price) * 100, 20)
    return round(min(s, 100), 0)

# -------------------------
# רמות מסחר
# -------------------------
def levels(price, high):
    entry = round(high * 1.01, 2)
    target = round(entry * (1 + TARGET), 2)
    stop = round(entry * (1 - STOP), 2)
    return entry, target, stop

# -------------------------
# סריקה
# -------------------------
stocks = []

for t in TICKERS:
    data = get_data(t)
    if not data:
        continue

    price, high, volume, change = data

    # תנאים שונים לפי מצב שוק
    if is_market_open():
        condition = (1 <= price <= 20 and volume > 1_000_000 and change > 2)
    else:
        condition = (1 <= price <= 20)  # 🔥 חשוב: בלי סינון חזק!

    if condition:
        s = score(price, high, volume, change)
        entry, target, stop = levels(price, high)

        stocks.append({
            "Ticker": t,
            "Score": s,
            "Price": round(price, 2),
            "Entry": entry,
            "Target": target,
            "Stop": stop
        })

# -------------------------
# אם עדיין ריק → נציג TOP גם בלי סינון
# -------------------------
if not stocks:
    for t in TICKERS:
        data = get_data(t)
        if not data:
            continue
        
        price, high, volume, change = data
        
        if 1 <= price <= 20:
            s = score(price, high, volume, change)
            entry, target, stop = levels(price, high)

            stocks.append({
                "Ticker": t,
                "Score": s,
                "Price": round(price, 2),
                "Entry": entry,
                "Target": target,
                "Stop": stop
            })

# -------------------------
# טופ 10
# -------------------------
df = pd.DataFrame(stocks).sort_values(by="Score", ascending=False).head(10)

# -------------------------
# הודעה בעברית
# -------------------------
if is_market_open():
    msg = "⚡ מניות למסחר (שוק פתוח) ⚡\n\n"
else:
    msg = "🌙 מניות לבדיקה לפני פתיחה 🌙\n\n"

for _, r in df.iterrows():
    msg += f"""
{r['Ticker']}
דירוג: {r['Score']}
מחיר: {r['Price']}

כניסה: {r['Entry']}
יעד: {r['Target']}
סטופ: {r['Stop']}
-------------------
"""

send(msg)