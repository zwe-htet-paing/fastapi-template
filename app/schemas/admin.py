from pydantic import BaseModel, EmailStr
from enum import Enum
from uuid import UUID
from typing import Optional, List
from app.models.user import UserRole

class UpdateUserRoleRequest(BaseModel):
    user_id: UUID
    new_role: UserRole