import os
import sys
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Load environment variables
load_dotenv()

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
        
    print("Menginisialisasi Telegram Bot...")
    
    # Import handlers
    from modules.telegram_handlers import (
        start_command, help_command, summary_command, report_command,
        top_products_command, stock_command, materials_command,
        production_command, ads_command, text_message_handler
    )
    
    # Build application
    application = Application.builder().token(token).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("top_products", top_products_command))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(CommandHandler("materials", materials_command))
    application.add_handler(CommandHandler("production", production_command))
    application.add_handler(CommandHandler("ads", ads_command))
    
    # Handle text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    
    print("Telegram Bot berjalan aktif secara lokal. Tekan Ctrl+C untuk menghentikan.")
    application.run_polling()

if __name__ == "__main__":
    main()
