import requests
import uuid
import sys

BASE_URL = "http://localhost:8000/api/auth"

def run_test():
    print("=== Testing Token Validity After Password Change ===")
    
    # 1. Setup User
    username = f"pwd_validity_{uuid.uuid4().hex[:6]}"
    password = "OldPassword123!"
    new_password = "NewPassword456!"
    
    print(f"\n1. Creating user: {username}")
    resp = requests.post(f"{BASE_URL}/register", json={
        "username": username,
        "password": password
    })
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   -> Token acquired.")
    
    # 2. Change Password
    print(f"\n2. Changing password...")
    resp = requests.put(f"{BASE_URL}/me/password", headers=headers, json={
        "current_password": password,
        "new_password": new_password
    })
    if resp.status_code != 200:
        print(f"FATAL: Password change failed: {resp.text}")
        sys.exit(1)
    print("   -> Password changed successfully.")
    
    # 3. Check if Token is still valid
    print("\n3. Checking if OLD Token is still valid...")
    resp = requests.get(f"{BASE_URL}/me", headers=headers)
    
    if resp.status_code == 200:
        print("   -> STATUS: 200 OK. Token remains VALID.")
        print("   -> CONCLUSION: Backend does NOT invalidate token on password change.")
        print("      If frontend says 'Session Expired', it might be frontend logic.")
    elif resp.status_code == 401:
        print("   -> STATUS: 401 Unauthorized. Token is INVALID.")
        print("   -> CONCLUSION: Backend invalidated token.")
        print("      If UI still shows logged in, AuthContext state was not cleared.")
    else:
        print(f"   -> STATUS: {resp.status_code}. Unexpected.")

if __name__ == "__main__":
    run_test()
