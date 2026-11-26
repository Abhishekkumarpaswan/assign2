from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.models import Order, User, Refund
from backend.app.schemas.schemas import OrderResponse
from backend.app.services.policy_service import policy_service
from backend.app.core.config import settings

router = APIRouter(prefix="/orders", tags=["Orders"])

def enrich_order_response(order: Order) -> OrderResponse:
    days_since = None
    is_open = False
    if order.delivery_date:
        days_since = (datetime.utcnow() - order.delivery_date).days
        policy = policy_service.search_policy(order.category)
        window_days = policy.get("window_days", settings.DEFAULT_RETURN_WINDOW_DAYS)
        is_open = days_since <= window_days

    return OrderResponse(
        id=order.id,
        customer_id=order.customer_id,
        status=order.status,
        delivery_date=order.delivery_date,
        total_amount=order.total_amount,
        category=order.category,
        item_details=order.item_details or [],
        created_at=order.created_at,
        is_return_window_open=is_open,
        days_since_delivery=days_since
    )

@router.get("", response_model=List[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Order)
    if current_user.role == "customer":
        query = query.filter(Order.customer_id == current_user.id)
    orders = query.order_by(Order.created_at.desc()).all()
    return [enrich_order_response(o) for o in orders]

@router.get("/{order_id}", response_model=OrderResponse)
def get_order_by_id(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found"
        )
    # Role-based access check
    if current_user.role == "customer" and order.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found"  # Don't disclose other users' order existence
        )

    return enrich_order_response(order)

@router.get("/{order_id}/eligibility")
def get_order_eligibility(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or (current_user.role == "customer" and order.customer_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found"
        )

    policy = policy_service.search_policy(order.category)
    window_days = policy.get("window_days", settings.DEFAULT_RETURN_WINDOW_DAYS)
    days_since = (datetime.utcnow() - order.delivery_date).days if order.delivery_date else None

    reasons = []
    eligible = True
    if order.status.lower() != "delivered":
        eligible = False
        reasons.append(f"Order status is '{order.status}'. Refunds are only permitted for delivered orders.")
    if days_since is not None and days_since > window_days:
        eligible = False
        reasons.append(f"Return window of {window_days} days has expired ({days_since} days since delivery).")

    existing_refund = db.query(Refund).filter(
        Refund.order_id == order.id,
        Refund.status.in_(["approved", "escalated", "pending_review"])
    ).first()
    if existing_refund:
        eligible = False
        reasons.append(f"An active refund ({existing_refund.id}) is already recorded with status '{existing_refund.status}'.")

    return {
        "eligible": eligible,
        "reasons": reasons,
        "returnWindowDays": window_days,
        "daysSinceDelivery": days_since,
        "refundableAmount": float(order.total_amount) if eligible else 0.0
    }
