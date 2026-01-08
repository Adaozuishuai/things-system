import requests
import uuid
import sys

BASE_URL = "http://localhost:8000/api/auth"

def run_test():
    print("=== Starting Settings Flow Test ===")
    
    # Generate unique user
    username = f"test_user_{uuid.uuid4().hex[:6]}"
    password = "InitialPassword123!"
    new_password = "NewPassword456!"
    
    # 1. Register
    print(f"\n1. Registering user: {username}")
    reg_resp = requests.post(f"{BASE_URL}/register", json={
        "username": username,
        "password": password
    })
    
    if reg_resp.status_code != 200:
        print(f"Registration failed: {reg_resp.text}")
        sys.exit(1)
        
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   -> Registration successful, token acquired.")
    
    # 2. Get Initial Profile
    print("\n2. Getting initial profile...")
    me_resp = requests.get(f"{BASE_URL}/me", headers=headers)
    if me_resp.status_code != 200:
        print(f"Get profile failed: {me_resp.text}")
        sys.exit(1)
    
    user_data = me_resp.json()
    print(f"   -> Current profile: {user_data}")
    assert user_data["username"] == username
    assert user_data["email"] is None
    
    # 3. Update Profile
    print("\n3. Updating profile (email, bio)...")
    update_data = {
        "email": "test@example.com",
        "bio": "This is a test bio."
    }
    update_resp = requests.put(f"{BASE_URL}/me", headers=headers, json=update_data)
    if update_resp.status_code != 200:
        print(f"Update profile failed: {update_resp.text}")
        sys.exit(1)
        
    updated_user = update_resp.json()
    print(f"   -> Update response: {updated_user}")
    assert updated_user["email"] == "test@example.com"
    assert updated_user["bio"] == "This is a test bio."
    
    # 4. Verify Update Persistence
    print("\n4. Verifying update persistence...")
    verify_resp = requests.get(f"{BASE_URL}/me", headers=headers)
    verify_data = verify_resp.json()
    assert verify_data["email"] == "test@example.com"
    print("   -> Persistence verified.")
    
    # 5. Change Password
    print("\n5. Changing password...")
    pwd_data = {
        "current_password": password,
        "new_password": new_password
    }
    pwd_resp = requests.put(f"{BASE_URL}/me/password", headers=headers, json=pwd_data)
    if pwd_resp.status_code != 200:
        print(f"Change password failed: {pwd_resp.text}")
        sys.exit(1)
    print("   -> Password changed successfully.")
    
    # 6. Verify Old Password Fails
    print("\n6. Verifying old password fails login...")
    old_login_resp = requests.post(f"{BASE_URL}/login", json={
        "username": username,
        "password": password
    })
    if old_login_resp.status_code == 401:
        print("   -> Old password login failed as expected (401).")
    else:
        print(f"   -> Unexpected status code: {old_login_resp.status_code}")
        sys.exit(1)
        
    # 7. Verify New Password Works
    print("\n7. Verifying new password works...")
    new_login_resp = requests.post(f"{BASE_URL}/login", json={
        "username": username,
        "password": new_password
    })
    if new_login_resp.status_code == 200:
        print("   -> New password login successful.")
    else:
        print(f"   -> New password login failed: {new_login_resp.text}")
        sys.exit(1)
        
    print("\n=== All Tests Passed! ===")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        sys.exit(1)
