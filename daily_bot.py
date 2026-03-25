import os
import requests
import pandas as pd
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# -------------------------
# בדיקת שוק פתוח
# -------------------------
def is_market_open():
    now = datetime.utcnow()
    return now.weekday() < 5 and 13 <= now.hour < 20

# -------------------------
# API חינמי (Financial Modeling Prep)
# -------------------------
URL = "https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey=demo"

try:
    data = requests.get(URL).json()
except:
    send("❌ שגיאה בשליפת נתונים")
    exit()

stocks = []

for s in data[:20]:  # לוקח 20 ראשונים
    try:
        price = float(s["price"])
        change = float(s["changesPercentage"].replace("%",""))
        volume = float(s.get("volume", 0))
        ticker = s["symbol"]

        if 1 <= price <= 20:
            entry = round(price * 1.01, 2)
            target = round(entry * 1.12, 2)
            stop = round(entry * 0.97, 2)

            score = min(100, round(change * 3 + (volume/1_000_000)))

            stocks.append({
                "Ticker": ticker,
                "Score": score,
                "Price": price,
                "Entry": entry,
                "Target": target,
                "Stop": stop,
                "Volume": volume,
                "Change": change
            })
    except:
        continue

# -------------------------
# בדיקה
# -------------------------
if len(stocks) == 0:
    send("⚠️ לא נמצאו מניות גם מה־API")
    exit()

df = pd.DataFrame(stocks).sort_values(by="Score", ascending=False).head(10)

# -------------------------
# הודעה
# -------------------------
if is_market_open():
    msg = "⚡ מניות חמות למסחר עכשיו ⚡\n\n"
else:
    msg = "🌙 מניות לבדיקה לפני פתיחה 🌙\n\n"

for _, r in df.iterrows():
    msg += (
        f"{r['Ticker']} | דירוג: {r['Score']}\n"
        f"מחיר: {r['Price']} | שינוי: {r['Change']}%\n"
        f"נפח: {int(r['Volume']/1_000_000)}M\n"
        f"כניסה: {r['Entry']} | יעד: {r['Target']} | סטופ: {r['Stop']}\n"
        f"----------------------\n"
    )

send(msg)
