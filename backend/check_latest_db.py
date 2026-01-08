import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.abspath("/home/system_/system_mvp/backend"))

from app.database import SessionLocal
from app.db_models import IntelItemDB
from sqlalchemy import desc

def print_latest_intel():
    db = SessionLocal()
    try:
        # Query the latest item by timestamp
        latest_item = db.query(IntelItemDB).order_by(desc(IntelItemDB.created_at)).first()
        
        if latest_item:
            print("\n" + "="*50)
            print("📢 Latest Intel Item")
            print("="*50)
            print(f"🆔 ID: {latest_item.id}")
            print(f"📌 Title: {latest_item.title}")
            print(f"📝 Summary: {latest_item.summary}")
            print(f"📄 Content : {latest_item.content if latest_item.content else 'N/A'}")
            print(f"🔗 URL: {latest_item.url}")
            print(f"🏷️  Tags: {latest_item.tags}")
            print(f"⏰ Time: {latest_item.publish_time_str}")
            print(f"📅 Created At: {latest_item.created_at}")
            print("="*50 + "\n")
        else:
            print("\n❌ No intel items found in the database.\n")
            
    finally:
        db.close()

if __name__ == "__main__":
    print_latest_intel()
