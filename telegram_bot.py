import os
import sys
import asyncio
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Load environment variables
load_dotenv()

async def post_init(app: Application):
    """Spawns the background scheduler check loop on bot startup."""
    from modules.telegram_handlers import schedule_loop
    asyncio.create_task(schedule_loop(app))

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or not token.strip() or token.strip() == "isi_token_bot_anda":
        print("=" * 70)
        print("ERROR: TELEGRAM_BOT_TOKEN belum dikonfigurasi di file .env!")
        print("Langkah penyelesaian:")
        print("1. Buat file '.env' di folder root project ini.")
        print("2. Isi dengan format:")
        print("   TELEGRAM_BOT_TOKEN=token_bot_anda")
        print("   ALLOWED_CHAT_IDS=chat_id_anda (opsional)")
        print("=" * 70)
        sys.exit(1)
        
    print("Menginisialisasi Telegram Bot (V4B)...")
    
    # Import handlers
    from modules.telegram_handlers import (
        start_command, help_command, summary_command, owner_command, report_command,
        alert_check_command, daily_on_command, daily_off_command, set_daily_time_command,
        closing_on_command, closing_off_command, set_closing_time_command,
        schedule_status_command, send_now_command,
        top_products_command, stock_command, materials_command,
        production_command, ads_command, text_message_handler
    )
    
    # Build application with post_init hook
    application = Application.builder().token(token).post_init(post_init).build()
    
    # Register core command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("owner", owner_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("alert_check", alert_check_command))
    
    # Register scheduling command handlers
    application.add_handler(CommandHandler("daily_on", daily_on_command))
    application.add_handler(CommandHandler("daily_off", daily_off_command))
    application.add_handler(CommandHandler("set_daily_time", set_daily_time_command))
    application.add_handler(CommandHandler("closing_on", closing_on_command))
    application.add_handler(CommandHandler("closing_off", closing_off_command))
    application.add_handler(CommandHandler("set_closing_time", set_closing_time_command))
    application.add_handler(CommandHandler("schedule_status", schedule_status_command))
    application.add_handler(CommandHandler("send_now", send_now_command))
    
    # Register detail query command handlers
    application.add_handler(CommandHandler("top_products", top_products_command))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(CommandHandler("materials", materials_command))
    application.add_handler(CommandHandler("production", production_command))
    application.add_handler(CommandHandler("ads", ads_command))
    
    # Handle normal text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    
    print("Telegram Bot berjalan aktif secara lokal (Scheduler loop aktif). Tekan Ctrl+C untuk menghentikan.")
    application.run_polling()

if __name__ == "__main__":
    main()
