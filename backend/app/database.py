from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "intel.db")
DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()
SQLITE_PATH = (os.getenv("SQLITE_PATH") or "").strip()

if DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
elif SQLITE_PATH:
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{SQLITE_PATH}"
else:
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"

connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite:///") else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
