import os
import json
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8505247790:AAGSQp2sGntSDYMWED0CdGlAbknDbbGnYXM")
ID_FILE = "admin_chat_id.txt"
BASE_URL = "http://localhost:8000"

# Global variables
BOT_ADMIN_TOKEN = None
ADMIN_CHAT_ID = None

# Dictionary to track bot messages for updates
bot_message_tracker = {}

def refresh_admin_token():
    """Refresh admin token by logging in automatically"""
    global BOT_ADMIN_TOKEN
    print("🔄 Refreshing admin token...")
    
    try:
        # Use default admin credentials
        admin_email = "avhan43@gmail.com"
        admin_password = "admin123"
        
        login_url = f"{BASE_URL}/admin/token"
        response = requests.post(login_url, data={
            "username": admin_email,
            "password": admin_password
        })
        
        if response.ok:
            data = response.json()
            BOT_ADMIN_TOKEN = data.get("access_token")
            print("✅ Admin token refreshed successfully!")
            return True
        else:
            print(f"❌ Failed to refresh admin token: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error refreshing admin token: {e}")
        return False

def load_admin_chat_id():
    """Load admin chat ID from file"""
    global ADMIN_CHAT_ID
    if os.path.exists(ID_FILE):
        with open(ID_FILE, "r") as f:
            try:
                ADMIN_CHAT_ID = int(f.read().strip())
                print(f"✅ Loaded admin chat ID: {ADMIN_CHAT_ID}")
            except ValueError:
                print("⚠️ Invalid admin chat ID in file")
                ADMIN_CHAT_ID = None

def save_admin_chat_id(chat_id):
    """Save admin chat ID to file"""
    with open(ID_FILE, "w") as f:
        f.write(str(chat_id))
    print(f"✅ Saved admin chat ID: {chat_id}")

def track_bot_message(request_id, chat_id, message_id):
    """Track bot messages for future updates"""
    bot_message_tracker[request_id] = {
        'chat_id': chat_id,
        'message_id': message_id
    }
    print(f"✅ Tracking message: Request {request_id} -> Chat {chat_id}, Message {message_id}")

def get_tracked_message(request_id):
    """Get tracked message info"""
    return bot_message_tracker.get(request_id)

