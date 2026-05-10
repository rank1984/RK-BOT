import os
import requests
import pandas as pd
import telegram
import asyncio

# הגדרות סביבה (מתקבל מ-GitHub Secrets)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
API_KEY = os.environ.get("API_KEY")

async def send_telegram_msg(message):
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')

def get_market_data():
    # סורק מניות בטווח 2-30 דולר עם נפח מינימלי של 200,000 מניות
    url = f"https://financialmodelingprep.com/api/v3/stock-screener?priceMoreThan=2&priceLowerThan=30&volumeMoreThan=200000&exchange=NASDAQ,NYSE&limit=50&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def get_sentiment(symbol):
    # פונקציה לבדיקת סנטימנט (דורש מפתח API תומך, אם לא - מחזיר ניקוד ניטרלי)
    try:
        url = f"https://financialmodelingprep.com/api/v4/historical/social-sentiment?symbol={symbol}&limit=1&apikey={API_KEY}"
        res = requests.get(url).json()
        if res:
            return res[0]['stocktwitsSentiment'] # מחזיר ציון סנטימנט מ-Stocktwits
    except:
        return 0.5
    return 0.5

async def main():
    data = get_market_data()
    if not data:
        await send_telegram_msg("❌ שגיאה במשיכת נתונים מהשרת.")
        return

    df = pd.DataFrame(data)
    
    # חישוב דירוג (Score) - שקלול של שינוי באחוזים ונפח
    df['score'] = (df['changesPercentage'] * 0.7) + (df['volume'] / 1000000 * 0.3)
    
    # מיון לפי הדירוג הגבוה ביותר
    df = df.sort_values(by='score', ascending=False).head(10)

    message = "🚀 <b>רשימת מומנטום יומית (2$-30$)</b>\n"
    message += "<i>דירוג לפי פוטנציאל עלייה מהירה</i>\n\n"

    for i, row in df.iterrows():
        symbol = row['symbol']
        price = row['price']
        change = row['changesPercentage']
        
        # אסטרטגיית כניסה/יציאה בסיסית
        buy_at = round(price * 1.01, 2) # קנייה בפריצה קלה של המחיר הנוכחי
        target = round(price * 1.12, 2) # יעד רווח 12%
        stop = round(price * 0.96, 2)   # סטופ לוס 4%
        
        rank_emoji = "⭐️" if i < 3 else "✅"
        
        message += f"{rank_emoji} <b>{symbol}</b> ({row['name'][:15]})\n"
        message += f"💰 מחיר: ${price} | שינוי: {change:.2f}%\n"
        message += f"🎯 <b>כניסה: ${buy_at} | יעד: ${target} | סטופ: ${stop}</b>\n"
        message += "------------------------\n"

    message += "\n💡 <i>המלצה: אל תשקיע יותר מ-20% מהתקציב במניה אחת.</i>"
    await send_telegram_msg(message)

if __name__ == "__main__":
    asyncio.run(main())
