#!/usr/bin/env python3
"""
File test untuk memastikan pembuatan admin otomatis berfungsi
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import database
from auth import verify_password

def test_admin_creation():
    print("Testing automatic admin creation...")
    
    # Set environment variables untuk testing
    os.environ["ADMIN_EMAIL"] = "test_admin@example.com"
    os.environ["ADMIN_PASSWORD"] = "test_password"
    
    # Impor fungsi startup
    from main import startup_db_client
    
    # Jalankan fungsi startup
    startup_db_client()
    
    # Cek apakah admin telah dibuat
    db = database.SessionLocal()
    
    admin = db.query(database.User).filter(
        database.User.email == "test_admin@example.com"
    ).first()
    
    assert admin is not None, "Admin user should exist"
    assert admin.is_admin == True, "User should have admin status"
    assert verify_password("test_password", admin.hashed_password), "Password should be correct"
    
    print(f"✅ Admin email: {admin.email}")
    print(f"✅ Is admin: {admin.is_admin}")
    print(f"✅ Credits: {admin.credits}")
    
    # Hapus user testing
    db.delete(admin)
    db.commit()
    db.close()
    
    print("\n✅ Automatic admin creation test passed!")

if __name__ == "__main__":
    test_admin_creation()