def remove_tracked_message(request_id):
    """Remove tracked message"""
    if request_id in bot_message_tracker:
        del bot_message_tracker[request_id]
        print(f"🗑️ Removed tracking for request {request_id}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    global ADMIN_CHAT_ID
    chat_id = update.effective_message.chat_id
    ADMIN_CHAT_ID = chat_id
    save_admin_chat_id(chat_id)
    
    await update.message.reply_text(
        f"✅ Bot connected! Your ID: {chat_id}\n"
        f"This ID has been saved automatically."
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks for approve/reject"""
    query = update.callback_query
    await query.answer()
    
    print(f"🔍 Button clicked: {query.data}")
    
    # Validate data
    if not query.data:
        print("⚠️ Empty callback data")
        return
    
    try:
        action, req_id = query.data.split("_")
        request_id = int(req_id)
        print(f"✅ Action: {action}, Request ID: {request_id}")
    except ValueError:
        print(f"❌ Invalid data format: {query.data}")
        await query.edit_message_text(text="⚠️ Error: Invalid button data.")
        return
    
    # Determine endpoint
    if action == "approve":
        endpoint = f"{BASE_URL}/admin/approve_topup/{request_id}"
        status_text = "✅ APPROVED BY ADMIN"
    else:
        endpoint = f"{BASE_URL}/admin/reject_topup/{request_id}"
        status_text = "❌ REJECTED BY ADMIN"
    
    # Ensure admin token is available
    if not BOT_ADMIN_TOKEN:
        print("⚠️ No admin token, refreshing...")
        if not refresh_admin_token():
            await query.edit_message_text(text="❌ ERROR: Admin token unavailable.")
            return
    
    try:
        # Send request to server
        headers = {"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"}
        response = requests.post(endpoint, headers=headers)
        
        # Handle token expiration
        if response.status_code == 401:
            print("⚠️ Token expired, refreshing...")
            if refresh_admin_token():
                headers = {"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"}
                response = requests.post(endpoint, headers=headers)
            else:
                await query.edit_message_text(text="❌ ERROR: Token invalid & Login failed.")
                return
        
        # Update message based on response
        if response.ok:
            # Check if the message has a caption (photo message) or just text
            if query.message.caption:
                # Update caption with status and remove buttons
                await query.edit_message_caption(
                    caption=query.message.caption + f"\n\n<b>STATUS: {status_text}</b>",
                    parse_mode="HTML",
                    reply_markup=None
                )
            else:
                # Update text message with status and remove buttons
                await query.edit_message_text(
                    text=query.message.text + f"\n\n<b>STATUS: {status_text}</b>",
                    parse_mode="HTML",
                    reply_markup=None
                )
            
            print(f"✅ Request {request_id} {action}ed successfully")
        else:
            error_msg = f"❌ Failed: {response.text}"
            if query.message.caption:
                await query.edit_message_caption(caption=query.message.caption + f"\n\n{error_msg}")
            else:
                await query.edit_message_text(text=query.message.text + f"\n\n{error_msg}")

    except Exception as e:
        print(f"❌ Error in button_click: {e}")
        error_msg = f"❌ Error: {str(e)}"
        if query.message.caption:
            await query.edit_message_caption(caption=query.message.caption + f"\n\n{error_msg}")
        else:
            await query.edit_message_text(text=query.message.text + f"\n\n{error_msg}")

async def clear_requests_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear all top-up requests"""
    user_id = update.effective_message.chat_id
    
    # Check if user is admin
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ You don't have access to this command!")
        return
    
    try:
        endpoint = f"{BASE_URL}/admin/clear_all_topup_requests"
        headers = {"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"}
        
        response = requests.post(endpoint, headers=headers)
        
        if response.status_code == 401:
            if refresh_admin_token():
                headers = {"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"}
                response = requests.post(endpoint, headers=headers)
        
        if response.ok:
            response_data = response.json()
            message = response_data.get("message", "All top-up requests have been cleared!")
            await update.message.reply_text(f"✅ {message}")
        else:
            await update.message.reply_text(f"❌ Failed to clear requests: {response.text}")
    
    except Exception as e:
        print(f"❌ Error clearing requests: {e}")
        await update.message.reply_text(f"❌ Error clearing requests: {str(e)}")

def notify_new_topup(amount, user_email, image_filename, request_id):
    """Send notification to Telegram when new top-up request is made"""
    global ADMIN_CHAT_ID
    if not ADMIN_CHAT_ID:
        print("⚠️ No admin chat ID set. Please use /start command in Telegram.")
        return

    file_path = f"uploads/{image_filename}"

    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{request_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{request_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        f"🔔 <b>New Top-Up Request!</b>\n\n"
        f"👤 User: <code>{user_email}</code>\n"
        f"💰 Amount: <b>{amount} Credits</b>\n"
        f"🆔 ID: <code>{request_id}</code>"
    )

    try:
        with open(file_path, 'rb') as photo_file:
            # Send photo with caption and buttons
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                data={
                    "chat_id": str(ADMIN_CHAT_ID),
                    "caption": caption,
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(reply_markup.to_dict())
                },
                files={"photo": (image_filename, photo_file)}
            )

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('ok') and 'result' in response_data:
                    message_info = response_data['result']
                    message_id = message_info.get('message_id')
                    if message_id:
                        track_bot_message(request_id, ADMIN_CHAT_ID, message_id)
                        print(f"✅ Notification with image sent! Message ID: {message_id}")
                    else:
                        print("✅ Notification with image sent! (No message ID)")
                else:
                    print("✅ Notification with image sent!")
            else:
                print(f"❌ Failed to send notification with image: {response.text}")
    except FileNotFoundError:
        print(f"❌ ERROR: Proof file not found at {file_path}")

        # Send text message as fallback
        text = (
            f"🔔 <b>New Top-Up Request!</b>\n\n"
            f"👤 User: <code>{user_email}</code>\n"
            f"💰 Amount: <b>{amount} Credits</b>\n"
            f"🆔 ID: <code>{request_id}</code>\n"
            f"📄 Proof: <code>{image_filename}</code> (File not found)"
        )

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={
                    "chat_id": str(ADMIN_CHAT_ID),
                    "text": text,
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(reply_markup.to_dict())
                }
            )

            if response.status_code == 200:
                print("✅ Fallback text notification sent!")
            else:
                print(f"❌ Failed to send fallback notification: {response.text}")
        except Exception as e:
            print(f"❌ Error sending fallback notification: {e}")
    except Exception as e:
        print(f"❌ Error sending notification with image: {e}")

async def update_bot_message(request_id: int, new_status: str):
    """Update bot message when status changes from admin panel"""
    tracked_msg = get_tracked_message(request_id)
    if not tracked_msg:
        print(f"⚠️ No tracked message for request {request_id}")
        return False

    chat_id = tracked_msg['chat_id']
    message_id = tracked_msg['message_id']

    try:
        # Get updated request info from server
        headers = {"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"}
        response = requests.get(f"{BASE_URL}/admin/topup_requests", headers=headers)

        if response.status_code == 401:
            if refresh_admin_token():
                headers = {"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"}
                response = requests.get(f"{BASE_URL}/admin/topup_requests", headers=headers)

        if response.ok:
            data = response.json()
            request_info = next((r for r in data.get("requests", []) if r["id"] == request_id), None)
            if not request_info:
                print(f"❌ Request {request_id} not found on server")
                return False

            # Create updated caption
            caption = (
                f"🔔 <b>New Top-Up Request!</b>\n\n"
                f"👤 User: <code>{request_info['user_email']}</code>\n"
                f"💰 Amount: <b>{request_info['amount']} Credits</b>\n"
                f"🆔 ID: <code>{request_info['id']}</code>\n\n"
                f"<b>STATUS: {new_status.upper()} BY ADMIN</b>"
            )

            # Update message in Telegram (try to update caption first)
            update_response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageCaption",
                data={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "caption": caption,
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps({"inline_keyboard": []})  # Remove buttons
                }
            )

            # If updating caption fails, try updating text message
            if update_response.status_code != 200:
                update_response = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
                    data={
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "text": caption,  # Use caption as text
                        "parse_mode": "HTML",
                        "reply_markup": json.dumps({"inline_keyboard": []})  # Remove buttons
                    }
                )

            if update_response.status_code == 200:
                response_data = update_response.json()
                if response_data.get('ok'):
                    print(f"✅ Bot message updated for request {request_id}")
                    remove_tracked_message(request_id)
                    return True
                else:
                    print(f"❌ Failed to update message: {response_data}")
                    return False
            else:
                print(f"❌ Failed to contact Telegram API: {update_response.text}")
                return False
        else:
            print(f"❌ Failed to get request data from server: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error updating bot message: {e}")
        return False

