import os
import logging
import asyncio
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

from handlers import handle_homework
from utils import get_bot_info, get_dynamic_greeting, load_config

# --- Load Env Vars ---
load_dotenv()
PORT = int(os.getenv("PORT", 8080))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- Logging ---
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Aiohttp Web App ---
web_app = web.Application()
application = None  # Global ref to telegram app


# --- STARTUP MESSAGE ---
async def send_startup_message(app):
    greeting = get_dynamic_greeting()
    version, time_btt = get_bot_info()
    routes = app.bot_data.get("ROUTES_MAP", {})
    admins = app.bot_data.get("ADMIN_CHAT_IDS", [])
    webhook_url = os.getenv("WEBHOOK_URL", "Not set")

    msg = (
        f"{greeting}\n"
        f"<b>Homework Forwarder Bot</b>\n"
        f"✅ Online (v{version})\n"
        f"🕒 Time: {time_btt} (BTT)\n"
        f"📬 Routes: {len(routes)} active\n"
        f"🌐 Webhook: {webhook_url}"
    )

    for admin in admins:
        try:
            await app.bot.send_message(chat_id=admin, text=msg, parse_mode="HTML")
            logger.info(f"✅ Startup message sent to {admin}")
        except Exception as e:
            logger.error(f"❌ Could not notify {admin}: {e}")


# --- Webhook Handler ---
def create_telegram_webhook(app_instance):
    async def telegram_webhook(request):
        try:
            data = await request.json()
            update = Update.de_json(data, app_instance.bot)
            await app_instance.process_update(update)
        except Exception as e:
            logger.error(f"Webhook error: {e}")
        return web.Response(text="OK")
    return telegram_webhook


# --- Main Bot Entrypoint ---
async def main():
    global application
    bot_token, _, admin_ids, routes = load_config()

    application = ApplicationBuilder().token(bot_token).build()
    await application.initialize()

    # Inject config into bot_data
    application.bot_data["ROUTES_MAP"] = {
        int(src): int(dst)
        for pair in routes if ":" in pair
        for src, dst in [pair.split(":")]
    }
    application.bot_data["ADMIN_CHAT_IDS"] = [int(x) for x in admin_ids if x.strip()]
    application.bot_data["FORWARDED_LOGS"] = []

    # Add handler
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.VOICE | filters.VIDEO | filters.AUDIO,
        handle_homework
    ))

    # Webhook setup
    web_app.router.add_post("/webhook", create_telegram_webhook(application))
    web_app.router.add_get("/", lambda req: web.Response(text="Bot is alive."))

    # Startup hook
    async def on_startup(app): await send_startup_message(application)
    web_app.on_startup.append(on_startup)

    # Start aiohttp server
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info(f"🚀 Bot is live at http://0.0.0.0:{PORT}")


# --- Entrypoint ---
if __name__ == "__main__":
    asyncio.run(main())
