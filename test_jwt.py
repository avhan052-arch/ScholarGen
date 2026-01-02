#!/usr/bin/env python3
"""
File test untuk memastikan JWT token berfungsi dengan baik
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import timedelta
from auth import create_access_token, decode_access_token

def test_jwt():
    print("Testing JWT token creation and decoding...")
    
    # Test membuat token
    test_data = {"sub": "test@example.com"}
    token = create_access_token(data=test_data, expires_delta=timedelta(minutes=30))
    print(f"✅ Token created: {token[:50]}...")
    
    # Test decode token
    decoded = decode_access_token(token)
    print(f"✅ Token decoded: {decoded}")
    
    # Verifikasi isi token
    assert decoded["sub"] == "test@example.com", "Token subject doesn't match"
    print("✅ Token subject verified")
    
    print("\n✅ All JWT tests passed!")

if __name__ == "__main__":
    test_jwt()