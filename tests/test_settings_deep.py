import requests
import uuid
import sys
import json
import threading
import time

BASE_URL = "http://localhost:8000/api/auth"

def create_user(prefix="user"):
    username = f"{prefix}_{uuid.uuid4().hex[:6]}"
    password = "Password123!"
    resp = requests.post(f"{BASE_URL}/register", json={
        "username": username,
        "password": password
    })
    if resp.status_code != 200:
        raise Exception(f"Failed to create user: {resp.text}")
    token = resp.json()["access_token"]
    return username, password, token

def test_duplicate_username():
    print("\n[Test] Duplicate Username Check")
    u1, p1, t1 = create_user("u1")
    u2, p2, t2 = create_user("u2")
    
    # Try to rename u2 to u1
    headers = {"Authorization": f"Bearer {t2}"}
    resp = requests.put(f"{BASE_URL}/me", headers=headers, json={"username": u1})
    
    if resp.status_code == 400:
        print("   -> PASS: Correctly rejected duplicate username.")
    else:
        print(f"   -> FAIL: Expected 400, got {resp.status_code} - {resp.text}")

def test_invalid_email_format():
    print("\n[Test] Invalid Email Format (Backend Validation)")
    # Note: Currently backend might not validate email format, this test checks behavior
    u1, p1, t1 = create_user("email_test")
    headers = {"Authorization": f"Bearer {t1}"}
    
    invalid_email = "not-an-email"
    resp = requests.put(f"{BASE_URL}/me", headers=headers, json={"email": invalid_email})
    
    if resp.status_code == 200:
        print(f"   -> WARNING: Backend accepted invalid email '{invalid_email}'. Ideally should fail.")
    else:
        print("   -> PASS: Backend rejected invalid email.")

def test_password_logic():
    print("\n[Test] Password Logic")
    u1, p1, t1 = create_user("pwd_test")
    headers = {"Authorization": f"Bearer {t1}"}
    
    # 1. Wrong current password
    resp = requests.put(f"{BASE_URL}/me/password", headers=headers, json={
        "current_password": "WrongPassword",
        "new_password": "NewPassword123!"
    })
    if resp.status_code == 400:
        print("   -> PASS: Rejected wrong current password.")
    else:
        print(f"   -> FAIL: Accepted wrong current password. Code: {resp.status_code}")
        
    # 2. Short new password (if policy exists)
    resp = requests.put(f"{BASE_URL}/me/password", headers=headers, json={
        "current_password": p1,
        "new_password": "123"
    })
    if resp.status_code == 200:
        print("   -> WARNING: Backend accepted short password '123'.")
    else:
        print("   -> PASS: Rejected short password.")

def test_preferences_persistence():
    print("\n[Test] Preferences JSON Persistence")
    u1, p1, t1 = create_user("pref_test")
    headers = {"Authorization": f"Bearer {t1}"}
    
    # 1. Save complex JSON
    complex_pref = {
        "theme": "dark",
        "notifications": {"email": True, "sms": False},
        "tags": ["AI", "Crypto"]
    }
    resp = requests.put(f"{BASE_URL}/me", headers=headers, json={"preferences": complex_pref})
    if resp.status_code != 200:
        print(f"   -> FAIL: Failed to save preferences. {resp.text}")
        return

    # 2. Verify retrieval
    resp = requests.get(f"{BASE_URL}/me", headers=headers)
    saved_pref = resp.json()["preferences"]
    
    # Deep compare
    if saved_pref == complex_pref:
        print("   -> PASS: Preferences saved and retrieved correctly.")
    else:
        print(f"   -> FAIL: Preferences mismatch.\nSent: {complex_pref}\nGot: {saved_pref}")

    # 3. Partial update (Merge test)
    # The current implementation might be REPLACE or MERGE. Let's find out.
    new_pref = {"theme": "light"} # Should we expect this to replace everything or just theme?
    # Our code: 
    # current_prefs.update(user_update.preferences)
    # So it should be a merge at top level.
    
    resp = requests.put(f"{BASE_URL}/me", headers=headers, json={"preferences": new_pref})
    resp = requests.get(f"{BASE_URL}/me", headers=headers)
    merged_pref = resp.json()["preferences"]
    
    if merged_pref["theme"] == "light" and "notifications" in merged_pref:
        print("   -> PASS: Preferences logic is MERGE (Top Level).")
    elif merged_pref["theme"] == "light" and "notifications" not in merged_pref:
        print("   -> INFO: Preferences logic is REPLACE.")
    else:
        print(f"   -> FAIL: Unexpected preference state: {merged_pref}")

def test_unauthorized_access():
    print("\n[Test] Unauthorized Access")
    # Try to access /me without token
    resp = requests.get(f"{BASE_URL}/me")
    if resp.status_code == 401:
        print("   -> PASS: Rejected no-token request.")
    else:
        print(f"   -> FAIL: Accepted no-token request. Code: {resp.status_code}")

    # Try with invalid token
    headers = {"Authorization": "Bearer invalid_token_string"}
    resp = requests.get(f"{BASE_URL}/me", headers=headers)
    if resp.status_code == 401:
        print("   -> PASS: Rejected invalid token.")
    else:
        print(f"   -> FAIL: Accepted invalid token. Code: {resp.status_code}")

def run_all():
    try:
        test_duplicate_username()
        test_invalid_email_format()
        test_password_logic()
        test_preferences_persistence()
        test_unauthorized_access()
        print("\n=== Deep Test Completed ===")
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")

if __name__ == "__main__":
    run_all()
