from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_support_staff
from backend.app.models.models import Escalation, User
from backend.app.schemas.schemas import EscalationDecision, EscalationResponse
from backend.app.services.ticket_service import ticket_service

router = APIRouter(prefix="/escalations", tags=["Escalations"])

@router.get("", response_model=List[EscalationResponse])
def list_escalations(
    decision: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_staff: User = Depends(get_current_support_staff)
):
    query = db.query(Escalation)
    if decision and decision != "all":
        query = query.filter(Escalation.decision == decision)
    if priority and priority != "all":
        query = query.filter(Escalation.priority == priority)
    return query.order_by(Escalation.created_at.desc()).all()

@router.post("/{escalation_id}/decision", response_model=EscalationResponse)
@router.patch("/{escalation_id}/decision", response_model=EscalationResponse)
def decide_escalation(
    escalation_id: str,
    decision_in: EscalationDecision,
    db: Session = Depends(get_db),
    current_staff: User = Depends(get_current_support_staff)
):
    try:
        updated = ticket_service.review_escalation(
            db=db,
            escalation_id=escalation_id,
            staff_id=current_staff.id,
            decision=decision_in.decision,
            internal_note=decision_in.internal_note
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
