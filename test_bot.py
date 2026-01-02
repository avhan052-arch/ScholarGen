# File: test_bot.py
import asyncio
from bot import BOT_TOKEN, start_command, button_click
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

async def main():
    # Buat instance aplikasi bot
    application = Application.builder().token(BOT_TOKEN).build()

    # Tambahkan handler
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_click))

    # Jalankan polling
    print("🤖 Bot berjalan secara terpisah (Debug Mode)...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Biarkan jalan terus menerus
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("Bot berhenti.")

if __name__ == "__main__":
    asyncio.run(main())