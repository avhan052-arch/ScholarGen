import os
import json
import threading
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- KONFIGURASI BOT ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ID_FILE = "admin_chat_id.txt"

# --- KONFIGURASI ADMIN (AUTO LOGIN) ---
ADMIN_EMAIL = "avhan43@gmail.com"
ADMIN_PASSWORD = "123"

BOT_ADMIN_TOKEN = None
BASE_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "http://localhost:8000")

# --- FUNGSI LOGIN OTOMATIS ---
def refresh_admin_token():
    global BOT_ADMIN_TOKEN
    print(f"🔄 Mencoba mengambil Token Admin otomatis...")
    print(f"🔍 DEBUG: BASE_URL: {BASE_URL}")
    print(f"🔍 DEBUG: ADMIN_EMAIL: {ADMIN_EMAIL}")
    print(f"🔍 DEBUG: ADMIN_PASSWORD: {'[HIDDEN]' if ADMIN_PASSWORD else '[EMPTY]'}")
    try:
        login_url = f"{BASE_URL}/admin/token"
        print(f"📡 DEBUG: Attempting to connect to: {login_url}")
        res = requests.post(login_url, data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        print(f"📡 DEBUG: Login response status: {res.status_code}")
        print(f"📡 DEBUG: Login response text: {res.text}")

        if res.ok:
            data = res.json()
            BOT_ADMIN_TOKEN = data.get("access_token")
            print(f"✅ Token Admin berhasil didapatkan! Token length: {len(BOT_ADMIN_TOKEN) if BOT_ADMIN_TOKEN else 0}")
            return True
        else:
            print(f"❌ Gagal Login Admin: {res.text}")
            return False
    except Exception as e:
        print(f"❌ Error saat koneksi ke Server Login: {e}")
        import traceback
        print(f"❌ Error traceback: {traceback.format_exc()}")
        return False

# --- MUAT ID ADMIN SAAT STARTUP ---
ADMIN_CHAT_ID = 7779707348
if os.path.exists(ID_FILE):
    with open(ID_FILE, "r") as f:
        try:
            ADMIN_CHAT_ID = int(f.read().strip())
            print(f"📂 Admin Chat ID dimuat otomatis: {ADMIN_CHAT_ID}")
        except ValueError:
            print("⚠️ File ID rusak, silakan ketik /start lagi.")

# --- FUNGSI HANDLER TELEGRAM ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_CHAT_ID
    ADMIN_CHAT_ID = update.effective_message.chat_id
    with open(ID_FILE, "w") as f:
        f.write(str(ADMIN_CHAT_ID))
    await update.message.reply_text(
        f"✅ Bot terhubung! ID Anda: {ADMIN_CHAT_ID}.\nID ini telah disimpan otomatis."
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani klik tombol Approve/Reject"""
    query = update.callback_query
    await query.answer() # Acknowledge dulu biar loading berhenti

    print(f"🔍 DEBUG: Button clicked - Query data: {query.data}")
    print(f"🔍 DEBUG: Current BOT_ADMIN_TOKEN: {'Available' if BOT_ADMIN_TOKEN else 'NOT AVAILABLE'}")
    print(f"🔍 DEBUG: Query message has caption: {bool(query.message.caption)}")
    print(f"🔍 DEBUG: Query message has reply_markup: {bool(query.message.reply_markup)}")

    # 1. Validasi Data
    if not query.data:
        print("⚠️ Callback data kosong.")
        return

    try:
        action, req_id = query.data.split("_")
        request_id = int(req_id)
        print(f"✅ DEBUG: Action: {action}, Request ID: {request_id}")
    except ValueError:
        print(f"❌ Error format data: {query.data}")
        await query.edit_message_text(text="⚠️ Error: Format data tombol tidak valid.")
        return

    # 2. Tentukan Endpoint
    if action == "approve":
        endpoint = f"{BASE_URL}/admin/approve_topup/{request_id}"
        text_success = "✅ Top Up Disetujui!"
        print(f"✅ DEBUG: Using approve endpoint: {endpoint}")
    else:
        endpoint = f"{BASE_URL}/admin/reject_topup/{request_id}"
        text_success = "❌ Top Up Ditolak!"
        print(f"✅ DEBUG: Using reject endpoint: {endpoint}")

    try:
        # 3. Kirim Request ke Server
        print(f"📡 DEBUG: Sending request to {endpoint}")
        print(f"📡 DEBUG: Authorization header: Bearer {'[TOKEN]' if BOT_ADMIN_TOKEN else '[MISSING]'}")
        res = requests.post(endpoint, headers={"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"})
        print(f"📡 DEBUG: Response status: {res.status_code}")
        print(f"📡 DEBUG: Response text: {res.text}")

        # 4. Handle jika Token Expired (401)
        if res.status_code == 401:
            print("⚠️ Token Admin kadaluarsa. Melakukan Auto-Login...")
            if refresh_admin_token():
                print("📡 DEBUG: Retrying request with new token...")
                res = requests.post(endpoint, headers={"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"})
                print(f"📡 DEBUG: Retry response status: {res.status_code}")
                print(f"📡 DEBUG: Retry response text: {res.text}")
            else:
                msg = "❌ GAGAL: Token invalid & Login Gagal."
                print(f"❌ DEBUG: Failed to refresh token, updating message with error: {msg}")
                if query.message.caption:
                    await query.edit_message_caption(caption=query.message.caption + f"\n\n{msg}")
                else:
                    await query.edit_message_text(text=query.message.text + f"\n\n{msg}")
                return

        # 5. Update Pesan jika Sukses
        if res.ok:
            print(f"✅ DEBUG: Request successful, updating message with status: {action.upper()} BY ADMIN")
            try:
                if query.message.caption:
                    await query.edit_message_caption(
                        caption=query.message.caption + f"\n\n<b>STATUS: {action.upper()} BY ADMIN</b>",
                        parse_mode="HTML"
                    )
                    print("✅ DEBUG: Caption updated successfully")
                else:
                    await query.edit_message_text(
                        text=query.message.text + f"\n\n<b>STATUS: {action.upper()} BY ADMIN</b>",
                        parse_mode="HTML"
                    )
                    print("✅ DEBUG: Text updated successfully")
            except Exception as edit_error:
                print(f"❌ DEBUG: Error updating message text/caption: {edit_error}")

            # Hapus tombol
            print(f"🗑️ DEBUG: Attempting to remove reply markup. Current markup: {bool(query.message.reply_markup)}")
            try:
                if query.message.reply_markup:
                    await query.edit_message_reply_markup(reply_markup=None)
                    print("✅ DEBUG: Reply markup removed successfully")
                else:
                    print("⚠️ DEBUG: No reply markup to remove")
            except Exception as markup_error:
                print(f"❌ DEBUG: Error removing reply markup: {markup_error}")

            # Kirim notifikasi ke admin WebSocket (untuk update tabel di admin panel)
            try:
                import database
                from sqlalchemy.orm import Session
                from main import manager # Pastikan main.py tidak circular import dengan bot

                db: Session = database.SessionLocal()
                topup_request = db.query(database.TopUpRequest).filter(database.TopUpRequest.id == request_id).first()

                if topup_request:
                    # Beritahu semua admin bahwa status request telah berubah
                    await manager.broadcast_to_admins({
                        "type": "update_request",
                        "id": request_id,
                        "new_status": "Approved" if action == "approve" else "Rejected"
                    })
                    print(f"✅ DEBUG: Admin notification sent for request {request_id}")
                else:
                    print(f"⚠️ DEBUG: Top up request {request_id} not found in database")
            except Exception as e:
                print(f"❌ Gagal mengirim notifikasi ke admin: {e}")
            finally:
                db.close()
        else:
            # Handle Error Server (500, 404, dll)
            error_msg = f"❌ Gagal: {res.text}"
            print(f"❌ DEBUG: Request failed with error: {error_msg}")
            if query.message.caption:
                await query.edit_message_caption(caption=query.message.caption + f"\n\n{error_msg}")
            else:
                await query.edit_message_text(text=query.message.text + f"\n\n{error_msg}")

    except Exception as e:
        # Handle Error Umum (Koneksi, dll)
        error_str = str(e).lower()
        if "not modified" in error_str:
            print("⚠️ DEBUG: Message not modified error (likely double click), ignoring")
            return # Biasanya double click, abaikan

        print(f"❌ Error pada button_click: {e}")
        error_msg = f"❌ Error: {str(e)}"
        if query.message.caption:
            await query.edit_message_caption(caption=query.message.caption + f"\n\n{error_msg}")
        else:
            await query.edit_message_text(text=query.message.text + f"\n\n{error_msg}")

def notify_new_topup(amount, user_email, image_filename, request_id):
    """Kirim notifikasi ke Telegram saat ada top up baru"""
    if not ADMIN_CHAT_ID:
        print("⚠️ BELUM ADA ADMIN CHAT ID.")
        print("SILAKAN BUKA TELEGRAM -> CARI BOT -> KETIK /start")
        return

    file_path = f"uploads/{image_filename}"

    keyboard = [
        [
            InlineKeyboardButton("✅ Setujui", callback_data=f"approve_{request_id}"),
            InlineKeyboardButton("❌ Tolak", callback_data=f"reject_{request_id}")
        ]
    ]
    
    # PERBAIKAN DI SINI: Gunakan variabel yang benar
    reply_markup_dict = InlineKeyboardMarkup(keyboard).to_dict()
    reply_markup_str = json.dumps(reply_markup_dict)

    caption = (
        f"🔔 <b>Request Top Up Baru!</b>\n\n"
        f"👤 User: <code>{user_email}</code>\n"
        f"💰 Jumlah: <b>{amount} Kredit</b>\n"
        f"🆔 ID: <code>{request_id}</code>"
    )

    try:
        with open(file_path, 'rb') as photo_file:
            data_payload = {
                "chat_id": str(ADMIN_CHAT_ID),
                "caption": caption,
                "parse_mode": "HTML",
                "reply_markup": reply_markup_str 
            }
            files_payload = {
                "document": (image_filename, photo_file)
            }

            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                data=data_payload,
                files=files_payload
            )
            if response.status_code == 200:
                print("✅ Notifikasi BERHASIL dikirim!")
            else:
                print(f"❌ Gagal mengirim: {response.text}")
    except FileNotFoundError:
        print("❌ GAGAL: File bukti tidak ditemukan di folder uploads!")
    except Exception as e:
        print(f"❌ Error: {e}")

def run_polling():
    """Fungsi ini dijalankan di thread terpisah"""
    print("🔄 Refreshing admin token in bot thread...")
    refresh_admin_token()
    application = Application.builder().token(BOT_TOKEN).build()

    # Registrasi Handler
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_click))

    print("🤖 Telegram Bot berjalan di background...")

    # PERBAIKAN DI SINI: Jangan buat manual loop, biarkan run_polling yang handle
    try:
        application.run_polling()
    except Exception as e:
        print(f"❌ Error di Bot: {e}")

def start_bot():
    # Refresh token saat bot dimulai
    print("🔄 Refreshing admin token at startup...")
    refresh_admin_token()

    bot_thread = threading.Thread(target=run_polling, daemon=True)
    bot_thread.start()
    print("🤖 Telegram Bot Thread dimulai...")