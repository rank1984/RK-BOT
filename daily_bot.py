import os
import requests
import pandas as pd
from telegram import Bot

# 🔹 הגדרות Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# 🔹 הגדרת ה-API של FMP (חינמי)
API_KEY = os.environ.get("API_KEY")  # המפתח החינמי שלך
url = f"https://financialmodelingprep.com/api/v3/stock-screener?marketCapMoreThan=0&volumeMoreThan=50000&priceLowerThan=50&apikey={API_KEY}"

try:
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"❌ לא הצלחנו למשוך נתונים מה-API: {e}")
    raise SystemExit

# 🔹 בדיקה אם יש נתונים
if not data:
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="⚠️ לא נמצאו מניות מתאימות כרגע")
    raise SystemExit

# 🔹 יצירת DataFrame ומיון לפי שינוי יומי (או פוטנציאל)
df = pd.DataFrame(data)
if 'changesPercentage' in df.columns:
    df['changesPercentage'] = df['changesPercentage'].str.replace('%','').astype(float)
    df = df.sort_values(by='changesPercentage', ascending=False)
else:
    df['changesPercentage'] = 0

# 🔹 בוחרים את 20 הראשונים
df_top = df.head(20)
# 🔹 בוחרים רק עמודות רלוונטיות
df_top = df_top[['symbol','name','price','changesPercentage','volume']]

# 🔹 הפיכת הטבלה לטקסט קריא בעברית
message = "📊 מניות עם פוטנציאל:\n\n"
for i, row in df_top.iterrows():
    message += f"{row['symbol']} - {row['name']}\nמחיר: ${row['price']}, שינוי: {row['changesPercentage']}%, נפח: {row['volume']}\n\n"

# 🔹 שליחת ההודעה ל-Telegram
bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
