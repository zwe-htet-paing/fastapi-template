from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

import uuid
import enum

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    
    
class SubscriptionPlan(str, enum.Enum):
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"
    
    
# --- Subscription Model ---
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stripe_subscription_id = Column(String, unique=True, index=True, nullable=False)

    plan = Column(Enum(SubscriptionPlan), nullable=True)  # optional, can derive from Stripe Price
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)

    current_period_end = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # optional Stripe metadata
    payment_provider = Column(String, default="stripe")
    payment_ref = Column(String, nullable=True)  # e.g., Stripe invoice ID

    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # relationship
    user = relationship("User", back_populates="subscriptions")