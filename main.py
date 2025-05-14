import os
import logging
import asyncio
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters
)
from handlers import handle_homework  # Import your custom handler function
from utils import get_bot_info, get_dynamic_greeting, load_config

# --- Load Environment Variables ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Parse Routes and Admin IDs from .env ---
ROUTES_MAP = {}
for pair in os.getenv("ROUTES_MAP", "").split(","):
    try:
        src, dst = map(int, pair.strip().split(":"))
        ROUTES_MAP[src] = dst
    except ValueError:
        logger.warning(f"Invalid ROUTES_MAP pair: {pair}")

ADMIN_CHAT_IDS = [
    int(chat_id.strip())
    for chat_id in os.getenv("ADMIN_CHAT_IDS", "").split(",")
    if chat_id.strip().isdigit()
]

# --- Create Application ---
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.bot_data["ROUTES_MAP"] = ROUTES_MAP
application.bot_data["ADMIN_CHAT_IDS"] = ADMIN_CHAT_IDS
application.bot_data["FORWARDED_LOGS"] = []

# --- Send Admin Notification on Startup ---
async def send_startup_message(app):
    bot_version, bt_time = get_bot_info()
    greeting = get_dynamic_greeting()
    message = (
        f"{greeting}\n"
        f"<b>Homework Forwarder Bot</b>\n"
        f"✅ Online (v{bot_version})\n"
        f"🕒 Time: {bt_time} (BTT)\n"
        f"📬 Routes: {len(ROUTES_MAP)} active\n"
        f"🌐 Webhook: {WEBHOOK_URL}/{BOT_TOKEN}"
    )
    for admin_id in ADMIN_CHAT_IDS:
        try:
            await app.bot.send_message(chat_id=admin_id, text=message, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send startup message to {admin_id}: {e}")

# --- Telegram Webhook Handler ---
async def telegram_webhook(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
    return web.Response()

# --- Aiohttp Web App ---
web_app = web.Application()
web_app.router.add_post(f"/{BOT_TOKEN}", telegram_webhook)

# --- Startup & Shutdown Hooks ---
async def on_startup(app):
    await send_startup_message(application)

async def on_shutdown(app):
    logger.info("Shutting down bot...")

web_app.on_startup.append(on_startup)
web_app.on_shutdown.append(on_shutdown)

# --- Add Telegram Handler ---
application.add_handler(MessageHandler(
    filters.TEXT | filters.PHOTO | filters.VIDEO | filters.VOICE | filters.AUDIO,
    handle_homework  # Handle different types of homework (text, photo, etc.)
))

# --- Run App ---
if __name__ == "__main__":
    async def run():
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        logger.info(f"Bot running at http://0.0.0.0:{PORT}")
        while True:
            await asyncio.sleep(3600)  # Keep the bot alive

    asyncio.run(run())
