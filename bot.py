import os
import json
import threading
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- KONFIGURASI BOT ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ID_FILE = "admin_chat_id.txt"  # File untuk menyimpan ID Admin

# --- KONFIGURASI ADMIN (AUTO LOGIN) ---
# Masukkan email dan password admin yang sudah Anda buat
ADMIN_EMAIL = "avhan43@gmail.com"
ADMIN_PASSWORD = "123" 

# Token Admin (Akan terisi otomatis saat startup atau saat refresh)
BOT_ADMIN_TOKEN = None 

# URL Aplikasi Anda
BASE_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "http://localhost:8000")

# --- FUNGSI LOGIN OTOMATIS ---
def refresh_admin_token():
    """Login ke FastAPI untuk mendapatkan Token Admin baru"""
    global BOT_ADMIN_TOKEN
    
    print("🔄 Mencoba mengambil Token Admin otomatis...")
    
    try:
        # Panggil endpoint login admin
        res = requests.post(f"{BASE_URL}/admin/token", data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if res.ok:
            data = res.json()
            BOT_ADMIN_TOKEN = data.get("access_token")
            print(f"✅ Token Admin berhasil didapatkan! (Expires in 30 menit)")
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
    """Menyimpan Chat ID Admin saat mereka mengetik /start"""
    global ADMIN_CHAT_ID
    ADMIN_CHAT_ID = update.effective_message.chat_id
    
    # SIMPAN ID KE FILE SUPAYA TIDAK HILANG SAAT RESTART
    with open(ID_FILE, "w") as f:
        f.write(str(ADMIN_CHAT_ID))
    
    await update.message.reply_text(
        f"✅ Bot terhubung! ID Anda: {ADMIN_CHAT_ID}.\nID ini telah disimpan otomatis."
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani klik tombol Approve/Reject"""
    query = update.callback_query
    await query.answer() 

    action, req_id = query.data.split("_")
    request_id = int(req_id)

    if action == "approve":
        endpoint = f"{BASE_URL}/admin/approve_topup/{request_id}"
        text_success = "✅ Top Up Disetujui!"
    else:
        endpoint = f"{BASE_URL}/admin/reject_topup/{request_id}"
        text_success = "❌ Top Up Ditolak!"

    try:
        # 1. Coba kirim request
        res = requests.post(endpoint, headers={"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"})

        # 2. Jika Error 401 (Token Kadaluarsa), Lakukan Auto Login dan Retry
        if res.status_code == 401:
            print("⚠️ Token Admin kadaluarsa. Melakukan Auto-Login...")
            
            # Refresh Token
            if refresh_admin_token():
                # Coba ulang request dengan token baru
                res = requests.post(endpoint, headers={"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"})
            else:
                await query.edit_message_caption(
                    caption=query.message.caption + f"\n\n❌ GAGAL: Token Admin invalid & Login Gagal.", 
                    parse_mode="HTML"
                )
                return

        if res.ok:
            # Update pesan di Telegram
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
        else:
            error_msg = f"❌ Gagal: {res.text}"
            if query.message.caption:
                await query.edit_message_caption(
                    caption=query.message.caption + f"\n\n{error_msg}", 
                    parse_mode="HTML"
                )
            else:
                await query.edit_message_text(
                    text=query.message.text + f"\n\n{error_msg}", 
                    parse_mode="HTML"
                )

    except Exception as e:
        # Cek apakah error ini cuma "Message is not modified"
        error_str = str(e).lower()
        if "not modified" in error_str:
            # Jika iya, abaikan saja (mungkin admin double-click)
            print("ℹ️ Pesan sudah diupdate sebelumnya (Double Click), skip update pesan.")
            return

        # Jika error lainnya, tampilkan error biasa
        error_msg = f"❌ Error: {str(e)}"
        if query.message.caption:
            await query.edit_message_caption(
                caption=query.message.caption + f"\n\n{error_msg}", 
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text(
                text=query.message.text + f"\n\n{error_msg}", 
                parse_mode="HTML"
            )

# --- FUNGSI NOTIFIKASI ---

def notify_new_topup(amount, user_email, image_filename, request_id):
    """Kirim notifikasi ke Telegram saat ada top up baru"""
    if not ADMIN_CHAT_ID:
        print("⚠️ BELUM ADA ADMIN CHAT ID.")
        print("SILAKAN BUKA TELEGRAM -> CARI BOT -> KETIK /start")
        return

    # 1. Path langsung ke file di komputer
    file_path = f"uploads/{image_filename}"

    # 2. Tombol Inline Keyboard
    keyboard = [
        [
            InlineKeyboardButton("✅ Setujui", callback_data=f"approve_{request_id}"),
            InlineKeyboardButton("❌ Tolak", callback_data=f"reject_{request_id}")
        ]
    ]
    # Pastikan reply_markup adalah string JSON
    reply_markup = InlineKeyboardMarkup(keyboard).to_dict()

    # 3. Pesan Caption
    caption = (
        f"🔔 <b>Request Top Up Baru!</b>\n\n"
        f"👤 User: <code>{user_email}</code>\n"
        f"💰 Jumlah: <b>{amount} Kredit</b>\n"
        f"🆔 ID: <code>{request_id}</code>"
    )

    try:
        # 4. Buka file
        with open(file_path, 'rb') as photo_file:
        
            # --- PERBAIKAN REPLY MARKUP ---
            reply_markup_dict = InlineKeyboardMarkup(keyboard).to_dict()
            reply_markup_str = json.dumps(reply_markup_dict) # <--- Ubah dict jadi string

            # Data Payload
            data_payload = {
                "chat_id": str(ADMIN_CHAT_ID),
                "caption": caption,
                "parse_mode": "HTML",
                "reply_markup": reply_markup_str # <--- Kirim versi String-nya
            }
            
            # Files Payload
            files_payload = {
                "document": (image_filename, photo_file)
            }

            # Kirim request
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                data=data_payload,
                files=files_payload
            )
        
            if response.status_code == 200:
                print("✅ Notifikasi (Binary File) BERHASIL dikirim!")
            else:
                print(f"❌ Gagal mengirim: {response.text}")

    except FileNotFoundError:
        print("❌ GAGAL: File bukti tidak ditemukan di folder uploads!")
    except Exception as e:
        print(f"❌ Error: {e}")

# --- FUNGSI STARTUP ---

def run_polling():
    """Fungsi ini dijalankan di thread terpisah"""
    
    # 1. Lakukan Login Otomatis saat bot start
    refresh_admin_token()

    # 2. Jalankan Bot
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Registrasi Handler
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_click))
    
    # Jalankan polling
    print("🤖 Telegram Bot berjalan di background...")
    # --- TAMBAHKAN BLOK INI ---
    # Membuat Event Loop baru yang terpisah untuk Thread Bot ini
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # ---------------------------
    # application.run_polling()
    try:
        application.run_polling()
    except Exception as e:
        print(f"❌ Error di Bot: {e}")


def start_bot():
    bot_thread = threading.Thread(target=run_polling, daemon=True)
    bot_thread.start()
    print("🤖 Telegram Bot Thread dimulai...")