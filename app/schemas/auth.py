from pydantic import BaseModel, EmailStr
from enum import Enum
from uuid import UUID
from typing import Optional, List
from app.models.user import UserRole

class UserOut(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: UserRole
    is_2fa_enabled: bool
    
class TokenRequest(BaseModel):
    email: EmailStr
    password: str
    
class TokenResponse(BaseModel):
    status: int
    message: str
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    status: int
    message: str
    user: UserOut
    access_token: str
    token_type: str = "bearer"
    
class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class SignupResponse(BaseModel):
    status: int
    message: str
    user: UserOut
    access_token: str
    token_type: str = "bearer"
     
class QRCodeResponse(BaseModel):
    status: int
    message: str
    secret: str
    qr_code: str

class BackupCodeResponse(BaseModel):
    status: int
    message: str
    backup_code: str
    warning: str
    
class VerifyTwoFARequest(BaseModel):
    code: str

class TwoFAStatusResponse(BaseModel):
    status: int
    has_2fa_enabled: bool
    backup_codes_count: int
    setup_pending: bool
    