def start_bot():
    """Start the bot in a separate thread (for compatibility with main app)"""
    import threading
    print("🔄 Refreshing admin token at startup...")
    success = refresh_admin_token()
    if not success:
        print("❌ Failed to get admin token at startup!")
    else:
        print(f"✅ Token admin ready! Token length: {len(BOT_ADMIN_TOKEN) if BOT_ADMIN_TOKEN else 0}")

    # Load admin chat ID
    load_admin_chat_id()

    def run_bot_thread():
        import asyncio
        from telegram.ext import Application

        # Create and set a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _run_bot():
            application = setup_bot()
            print("🤖 Telegram Bot is starting...")
            try:
                # Initialize the application
                await application.initialize()
                await application.start()

                # Start the updater
                await application.updater.start_polling(drop_pending_updates=True)

                # Keep the application running
                # We'll use a simple sleep loop since run_polling is now running
                try:
                    while True:
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    pass
            except Exception as e:
                print(f"❌ Error in bot polling: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Clean shutdown
                await application.stop()
                await application.shutdown()

        # Run the bot coroutine in the loop
        loop.create_task(_run_bot())

        # Run the event loop
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        finally:
            loop.stop()
            if not loop.is_closed():
                loop.close()

    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    print("🤖 Telegram Bot Thread started...")

def setup_bot():
    """Setup and return the bot application"""
    # Load admin chat ID
    load_admin_chat_id()

    # Refresh admin token
    refresh_admin_token()

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(CommandHandler("clear_requests", clear_requests_command))

    return application

async def run_bot():
    """Run the bot"""
    application = setup_bot()

    print("🤖 Telegram Bot is starting...")
    try:
        await application.run_polling()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Telegram Bot...")

    # For direct execution, just start the bot normally
    start_bot()

    # Keep the main thread alive
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
