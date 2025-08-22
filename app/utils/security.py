import os
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt
import pyotp
import secrets
import hashlib
import hmac

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret") # For JWT token
ALGORITHM = "HS256"


# --- Password Hashing ---
def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify bcrypt hashed password."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


# --- JWT Token ---
def create_access_token(
    data: dict, expires_delta: timedelta = timedelta(hours=12)
) -> str:
    """Generate a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Verify JWT token and return payload data."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None


# --- 2FA (TOTP) ---
def generate_totp_secret() -> str:
    """Generate a new TOTP secret."""
    return pyotp.random_base32()


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """Verify TOTP code with optional time window tolerance."""
    if not secret or not code:
        return False
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    except Exception:
        return False


# --- 2FA Backup Code (Single) ---
def generate_backup_code() -> str:
    """Generate a single backup code."""
    return secrets.token_hex(4).upper()


def hash_backup_code(code: str) -> str:
    """Hash backup code for secure storage."""
    return hashlib.sha256(code.encode()).hexdigest()


def verify_backup_code(code: str, hashed_code: str) -> bool:
    """Verify backup code against its hash securely."""
    return hmac.compare_digest(hash_backup_code(code), hashed_code)
