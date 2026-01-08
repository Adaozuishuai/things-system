import requests
import uuid
import sys
import time

BASE_URL = "http://localhost:8000/api/auth"

def run_test():
    print("=== Testing Profile Update Consistency (Global Sync) ===")
    
    # 1. Setup User
    username = f"sync_test_{uuid.uuid4().hex[:6]}"
    password = "Password123!"
    
    print(f"\n1. Creating user: {username}")
    resp = requests.post(f"{BASE_URL}/register", json={
        "username": username,
        "password": password
    })
    if resp.status_code != 200:
        print(f"FATAL: Register failed: {resp.text}")
        sys.exit(1)
        
    token_a = resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    print("   -> Token A acquired (Device A).")
    
    # Simulate Device B login
    resp_b = requests.post(f"{BASE_URL}/login", json={
        "username": username,
        "password": password
    })
    token_b = resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    print("   -> Token B acquired (Device B).")
    
    # 2. Update Profile on Device A
    new_email = "updated@example.com"
    new_bio = "Updated bio from Device A"
    
    print(f"\n2. Updating profile on Device A...")
    update_data = {
        "email": new_email,
        "bio": new_bio
    }
    resp = requests.put(f"{BASE_URL}/me", headers=headers_a, json=update_data)
    
    if resp.status_code == 200:
        print("   -> Update successful on Device A.")
    else:
        print(f"FATAL: Update failed: {resp.text}")
        sys.exit(1)
        
    # 3. Verify on Device B (Global Sync)
    print("\n3. Verifying consistency on Device B (Immediate check)...")
    # No sleep here, we want to test immediate consistency
    resp = requests.get(f"{BASE_URL}/me", headers=headers_b)
    
    if resp.status_code != 200:
        print(f"FATAL: Failed to get profile on Device B: {resp.text}")
        sys.exit(1)
        
    data = resp.json()
    print(f"   -> Device B saw: Email={data['email']}, Bio={data['bio']}")
    
    if data['email'] == new_email and data['bio'] == new_bio:
        print("   -> PASS: Global sync verified. Device B sees updates immediately.")
    else:
        print(f"   -> FAIL: Data inconsistency detected!\n      Expected: {new_email}, {new_bio}\n      Got: {data['email']}, {data['bio']}")

if __name__ == "__main__":
    run_test()
