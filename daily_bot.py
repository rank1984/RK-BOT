import os
import requests
import pandas as pd
from telegram import Bot

# -----------------
# 1️⃣ Secrets
# -----------------
API_KEY = os.getenv("API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not API_KEY or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ API_KEY או TELEGRAM_TOKEN/CHAT_ID לא מוגדרים ב-Secrets")

# -----------------
# 2️⃣ משיכת נתונים מה-API
# -----------------
url = f"https://financialmodelingprep.com/api/v3/stock-screener?priceLowerThan=50&volumeMoreThan=50000&apikey={API_KEY}"

try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    raise RuntimeError(f"❌ לא הצלחנו למשוך נתונים מה-API: {e}")

if not data:
    message = "⚠️ לא נמצאו מניות מתאימות כרגע."
else:
    # -----------------
    # 3️⃣ עיבוד הנתונים
    # -----------------
    df = pd.DataFrame(data)

    # ממיין לפי שינוי צפוי (changesPercentage)
    if 'changesPercentage' in df.columns:
        df_sorted = df.sort_values(by="changesPercentage", ascending=False).head(10)
    else:
        df_sorted = df.head(10)

    # בונה הודעה בעברית
    message = "📈 מניות מומלצות לבדיקה:\n\n"
    for i, row in df_sorted.iterrows():
        symbol = row.get("symbol", "N/A")
        name = row.get("name", "N/A")
        price = row.get("price", "N/A")
        change = row.get("changesPercentage", "N/A")
        message += f"{symbol} - {name}\nמחיר: {price}$, שינוי צפוי: {change}\n\n"

# -----------------
# 4️⃣ שליחת הודעה לטלגרם
# -----------------
bot = Bot(token=TELEGRAM_TOKEN)

try:
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
except Exception as e:
    raise RuntimeError(f"❌ לא הצלחנו לשלוח הודעה לטלגרם: {e}")
