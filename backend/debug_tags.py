from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db_models import IntelItemDB
import json

SQLALCHEMY_DATABASE_URL = "postgresql://intel_user:intel_pass@localhost/intel_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

items = db.query(IntelItemDB).order_by(IntelItemDB.created_at.desc()).limit(5).all()

print(f"Found {len(items)} items.")
for item in items:
    print(f"ID: {item.id}, Title: {item.title}")
    print(f"Tags ({type(item.tags)}): {item.tags}")
    print("-" * 20)
