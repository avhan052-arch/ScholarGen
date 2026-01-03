#!/usr/bin/env python3
"""
Test script for Telegram Bot buttons functionality
This script tests the "Setujui" (Approve) and "Tolak" (Reject) buttons
"""

import requests
import time
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
BOT_ADMIN_TOKEN = None  # Will be fetched automatically
ADMIN_EMAIL = "avhan43@gmail.com"
ADMIN_PASSWORD = "admin123"

def get_admin_token():
    """Get admin token for API authentication"""
    global BOT_ADMIN_TOKEN
    print("🔄 Getting admin token...")
    
    login_url = f"{BASE_URL}/admin/token"
    response = requests.post(login_url, data={
        "username": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        BOT_ADMIN_TOKEN = data.get("access_token")
        print(f"✅ Token obtained successfully! Token length: {len(BOT_ADMIN_TOKEN) if BOT_ADMIN_TOKEN else 0}")
        return BOT_ADMIN_TOKEN
    else:
        print(f"❌ Failed to get token: {response.text}")
        return None

def get_pending_requests():
    """Get all pending top-up requests"""
    print("🔍 Getting pending requests...")
    
    if not BOT_ADMIN_TOKEN:
        print("❌ No admin token available")
        return []
    
    headers = {"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"}
    response = requests.get(f"{BASE_URL}/admin/topup_requests", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        pending_requests = [req for req in data.get("requests", []) if req["status"] == "Pending"]
        print(f"✅ Found {len(pending_requests)} pending requests")
        return pending_requests
    else:
        print(f"❌ Failed to get requests: {response.text}")
        return []

def test_approve_request(request_id: int) -> bool:
    """Test the approve endpoint for a specific request"""
    print(f"✅ Testing APPROVE for request ID: {request_id}")
    
    if not BOT_ADMIN_TOKEN:
        print("❌ No admin token available")
        return False
    
    headers = {"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"}
    response = requests.post(f"{BASE_URL}/admin/approve_topup/{request_id}", headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Request {request_id} APPROVED successfully")
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"❌ Failed to approve request {request_id}: {response.text}")
        return False

def test_reject_request(request_id: int) -> bool:
    """Test the reject endpoint for a specific request"""
    print(f"❌ Testing REJECT for request ID: {request_id}")
    
    if not BOT_ADMIN_TOKEN:
        print("❌ No admin token available")
        return False
    
    headers = {"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"}
    response = requests.post(f"{BASE_URL}/admin/reject_topup/{request_id}", headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Request {request_id} REJECTED successfully")
        print(f"Response: {response.json()}")
        return True
    else:
        print(f"❌ Failed to reject request {request_id}: {response.text}")
        return False

def get_request_status(request_id: int) -> Optional[str]:
    """Get the current status of a specific request"""
    if not BOT_ADMIN_TOKEN:
        print("❌ No admin token available")
        return None
    
    headers = {"Authorization": f"Bearer {BOT_ADMIN_TOKEN}"}
    response = requests.get(f"{BASE_URL}/admin/topup_requests", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        for req in data.get("requests", []):
            if req["id"] == request_id:
                return req["status"]
    
    return None

def test_button_functionality():
    """Main test function for bot buttons"""
    print("=" * 60)
    print("🤖 TELEGRAM BOT BUTTONS TESTING SCRIPT")
    print("=" * 60)
    
    # Step 1: Get admin token
    token = get_admin_token()
    if not token:
        print("❌ Cannot proceed without admin token")
        return False
    
    # Step 2: Get pending requests
    pending_requests = get_pending_requests()
    if not pending_requests:
        print("❌ No pending requests to test with")
        print("💡 Please create a pending top-up request first")
        return False
    
    # Step 3: Test with the first pending request
    test_request = pending_requests[0]
    request_id = test_request["id"]
    original_status = test_request["status"]
    
    print(f"📝 Testing with request ID: {request_id}")
    print(f"📊 Original status: {original_status}")
    
    # Step 4: Test APPROVE functionality
    print("\n" + "-" * 40)
    print("TEST 1: APPROVE BUTTON")
    print("-" * 40)
    
    approve_success = test_approve_request(request_id)
    
    # Verify status changed to Approved
    time.sleep(1)  # Wait a moment for the update
    current_status = get_request_status(request_id)
    print(f"📊 Status after approve: {current_status}")
    
    if current_status == "Approved" and approve_success:
        print("✅ APPROVE test PASSED")
    else:
        print("❌ APPROVE test FAILED")
    
    # Step 5: Create another test request by rejecting it first, then testing approve
    print("\n" + "-" * 40)
    print("TEST 2: REJECT BUTTON")
    print("-" * 40)
    
    # Get another pending request for reject test
    pending_requests = get_pending_requests()
    if pending_requests:
        reject_request = pending_requests[0]
        reject_request_id = reject_request["id"]
        
        reject_success = test_reject_request(reject_request_id)
        
        # Verify status changed to Rejected
        time.sleep(1)  # Wait a moment for the update
        current_status = get_request_status(reject_request_id)
        print(f"📊 Status after reject: {current_status}")
        
        if current_status == "Rejected" and reject_success:
            print("✅ REJECT test PASSED")
        else:
            print("❌ REJECT test FAILED")
    else:
        print("❌ No pending requests available for reject test")
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETED")
    print("=" * 60)
    
    return True

def test_manual_request(request_id: int, action: str):
    """Test a specific request with a specific action"""
    if action.lower() == "approve":
        return test_approve_request(request_id)
    elif action.lower() == "reject":
        return test_reject_request(request_id)
    else:
        print("❌ Action must be 'approve' or 'reject'")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Manual test mode: python test_bot_buttons.py <request_id> <action>
        if len(sys.argv) == 3:
            try:
                request_id = int(sys.argv[1])
                action = sys.argv[2].lower()
                if action in ["approve", "reject"]:
                    get_admin_token()  # Get token first
                    test_manual_request(request_id, action)
                else:
                    print("❌ Action must be 'approve' or 'reject'")
            except ValueError:
                print("❌ Request ID must be a number")
        else:
            print("Usage: python test_bot_buttons.py <request_id> <approve|reject>")
    else:
        # Full test mode
        test_button_functionality()
