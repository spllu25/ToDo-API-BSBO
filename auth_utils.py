from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv
load_dotenv()

# Секретный ключ для подписи JWT (НИКОГДА не публикуйте в коде!)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 часа


# Вместо sha256_crypt верните bcrypt с обработкой длинных паролей:
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Хеширует пароль с обработкой ограничения bcrypt (72 байта)"""
    # Проверяем длину в байтах
    password_bytes = password.encode('utf-8')
    
    if len(password_bytes) > 72:
        # Если пароль слишком длинный, сначала хешируем его SHA-256
        password = hashlib.sha256(password_bytes).hexdigest()
    
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль"""
    password_bytes = plain_password.encode('utf-8')
    
    if len(password_bytes) > 72:
        # Если пароль длинный, хешируем его SHA-256 для сравнения
        plain_password = hashlib.sha256(password_bytes).hexdigest()
    
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] =
    None) -> str: 
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None