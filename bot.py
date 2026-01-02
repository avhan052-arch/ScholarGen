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
    print("🔄 Mencoba mengambil Token Admin otomatis...")
    try:
        res = requests.post(f"{BASE_URL}/admin/token", data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if res.ok:
            data = res.json()
            BOT_ADMIN_TOKEN = data.get("access_token")
            print(f"✅ Token Admin berhasil didapatkan!")
            return True
        else:
            print(f"❌ Gagal Login Admin: {res.text}")
            return False
    except Exception as e:
        print(f"❌ Error saat koneksi ke Server Login: {e}")
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

    # 1. Validasi Data
    if not query.data:
        print("⚠️ Callback data kosong.")
        return

    try:
        action, req_id = query.data.split("_")
        request_id = int(req_id)
    except ValueError:
        print(f"❌ Error format data: {query.data}")
        await query.edit_message_text(text="⚠️ Error: Format data tombol tidak valid.")
        return

    # 2. Tentukan Endpoint
    if action == "approve":
        endpoint = f"{BASE_URL}/admin/approve_topup/{request_id}"
        text_success = "✅ Top Up Disetujui!"
    else:
        endpoint = f"{BASE_URL}/admin/reject_topup/{request_id}"
        text_success = "❌ Top Up Ditolak!"

    try:
        # 3. Kirim Request ke Server
        res = requests.post(endpoint, headers={"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"})

        # 4. Handle jika Token Expired (401)
        if res.status_code == 401:
            print("⚠️ Token Admin kadaluarsa. Melakukan Auto-Login...")
            if refresh_admin_token():
                res = requests.post(endpoint, headers={"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"})
            else:
                msg = "❌ GAGAL: Token invalid & Login Gagal."
                if query.message.caption:
                    await query.edit_message_caption(caption=query.message.caption + f"\n\n{msg}")
                else:
                    await query.edit_message_text(text=query.message.text + f"\n\n{msg}")
                return

        # 5. Update Pesan jika Sukses
        if res.ok:
            if query.message.caption:
                await query.edit_message_caption(
                    caption=query.message.caption + f"\n\n<b>STATUS: {action.upper()} BY ADMIN</b>",
                    parse_mode="HTML"
                )
            else:
                await query.edit_message_text(
                    text=query.message.text + f"\n\n<b>STATUS: {action.upper()} BY ADMIN</b>",
                    parse_mode="HTML"
                )
            
            # Hapus tombol
            if query.message.reply_markup:
                await query.edit_message_reply_markup(reply_markup=None)

            # 6. Kirim Notifikasi ke User via WebSocket
            try:
                import database
                from sqlalchemy.orm import Session
                from sqlalchemy import create_engine
                from main import manager # Pastikan main.py tidak circular import dengan bot

                engine = create_engine("sqlite:///./skripsi.db")
                db: Session = database.SessionLocal()
                topup_request = db.query(database.TopUpRequest).filter(database.TopUpRequest.id == request_id).first()

                if topup_request:
                    user = db.query(database.User).filter(database.User.id == topup_request.user_id).first()
                    if user:
                        status_text = "disetujui" if action == "approve" else "ditolak"
                        await manager.broadcast_to_user(user.id, {
                            "type": "topup_notification",
                            "status": "approved" if action == "approve" else "rejected",
                            "message": f"Top up sebesar {topup_request.amount} kredit telah {status_text} oleh admin."
                        })
            except Exception as e:
                print(f"❌ Gagal mengirim notifikasi ke user: {e}")
            finally:
                db.close()
        else:
            # Handle Error Server (500, 404, dll)
            error_msg = f"❌ Gagal: {res.text}"
            if query.message.caption:
                await query.edit_message_caption(caption=query.message.caption + f"\n\n{error_msg}")
            else:
                await query.edit_message_text(text=query.message.text + f"\n\n{error_msg}")

    except Exception as e:
        # Handle Error Umum (Koneksi, dll)
        error_str = str(e).lower()
        if "not modified" in error_str:
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
    bot_thread = threading.Thread(target=run_polling, daemon=True)
    bot_thread.start()
    print("🤖 Telegram Bot Thread dimulai...")