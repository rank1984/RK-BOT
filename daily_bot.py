import os
import requests
import pandas as pd
from telegram import Bot

# --- Telegram ---
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

def send(msg):
    bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')

# --- API ---
API_KEY = os.getenv("API_KEY")
URL = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={API_KEY}"

# --- הבאת נתונים ---
try:
    response = requests.get(URL)
    if response.status_code != 200:
        send(f"❌ שגיאת API: {response.status_code}")
        exit()
    data = response.json()
except Exception as e:
    send(f"❌ שגיאת API: {e}")
    exit()

# --- טיפול במקרה שאין נתונים ---
if not isinstance(data, list):
    send(f"❌ בעיית API:\n{data}")
    data = []

stocks = []

# --- יצירת רשימת מניות לפני פתיחת השוק ---
for s in list(data)[:20]:  # עד 20 מניות
    try:
        ticker = s.get("symbol")
        price = float(s.get("price", 0))
        change_str = s.get("changesPercentage", "0%").replace("%","")
        change = float(change_str)
        volume = float(s.get("volume",0))

        if 1 <= price <= 25:  # אפשר לשנות ל-25$ כדי לקבל יותר מניות
            entry = round(price*1.01,2)
            target = round(entry*1.12,2)
            stop = round(entry*0.97,2)
            score = min(100, round(change*3 + (volume/1_000_000)))

            stocks.append({
                "מניה": ticker,
                "מחיר נוכחי": price,
                "שינוי %": change,
                "נפח": volume,
                "כניסה": entry,
                "יעד": target,
                "סטופ": stop,
                "דירוג": score
            })
    except:
        continue

# --- אם אין מניות בטווח המחיר, הצג את ה-10 הראשונות מכל שינוי ---
if len(stocks) == 0:
    for s in list(data)[:10]:
        ticker = s.get("symbol")
        price = float(s.get("price",0))
        change_str = s.get("changesPercentage","0%").replace("%","")
        change = float(change_str)
        volume = float(s.get("volume",0))
        entry = round(price*1.01,2)
        target = round(entry*1.12,2)
        stop = round(entry*0.97,2)
        score = round(change*3 + (volume/1_000_000))
        stocks.append({
            "מניה": ticker,
            "מחיר נוכחי": price,
            "שינוי %": change,
            "נפח": volume,
            "כניסה": entry,
            "יעד": target,
            "סטופ": stop,
            "דירוג": score
        })

# --- שליחת הודעה לטלגרם ---
if len(stocks) > 0:
    df = pd.DataFrame(stocks).sort_values(by='דירוג', ascending=False)
    msg = "<b>⚡ מניות מומלצות לפני פתיחת השוק:</b>\n\n"
    for i,row in df.iterrows():
        msg += (f"{row['מניה']}: מחיר {row['מחיר נוכחי']}$ | "
                f"שינוי {row['שינוי %']}% | "
                f"כניסה {row['כניסה']}$ | "
                f"יעד {row['יעד']}$ | "
                f"סטופ {row['סטופ']}$\n")
    send(msg)
else:
    send("⚠️ לא נמצאו מניות מתאימות כרגע.")
