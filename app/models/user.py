from datetime import datetime, timezone
from sqlalchemy import (
    Column, 
    String, 
    Boolean, 
    DateTime, 
    Enum
)
from sqlalchemy.orm import relationship
from app.database import Base

import uuid
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Role-based access
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)
    
    # Two-Factor Authentication (2FA) fields
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    active_2fa_secret = Column(String, nullable=True)
    pending_2fa_secret = Column(String, nullable=True)
    backup_2fa_code = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete")

