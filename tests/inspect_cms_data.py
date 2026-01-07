import asyncio
import os
import sys
import json
import uuid
import aiohttp
from dotenv import load_dotenv

# Add backend path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.agent.orchestrator import orchestrator

# Load environment variables
load_dotenv()

async def inspect_cms_data():
    print("=== Payload CMS Data Inspection Tool ===\n")

    # 1. Configuration
    cms_url = os.getenv("CMS_URL")
    cms_collection = os.getenv("CMS_COLLECTION", "posts")
    cms_email = os.getenv("CMS_EMAIL")
    cms_password = os.getenv("CMS_PASSWORD")
    cms_user_collection = os.getenv("CMS_USER_COLLECTION", "users")

    if not all([cms_url, cms_email, cms_password]):
        print("❌ Error: CMS credentials not found in .env")
        return

    print(f"Target: {cms_url} (Collection: {cms_collection})")

    async with aiohttp.ClientSession() as session:
        # 2. Login
        print("\n[Step 1] Logging in...")
        login_url = f"{cms_url}/api/{cms_user_collection}/login"
        payload = {"email": cms_email, "password": cms_password}
        
        try:
            async with session.post(login_url, json=payload) as response:
                if response.status != 200:
                    print(f"❌ Login Failed: {response.status}")
                    print(await response.text())
                    return
                
                login_data = await response.json()
                token = login_data.get("token")
                print("✅ Login Successful. Token acquired.")
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return

        # 3. Fetch Data
        print("\n[Step 2] Fetching raw data...")
        fetch_url = f"{cms_url}/api/{cms_collection}?limit=3" # Fetch only 3 items
        headers = {"Authorization": f"JWT {token}"}
        
        try:
            async with session.get(fetch_url, headers=headers) as response:
                if response.status != 200:
                    print(f"❌ Fetch Failed: {response.status}")
                    return
                
                data = await response.json()
                docs = data.get("docs", [])
                print(f"✅ Fetched {len(docs)} items.")
                
                if not docs:
                    print("⚠️ No items found in collection.")
                    return

                # 4. Print Raw Data (First Item)
                first_doc = docs[0]
                print("\n[Step 3] Inspecting First Raw Item:")
                print("-" * 40)
                print(json.dumps(first_doc, indent=2, ensure_ascii=False))
                print("-" * 40)

                # 5. Simulate Backend Logic (Refinement)
                print("\n[Step 4] Simulating Backend Logic (RefinementAgent)...")
                print("Sending raw item to AgentOrchestrator...")
                
                # Construct the input dict as PayloadPoller does
                raw_item_dict = {
                    "id": str(first_doc.get("id", uuid.uuid4())),
                    "title": first_doc.get("title") or "Untitled",
                    "summary": first_doc.get("summary") or first_doc.get("description") or "",
                    "original": first_doc.get("original") or first_doc.get("content") or "",
                    "tags": [],
                    "publishDate": first_doc.get("publishDate") or first_doc.get("createdAt"),
                    "source": first_doc.get("author") or "PayloadCMS",
                    "url": f"{cms_url}/admin/collections/{cms_collection}/{first_doc.get('id')}"
                }
                
                # Call the actual refinement logic
                refined_item = await orchestrator.refine_intel_item(raw_item_dict)
                
                print("\n✅ Backend Processing Result:")
                print("-" * 40)
                print(json.dumps(refined_item, indent=2, ensure_ascii=False))
                print("-" * 40)
                
                print("\n🔍 Verification:")
                if "tags" in refined_item and refined_item["tags"]:
                    print(f"✅ Tags generated: {len(refined_item['tags'])}")
                else:
                    print("⚠️ No tags generated (Check Agent Prompt or LLM status)")

        except Exception as e:
            print(f"❌ Error during fetch/process: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_cms_data())
