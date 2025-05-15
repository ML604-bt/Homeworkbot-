import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, ContextTypes,
    filters
)
from aiohttp import web
from handlers import handle_homework
from utils import get_bot_info, get_dynamic_greeting, load_config

# --- Load .env ---
load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Startup Message ---
async def send_startup_message(app):
    greeting = get_dynamic_greeting()
    bot_version, bt_time = get_bot_info()
    routes = app.bot_data.get("ROUTES_MAP", {})
    admins = app.bot_data.get("ADMIN_CHAT_IDS", [])
    webhook_url = os.getenv("WEBHOOK_URL", "Not set")

    message = (
        f"{greeting}\n"
        f"<b>Homework Forwarder Bot</b>\n"
        f"✅ Online (v{bot_version})\n"
        f"🕒 Time: {bt_time} (BTT)\n"
        f"📬 Routes: {len(routes)} active\n"
        f"🌐 Webhook: {webhook_url}"
    )

    if not admins:
        logger.warning("⚠️ No ADMIN_CHAT_IDS found.")
        return

    for admin_id in admins:
        try:
            await app.bot.send_message(chat_id=admin_id, text=message, parse_mode="HTML")
            logger.info(f"✅ Sent to {admin_id}")
        except Exception as e:
            logger.error(f"❌ Could not send to {admin_id}: {e}")

# --- Main Entrypoint ---
async def main():
    bot_token, _, admin_chat_ids, routes_map = load_config()

    app = ApplicationBuilder().token(bot_token).build()

    # Inject routing map and admin list
    app.bot_data["ROUTES_MAP"] = {
        int(src.strip()): int(dst.strip())
        for pair in routes_map if ":" in pair
        for src, dst in [pair.split(":")]
    }
    app.bot_data["ADMIN_CHAT_IDS"] = [int(x.strip()) for x in admin_chat_ids if x.strip()]
    app.bot_data["FORWARDED_LOGS"] = []

    # Message Handler for all supported media
    app.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.VIDEO | filters.VOICE | filters.AUDIO,
        handle_homework
    ))

    # Send startup message only once
    async def post_init(app):
        await send_startup_message(app)

    app.post_init = post_init

    # Run webhook server
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
    )

# --- Run ---
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
