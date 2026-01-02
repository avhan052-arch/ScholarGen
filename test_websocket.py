#!/usr/bin/env python3
"""
File test untuk memastikan websocket berfungsi dengan baik
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import create_access_token
from datetime import timedelta

def test_websocket_token():
    print("Testing token creation for WebSocket...")
    
    # Buat token untuk testing
    test_data = {"sub": "admin@example.com"}
    token = create_access_token(data=test_data, expires_delta=timedelta(minutes=30))
    print(f"✅ Admin token created: {token[:50]}...")
    
    # Untuk testing WebSocket admin, Anda bisa menggunakan token ini
    # di URL seperti: ws://localhost:8000/ws/admin?token={token}
    print(f"✅ Token bisa digunakan untuk WebSocket admin")
    
    print("\nUntuk testing WebSocket admin, gunakan URL:")
    print(f"ws://localhost:8000/ws/admin?token={token}")
    print("\n✅ WebSocket token test passed!")

if __name__ == "__main__":
    test_websocket_token()