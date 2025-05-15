import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from keep_alive import keep_alive

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message and message.text:
        await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=message.text)

async def on_startup(app):
    await app.bot.send_message(chat_id=TARGET_CHAT_ID, text="Bot is live! Text forwarding is active.")

def main():
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.post_init = on_startup
    app.run_polling()

if __name__ == '__main__':
    main()
