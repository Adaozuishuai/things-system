from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.database import get_db
from app.models import UserCreate, Token, UserUpdate, PasswordChange, UserResponse
from app.db_models import UserDB
from app.services.auth_utils import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from datetime import timedelta
import os
import re

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = UserDB(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Auto login after register
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserDB = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_me(user_update: UserUpdate, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if username exists if being updated
    if user_update.username and user_update.username != current_user.username:
        existing_user = db.query(UserDB).filter(UserDB.username == user_update.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = user_update.username
        
    if user_update.email is not None:
        if user_update.email and not re.match(r"[^@]+@[^@]+\.[^@]+", user_update.email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        current_user.email = user_update.email
    
    if user_update.bio is not None:
        current_user.bio = user_update.bio
        
    if user_update.avatar is not None:
        current_user.avatar = user_update.avatar
        
    if user_update.preferences is not None:
        # Ensure it's a dict
        current_prefs = dict(current_user.preferences) if current_user.preferences else {}
        current_prefs.update(user_update.preferences)
        current_user.preferences = current_prefs

    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/me/password")
async def update_password_me(password_change: PasswordChange, current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    if len(password_change.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    current_user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()
    return {"message": "Password updated successfully"}
