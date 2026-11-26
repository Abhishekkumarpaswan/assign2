from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_current_support_staff
from backend.app.models.models import Refund, User, Ticket, Order, AuditLog
from backend.app.schemas.schemas import RefundCreate, RefundReview, RefundResponse
from backend.app.services.refund_service import refund_service, RefundError

router = APIRouter(prefix="/refunds", tags=["Refunds"])

@router.get("", response_model=List[RefundResponse])
def list_refunds(
    status: Optional[str] = Query(None),
    order_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Refund)
    if current_user.role == "customer":
        query = query.filter(Refund.requested_by == current_user.id)
    if status and status != "all":
        query = query.filter(Refund.status == status)
    if order_id:
        query = query.filter(Refund.order_id == order_id)
    return query.order_by(Refund.created_at.desc()).all()

@router.post("", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
def request_refund(
    refund_in: RefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = refund_service.process_refund_request(
            db=db,
            customer_id=current_user.id,
            order_id=refund_in.order_id,
            ticket_id=refund_in.ticket_id,
            amount=refund_in.amount,
            reason=refund_in.reason,
            idempotency_key=refund_in.idempotency_key
        )
        if not result.get("success") and not result.get("duplicate"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Refund request could not be processed.")
            )

        refund_id = result.get("refund_id")
        refund = db.query(Refund).filter(Refund.id == refund_id).first()
        if not refund:
            raise HTTPException(status_code=500, detail="Refund record creation error")
        return refund

    except RefundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/{refund_id}/review", response_model=RefundResponse)
@router.patch("/{refund_id}/review", response_model=RefundResponse)
def review_refund(
    refund_id: str,
    review_in: RefundReview,
    db: Session = Depends(get_db),
    current_staff: User = Depends(get_current_support_staff)
):
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Refund '{refund_id}' not found"
        )

    refund.status = review_in.decision
    refund.reviewed_by = current_staff.id
    refund.decision_reason = review_in.decision_reason or f"Manually reviewed by {current_staff.name}"

    ticket = db.query(Ticket).filter(Ticket.id == refund.ticket_id).first()
    if ticket:
        if review_in.decision == "approved":
            ticket.status = "resolved"
        elif review_in.decision == "rejected":
            ticket.status = "closed"
        elif review_in.decision == "info_requested":
            ticket.status = "in_progress"

    audit = AuditLog(
        action=f"refund_{review_in.decision}",
        entity_type="refund",
        entity_id=refund.id,
        user_id=current_staff.id,
        details={"decision": review_in.decision, "reason": review_in.decision_reason}
    )
    db.add(audit)
    db.commit()
    db.refresh(refund)
    return refund
