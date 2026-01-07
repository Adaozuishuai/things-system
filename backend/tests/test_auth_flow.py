import requests
import uuid
import sys
import os

# Configuration
BASE_URL = "http://localhost:8000/api/auth"

def test_auth_flow():
    print("=== Authentication System Test ===\n")
    
    # Generate random user
    random_id = str(uuid.uuid4())[:8]
    username = f"testuser_{random_id}"
    password = "testpassword123"
    
    print(f"Testing with User: {username} / {password}")
    
    # 1. Register
    print("\n[Step 1] Testing Registration...")
    try:
        reg_payload = {"username": username, "password": password}
        response = requests.post(f"{BASE_URL}/register", json=reg_payload)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Registration Successful.")
            print(f"   Token received: {token[:20]}...")
        else:
            print(f"❌ Registration Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. Duplicate Registration
    print("\n[Step 2] Testing Duplicate Registration...")
    response = requests.post(f"{BASE_URL}/register", json=reg_payload)
    if response.status_code == 400:
        print(f"✅ Correctly rejected duplicate username (400 Bad Request).")
    else:
        print(f"❌ Failed to reject duplicate: {response.status_code}")

    # 3. Login
    print("\n[Step 3] Testing Login...")
    login_payload = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/login", json=login_payload)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"✅ Login Successful.")
        print(f"   Token received: {token[:20]}...")
    else:
        print(f"❌ Login Failed: {response.status_code}")
        print(f"   Response: {response.text}")

    # 4. Invalid Login (Wrong Password)
    print("\n[Step 4] Testing Invalid Password...")
    wrong_payload = {"username": username, "password": "wrongpassword"}
    response = requests.post(f"{BASE_URL}/login", json=wrong_payload)
    
    if response.status_code == 401:
        print(f"✅ Correctly rejected wrong password (401 Unauthorized).")
    else:
        print(f"❌ Failed to reject wrong password: {response.status_code}")
        
    # 5. Invalid Login (Non-existent User)
    print("\n[Step 5] Testing Non-existent User...")
    non_exist_payload = {"username": "ghost_user_9999", "password": "password"}
    response = requests.post(f"{BASE_URL}/login", json=non_exist_payload)
    
    if response.status_code == 401:
        print(f"✅ Correctly rejected non-existent user (401 Unauthorized).")
    else:
        print(f"❌ Failed to reject non-existent user: {response.status_code}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_auth_flow()
