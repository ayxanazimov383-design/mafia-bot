import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from google import genai

TELEGRAM_TOKEN = "8985705257:AAFnZWpYCBE7LnX6AgiUAGxjWADPSSFBVlY"
GEMINI_API_KEY = "AQ.Ab8RN6Ip8xl37itGsHObrQ7r1JmlQZlaljTIVErSLBB3E8WGCg"

client = genai.Client(api_key=GEMINI_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я Study AI \n"
        "Отправь мне вопрос по ДЗ, а я объясню простыми словами."
    )


async def ai_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    prompt = f"""
    Ты учебный помощник для школьника.

    Объясняй максимально просто.
    Не используй Markdown.
    Не используй символы *, #, $, ```.

    Формулы пиши обычным текстом.

    Например:
    a² + b² = c²

    Если есть формула, объясни её словами.
    Если это задача, решай по шагам.

    Вопрос:
    {user_text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        await update.message.reply_text(response.text)

    except Exception as e:
        await update.message.reply_text(f"Ошибка ИИ: {e}")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_answer))

    print("Study AI Bot запущен ✅")
    app.run_polling()


if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.new_event_loop())
    main()
    if __name__ == "__main__":
        asyncio.set_event_loop(asyncio.new_event_loop())
        main()