# auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import database
from jose import jwt, JWTError

# Handle masalah bcrypt version incompatibility
import bcrypt

# Konfigurasi Secret Key (HARUS DIUBAH DI PRODUCTION)
SECRET_KEY = "ini_kunci_rahasia_saya_123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Fungsi hashing dan verifikasi password menggunakan bcrypt langsung
def verify_password(plain_password, hashed_password):
    # Potong password jika lebih dari 72 karakter untuk menghindari batasan bcrypt
    if len(plain_password) > 72:
        plain_password = plain_password[:72]
    # Decode hashed_password jika dalam bentuk string (bukan bytes)
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    try:
        return bcrypt.checkpw(plain_password, hashed_password)
    except ValueError:
        # Jika terjadi error karena password terlalu panjang, kembalikan False
        return False

def get_password_hash(password):
    # Potong password jika lebih dari 72 karakter untuk menghindari batasan bcrypt
    if len(password) > 72:
        password = password[:72]
    if isinstance(password, str):
        password = password.encode('utf-8')
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def decode_access_token(token: str):
    try:
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Kita kembalikan payload lengkapnya, atau email saja
        return payload
    except JWTError:
        # Jika token invalid atau expired, return None
        return None

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tidak bisa memvalidasi credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(database.User).filter(database.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user