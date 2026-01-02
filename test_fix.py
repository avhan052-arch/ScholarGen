#!/usr/bin/env python3
"""
File test untuk memastikan perbaikan bcrypt/password berfungsi dengan baik
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth import get_password_hash, verify_password

def test_password_length():
    print("Testing password length handling...")
    
    # Test dengan password pendek
    short_password = "short"
    hashed = get_password_hash(short_password)
    assert verify_password(short_password, hashed), "Short password test failed"
    print("✅ Short password test passed")
    
    # Test dengan password tepat 72 karakter
    exactly_72 = "a" * 72
    hashed = get_password_hash(exactly_72)
    assert verify_password(exactly_72, hashed), "72-char password test failed"
    print("✅ 72-char password test passed")
    
    # Test dengan password lebih dari 72 karakter
    too_long = "a" * 100
    hashed = get_password_hash(too_long)
    # Harus bisa verify dengan password asli (akan dipotong otomatis)
    assert verify_password(too_long, hashed), "Long password test failed"
    print("✅ Long password test passed")
    
    # Test dengan password yang dipotong
    truncated = too_long[:72]
    assert verify_password(truncated, hashed), "Truncated password test failed"
    print("✅ Truncated password test passed")
    
    print("\n✅ All password length tests passed!")

if __name__ == "__main__":
    test_password_length()