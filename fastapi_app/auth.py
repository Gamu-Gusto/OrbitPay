import os
import secrets
import hashlib
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext

JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-env")
JWT_ALG = "HS256"
ACCESS_TOKEN_MINUTES = 30
REFRESH_TOKEN_DAYS = 30


def _truncate_for_bcrypt(password: str) -> str:
    """Truncate password safely to 72 bytes for bcrypt, preserving UTF-8 character boundaries."""
    encoded = password.encode('utf-8')
    if len(encoded) <= 72:
        return password
    
    # Truncate to 72 bytes and decode, but handle potential incomplete UTF-8 sequences
    truncated_bytes = encoded[:72]
    
    # Find the last complete UTF-8 character by working backwards
    while len(truncated_bytes) > 0:
        try:
            # Try to decode the truncated bytes
            return truncated_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # Remove the last byte and try again
            truncated_bytes = truncated_bytes[:-1]
    
    # If we can't decode anything, return empty string
    return ""


def hash_password(password: str) -> str:
    """Hash password safely with truncation and bcrypt."""
    password = _truncate_for_bcrypt(password)
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against stored bcrypt hash."""
    password = _truncate_for_bcrypt(password)
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(subject: str, roles: list[str]) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": subject,
        "roles": roles,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])


def create_refresh_token() -> tuple[str, str]:
    """Generate a secure refresh token. Returns (raw_token, token_hash)."""
    raw = secrets.token_urlsafe(48)
    h = hashlib.sha256(raw.encode()).hexdigest()
    return raw, h


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


