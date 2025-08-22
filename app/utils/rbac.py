from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_async_session
from app.models.user import User
from app.utils.security import verify_token

# HTTP Bearer scheme
oauth2_scheme = HTTPBearer()


# --- Current User Dependency ---
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Extract user from JWT token.
    """
    token = credentials.credentials
    payload = verify_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # user = await db.query(User).filter(User.email == payload["sub"]).first()
    user = (await db.execute(
        select(User).where(User.email == payload["sub"])
    )).scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


# --- Role-based Dependency ---
def require_role(role: str):
    """
    Enforce that the current user has the required role.
    Usage: Depends(require_role("admin"))
    """
    async def checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return current_user
    return checker


# --- Optional: Multi-role enforcement ---
def require_roles(roles: list[str]):
    """
    Enforce that the current user has one of the allowed roles.
    Usage: Depends(require_roles(["admin", "user"]))
    """
    async def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return current_user

    return checker
