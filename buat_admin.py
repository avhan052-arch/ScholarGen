import database
from auth import get_password_hash

# 1. Buka Koneksi Database
db = database.SessionLocal()

# --- KONFIGURASI ADMIN BARU ---
# Ganti email dan password di sini sesuai keinginan Anda
email_admin = "avhan43@gmail.com"  
password_admin = "123" 
# -------------------------------

# 2. Cek apakah email sudah terdaftar sebelumnya
existing_user = db.query(database.User).filter(database.User.email == email_admin).first()

if existing_user:
    print(f"⚠️ Email {email_admin} sudah ada di database.")
    
    # Jika sudah ada, kita ubah saja statusnya jadi admin dan update password
    confirm = input("Apakah ingin update user ini menjadi Admin dan ubah password? (y/n): ")
    if confirm.lower() == 'y':
        existing_user.hashed_password = get_password_hash(password_admin)
        existing_user.is_admin = True
        db.commit()
        print(f"✅ User {email_admin} berhasil diupdate menjadi Admin!")
    else:
        print("Proses dibatalkan.")

else:
    # 3. Jika belum ada, buat user baru
    # Kita enkripsi passwordnya dulu
    hashed_password = get_password_hash(password_admin)
    
    new_admin = database.User(
        email=email_admin,
        hashed_password=hashed_password,
        is_admin=True,         # <--- INI PENTING: Jadikan user ini admin
        credits=99999            # <--- Opsional: Beri saldo banyak untuk testing
    )
    
    # Simpan ke database
    db.add(new_admin)
    db.commit()
    
    print("=========================================")
    print("✅ ADMIN BARU BERHASIL DIBUAT!")
    print("=========================================")
    print(f"Email Login : {email_admin}")
    print(f"Password   : {password_admin}")
    print(f"Role       : Administrator")
    print("=========================================")

# 4. Tutup koneksi
db.close()