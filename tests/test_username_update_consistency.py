import requests
import uuid
import sys

BASE_URL = "http://localhost:8000/api/auth"

def run_test():
    print("=== Testing Username Update Consistency ===")
    
    # 1. Setup User
    username = f"consistency_test_{uuid.uuid4().hex[:6]}"
    password = "Password123!"
    new_username = f"new_name_{uuid.uuid4().hex[:6]}"
    
    print(f"\n1. Creating user: {username}")
    resp = requests.post(f"{BASE_URL}/register", json={
        "username": username,
        "password": password
    })
    if resp.status_code != 200:
        print(f"FATAL: Register failed: {resp.text}")
        sys.exit(1)
        
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   -> Token acquired.")
    
    # 2. Update Username
    print(f"\n2. Updating username to: {new_username}")
    resp = requests.put(f"{BASE_URL}/me", headers=headers, json={"username": new_username})
    
    if resp.status_code == 200:
        print("   -> Username updated successfully.")
    else:
        print(f"FATAL: Update failed: {resp.text}")
        sys.exit(1)
        
    # 3. Verify Consistency with OLD Token
    print("\n3. Verifying access with existing token...")
    resp = requests.get(f"{BASE_URL}/me", headers=headers)
    
    if resp.status_code == 200:
        print("   -> SUCCESS: Token is persistent (User ID based).")
        data = resp.json()
        if data["username"] == new_username:
            print("   -> Data Consistency: PASS (Username is updated in response)")
        else:
            print(f"   -> Data Consistency: FAIL (Old username returned: {data['username']})")
    elif resp.status_code == 401:
        print("   -> FAIL/WARNING: Token invalidated immediately after username change.")
        print("      (This happens because Token stores username instead of UUID)")
    else:
        print(f"   -> ERROR: Unexpected status code: {resp.status_code}")

if __name__ == "__main__":
    run_test()
