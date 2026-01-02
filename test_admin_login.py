#!/usr/bin/env python3
"""
File test untuk memastikan endpoint login admin berfungsi
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_admin_login_endpoint():
    print("Testing admin login endpoint...")
    
    # Impor aplikasi FastAPI
    from main import app
    from fastapi.testclient import TestClient
    
    # Buat test client
    client = TestClient(app)
    
    # Coba buat admin untuk testing
    from auth import get_password_hash
    import database
    
    # Hapus admin testing jika sudah ada
    db = database.SessionLocal()
    existing_test_admin = db.query(database.User).filter(
        database.User.email == "test_admin_login@example.com"
    ).first()
    
    if existing_test_admin:
        db.delete(existing_test_admin)
        db.commit()
    
    # Buat admin testing
    hashed_password = get_password_hash("test_password")
    test_admin = database.User(
        email="test_admin_login@example.com",
        hashed_password=hashed_password,
        is_admin=True,
        credits=99999
    )
    db.add(test_admin)
    db.commit()
    db.refresh(test_admin)
    
    # Test login
    response = client.post(
        "/admin/token",
        data={
            "username": "test_admin_login@example.com",
            "password": "test_password"
        }
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    # Harusnya mendapatkan token
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "access_token" in response.json(), "Response should contain access_token"
    
    # Hapus admin testing
    db.delete(test_admin)
    db.commit()
    db.close()
    
    print("\n✅ Admin login endpoint test passed!")

if __name__ == "__main__":
    test_admin_login_endpoint()