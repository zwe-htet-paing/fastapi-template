import os
import stripe
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_session
from app.utils.rbac import get_current_user
from app.models.user import User, Subscription

# 🔑 Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
PRICE_IDS = ["price_1S3LdN1G47fopV1p2KVkHMu7", "price_1S3Ldk1G47fopV1pL4XX12zU"]  # replace with your Stripe Price IDs

router = APIRouter()

@router.get("/products")
async def list_products():
    """Return available subscription products."""
    price_objs = [stripe.Price.retrieve(pid) for pid in PRICE_IDS]
    return {"prices": price_objs}

class CheckoutRequest(BaseModel):
    price_id: str
    
@router.post("/create-checkout-session")
async def create_checkout_session(
    req: CheckoutRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Create a Stripe checkout session."""
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": req.price_id, 
                    "quantity": 1
                }
            ],
            mode="subscription",
            success_url=str(request.base_url) + "products?success=1&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=str(request.base_url) + "products?canceled=1",
            client_reference_id=str(user.id),
        )
        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_session)):
    """Handle Stripe webhooks."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        sub_id = data["subscription"]
        user_id = data.get("client_reference_id")

        user = db.query(User).get(user_id)
        if not user:
            return JSONResponse({"error": "User not found"}, status_code=404)

        sub = stripe.Subscription.retrieve(sub_id)

        subscription, _ = db.merge(
            Subscription(
                user_id=user.id,
                stripe_subscription_id=sub_id,
                status=sub["status"],
                current_period_end=datetime.fromtimestamp(
                    sub["current_period_end"], tz=timezone.utc
                )
                if sub.get("current_period_end")
                else None,
            )
        )
        db.add(subscription)
        db.commit()
        
        print("Subscription created:", subscription)

    elif event_type == "customer.subscription.updated":
        db.query(Subscription).filter(
            Subscription.stripe_subscription_id == data["id"]
        ).update(
            {
                "status": data["status"],
                "current_period_end": datetime.fromtimestamp(
                    data["current_period_end"], tz=timezone.utc
                )
                if data.get("current_period_end")
                else None,
            }
        )
        db.commit()

    elif event_type in ("customer.subscription.deleted", "invoice.payment_failed"):
        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == data["id"]
        ).first()
        if sub:
            sub.status = "canceled"
            db.commit()

    return {"status": "success"}


@router.post("/cancel-subscription")
async def cancel_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    """Cancel user's active subscription."""
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.status == "active")
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")

    stripe.Subscription.modify(sub.stripe_subscription_id, cancel_at_period_end=True)
    return {"message": "Subscription canceled at period end"}