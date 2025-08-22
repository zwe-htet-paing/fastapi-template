from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


from app.database import get_async_session
from app.models.user import User, UserRole
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_totp_secret,
    verify_totp_code,
    generate_backup_code,
    hash_backup_code,
)
from app.utils.rbac import get_current_user, require_role
from app.schemas.auth import (
    TokenRequest,
    TokenResponse,
    UserOut,
    LoginRequest,
    LoginResponse,
    SignupRequest,
    SignupResponse,
    VerifyTwoFARequest,
    QRCodeResponse,
    BackupCodeResponse
)

import pyotp
import qrcode
import io
import base64

router = APIRouter()

# ----------------- Auth Endpoints -----------------

@router.post("/token", response_model=TokenResponse)
async def token(request: TokenRequest, db: AsyncSession = Depends(get_async_session)) -> TokenResponse:
    # user = await db.query(User).filter(User.email == request.email).first()
    user = (await db.execute(select(User).where(User.email == request.email))).scalars().first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.email, "role": user.role})
    return TokenResponse(
        status=status.HTTP_200_OK,
        message="Token generated successfully", 
        access_token=access_token, 
        token_type="bearer")


@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_async_session)) -> SignupResponse:
    # existing_user = await db.query(User).filter(User.email == request.email).first()
    existing_user = (await db.execute(select(User).where(User.email == request.email))).scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_pw = hash_password(request.password)
    new_user = User(
        username=request.username,
        email=request.email,
        hashed_password=hashed_pw,
        role= UserRole.user,  # Default role
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_access_token({"sub": new_user.email, "role": new_user.role})
    user_out = UserOut(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        role=new_user.role,
        is_2fa_enabled=new_user.is_2fa_enabled,
    )

    return SignupResponse(
        status=status.HTTP_201_CREATED,
        message="Signup successful",
        user=user_out,
        access_token=token,
        token_type="bearer",
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_async_session)) -> LoginResponse:
    # user = await db.query(User).filter(User.email == request.email).first()
    user = (await db.execute(select(User).where(User.email == request.email))).scalars().first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": user.email, "role": user.role})
    user_out = UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_2fa_enabled=user.is_2fa_enabled,
    )

    return LoginResponse(
        status=status.HTTP_200_OK,
        message="Login successful",
        user=user_out,
        access_token=token,
        token_type="bearer",
    )


# ----------------- 2FA Endpoints -----------------

@router.post("/setup-2fa", response_model=QRCodeResponse)
async def setup_2fa(db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    if current_user.is_2fa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is already enabled")

    secret = generate_totp_secret()
    current_user.pending_2fa_secret = secret
    await db.commit()

    totp_uri = pyotp.TOTP(secret).provisioning_uri(name=current_user.email, issuer_name="Your App")
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    qr_base64 = base64.b64encode(buf.getvalue()).decode()

    return QRCodeResponse(
        status=status.HTTP_200_OK,
        message="Scan this QR code with your authenticator app",
        secret=secret,
        qr_code=f"data:image/png;base64,{qr_base64}",
    )


@router.post("/verify-2fa-setup", response_model=BackupCodeResponse)
async def verify_2fa_setup(
    request: VerifyTwoFARequest, 
    db: AsyncSession = Depends(get_async_session), 
    current_user: User = Depends(get_current_user)) -> BackupCodeResponse:
    if not current_user.pending_2fa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending 2FA setup found")
    if not verify_totp_code(current_user.pending_2fa_secret, request.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")

    backup_code = generate_backup_code()
    hashed_backup = hash_backup_code(backup_code)

    current_user.active_2fa_secret = current_user.pending_2fa_secret
    current_user.pending_2fa_secret = None
    current_user.is_2fa_enabled = True
    current_user.backup_2fa_code = hashed_backup
    await db.commit()
    
    return BackupCodeResponse(
        status=status.HTTP_200_OK,
        message="2FA setup completed successfully",
        backup_code=backup_code,
        warning="Save this backup code securely. It can only be used once."
    )


@router.post("/enable-2fa")
async def enable_2fa(db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    if current_user.is_2fa_enabled:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "2FA is already enabled"
            }

    secret = generate_totp_secret()
    current_user.pending_2fa_secret = secret
    db.commit()
    return {
        "status": status.HTTP_200_OK,
        "message": "2FA enabled (pending verification)", 
        "secret": secret
        }


@router.post("/disable-2fa")
async def disable_2fa(db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    if not current_user.is_2fa_enabled:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "2FA is already disabled"
            }

    current_user.is_2fa_enabled = False
    current_user.active_2fa_secret = None
    current_user.pending_2fa_secret = None
    current_user.backup_2fa_code = None
    await db.commit()

    return {
        "status": status.HTTP_200_OK,
        "message": "2FA has been disabled successfully"
        }

@router.post("/verify-2fa")
async def verify_2fa(request: VerifyTwoFARequest, current_user: User = Depends(get_current_user)):
    if not current_user.is_2fa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is not enabled for this user")

    totp_valid = verify_totp_code(current_user.totp_secret, request.code)
    if not totp_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid 2FA code")

    return {
        "status": status.HTTP_200_OK,
        "message": "2FA code verified successfully.",
        }