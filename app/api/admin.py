from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_async_session
from app.models.user import User, UserRole
from app.utils.rbac import require_role
from app.schemas.admin import UpdateUserRoleRequest

router = APIRouter()


# --- Get all users (admin only) ---
@router.get("/users", dependencies=[Depends(require_role("admin"))])
async def get_all_users(db: AsyncSession = Depends(get_async_session),):
    # users = db.query(User).all()
    users = (await db.execute(select(User))).scalars().all()
    return {
        "status": status.HTTP_200_OK,
        "message": "Users retrieved successfully",
        "data": [user for user in users]
    }


# --- Update user role (admin only) ---
@router.post("/update-role")
async def update_user_role(
    request: UpdateUserRoleRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(require_role("admin"))
):
    if current_user.role != UserRole.admin.value:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # user = db.query(User).filter(User.id == request.user_id).first()
    user = (await db.execute(select(User).where(User.id == request.user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.new_role not in [r.value for r in UserRole]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user.role = request.new_role
    await db.commit()
    await db.refresh(user)
    return {
        "status": status.HTTP_200_OK,
        "message": f"User role updated to {user.role}", 
        "data": user
        }
