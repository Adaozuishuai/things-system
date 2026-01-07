from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class RawData(Base):
    __tablename__ = "raw_data"

    id = Column(String, primary_key=True, default=generate_uuid)
    url = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    source = Column(String, default="manual")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)

class IntelItemDB(Base):
    __tablename__ = "intel_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    url = Column(String, nullable=True)
    source = Column(String, default="Unknown")
    publish_time_str = Column(String) # For display: YYYY/MM/DD HH:MM
    timestamp = Column(Float) # For sorting
    tags = Column(JSON, default=list)
    is_hot = Column(Boolean, default=False)
    favorited = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserDB(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    avatar = Column(String, nullable=True)
    preferences = Column(JSON, default={})
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
