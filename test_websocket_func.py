#!/usr/bin/env python3
"""
File test untuk memastikan WebSocket berfungsi dengan baik
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_websocket_functionality():
    print("Testing WebSocket functionality...")
    
    # Kita tidak bisa menguji WebSocket secara langsung tanpa server berjalan,
    # tapi kita bisa memastikan bahwa endpoint-nya terdefinisi dengan benar
    from main import app
    
    # Cek apakah endpoint WebSocket ada
    websocket_routes = [route for route in app.routes if hasattr(route, 'methods') and 'WEBSOCKET' in route.methods]
    print(f"✅ Jumlah WebSocket routes: {len(websocket_routes)}")
    
    # Cek apakah endpoint ws/{user_id} ada
    ws_user_found = any(route.path == "/ws/{user_id}" for route in app.routes if hasattr(route, 'path'))
    print(f"✅ WebSocket /ws/{{user_id}} route exists: {ws_user_found}")
    
    # Cek apakah endpoint ws/admin ada
    ws_admin_found = any(route.path == "/ws/admin" for route in app.routes if hasattr(route, 'path'))
    print(f"✅ WebSocket /ws/admin route exists: {ws_admin_found}")
    
    assert ws_user_found, "WebSocket user route should exist"
    assert ws_admin_found, "WebSocket admin route should exist"
    
    print("\n✅ WebSocket functionality test passed!")

if __name__ == "__main__":
    test_websocket_functionality()