import asyncio
import os
import requests
import pandas as pd
from telegram import Bot

# ====== הגדרות ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
API_KEY = os.environ.get("API_KEY")  # מפתח ל-FMP או API אחר

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN או TELEGRAM_CHAT_ID לא מוגדרים ב-Secrets")

bot = Bot(token=TELEGRAM_TOKEN)

async def send_telegram(msg):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode='HTML')

# ====== פונקציה להביא מניות קטנות ======
def get_small_caps():
    try:
        url = f"https://financialmodelingprep.com/api/v3/stock/actives?apikey={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # סינון מניות קטנות <= 25$
        small_caps = [s for s in data if float(s.get("price", 0)) <= 25]
        df = pd.DataFrame(small_caps)
        if df.empty:
            return None

        # ממיין לפי volume גבוה ו-score (אם יש)
        if 'changes' in df.columns:
            df['Score'] = df['changes']  # ניתן לשנות קריטריון AI Score
        else:
            df['Score'] = 0

        df = df.sort_values(by='Score', ascending=False).head(10)
        return df[['ticker', 'price', 'Score']]
    except Exception as e:
        print("❌ שגיאה בקבלת מניות:", e)
        return None

# ====== פונקציה להכין הודעה ======
def format_message(df):
    if df is None or df.empty:
        return "⚠️ לא נמצאו מניות מתאימות כרגע."
    msg = "📊 מניות פוטנציאליות לפני פתיחת השוק:\n\n"
    for idx, row in df.iterrows():
        msg += f"🔹 {row['ticker']}\n"
        msg += f"מחיר: ${row['price']}\n"
        msg += f"AI Score: {row['Score']}\n\n"
    return msg

# ====== MAIN ======
async def main():
    df = get_small_caps()
    msg = format_message(df)
    await send_telegram(msg)

if __name__ == "__main__":
    asyncio.run(main())
