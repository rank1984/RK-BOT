import os
import requests
import pandas as pd
from telegram import Bot

# ====== הגדרות טלגרם ======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN או TELEGRAM_CHAT_ID לא מוגדרים ב-Secrets")

bot = Bot(token=TELEGRAM_TOKEN)

# ====== פונקציה לשליחת הודעה ======
def send_message(text):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode='HTML')

# ====== נתוני מניות - כאן נחליף למקור אמיתי או API ======
# לדוגמה: מגדירים רשימה ידנית של מניות פוטנציאליות
# בשימוש אמיתי – תחליף את זה ל-API שמספק מניות עד $50 עם נפח טוב
data = [
    {"symbol": "ABC", "price": 28.0, "target": 32.0, "stop": 27.0, "score": 94},
    {"symbol": "XYZ", "price": 45.0, "target": 50.0, "stop": 44.0, "score": 90},
    {"symbol": "LMN", "price": 15.0, "target": 18.0, "stop": 14.5, "score": 88},
    {"symbol": "QRS", "price": 38.0, "target": 42.0, "stop": 37.0, "score": 85},
]

# ====== חישוב עלייה צפויה ======
for d in data:
    d["potential_pct"] = round((d["target"] - d["price"]) / d["price"] * 100, 2)

# ====== ממיין לפי עלייה צפויה מהגבוה לנמוך ======
df = pd.DataFrame(data)
df = df.sort_values(by="potential_pct", ascending=False).head(10)

# ====== טבלת HTML בעברית ======
table_text = "<b>מניות פוטנציאליות למסחר:</b>\n\n"
table_text += "מניה | מחיר נוכחי | יעד רווח | סטופ לוס | דירוג AI | עלייה צפויה %\n"
table_text += "-"*60 + "\n"
for _, row in df.iterrows():
    table_text += f"{row['symbol']} | {row['price']}$ | {row['target']}$ | {row['stop']}$ | {row['score']} | {row['potential_pct']}%\n"

# ====== שליחה לטלגרם ======
send_message(table_text)
