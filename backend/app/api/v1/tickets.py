from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_current_support_staff
from backend.app.models.models import Ticket, User, Message, AuditLog
from backend.app.schemas.schemas import (
    TicketCreate, TicketUpdate, TicketResponse, TicketDetailResponse, SupportTicketDetailResponse,
    MessageCreate, MessageResponse
)
from backend.app.services.ticket_service import ticket_service

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.get("", response_model=List[TicketResponse])
def list_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tickets = ticket_service.list_tickets_for_user(
        db=db,
        user_id=current_user.id,
        role=current_user.role,
        status=status,
        priority=priority,
        category=category,
        search=search
    )
    return tickets

@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        desc = ticket_in.description if ticket_in.description and ticket_in.description.strip() else ticket_in.subject
        clean_order_id = ticket_in.order_id if ticket_in.order_id and ticket_in.order_id.strip() else None
        ticket = ticket_service.create_ticket(
            db=db,
            customer_id=current_user.id,
            subject=ticket_in.subject,
            description=desc,
            category=ticket_in.category or "general",
            order_id=clean_order_id,
            priority=ticket_in.priority or "medium"
        )
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket_details(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = ticket_service.get_ticket_for_user(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        role=current_user.role
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found"
        )
    return ticket

@router.get("/{ticket_id}/support-view", response_model=SupportTicketDetailResponse)
def get_support_ticket_details(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_support_staff)
):
    ticket = ticket_service.get_ticket_for_user(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        role=current_user.role
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found"
        )
    return ticket

@router.patch("/{ticket_id}", response_model=TicketResponse)
@router.patch("/{ticket_id}/status", response_model=TicketResponse)
def update_ticket(
    ticket_id: str,
    ticket_in: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = ticket_service.get_ticket_for_user(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        role=current_user.role
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found"
        )

    # Customers can only close their tickets
    if current_user.role == "customer" and ticket_in.status != "closed":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers can only close their own tickets"
        )

    if ticket_in.status:
        ticket.status = ticket_in.status
    if ticket_in.priority and current_user.role in ["support_agent", "admin"]:
        ticket.priority = ticket_in.priority
    if ticket_in.internal_note and current_user.role in ["support_agent", "admin"]:
        audit = AuditLog(
            action="internal_note_added",
            entity_type="ticket",
            entity_id=ticket.id,
            user_id=current_user.id,
            details={"note": ticket_in.internal_note}
        )
        db.add(audit)

    db.commit()
    db.refresh(ticket)
    return ticket

@router.post("/{ticket_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def add_ticket_message(
    ticket_id: str,
    msg_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = ticket_service.get_ticket_for_user(
        db=db,
        ticket_id=ticket_id,
        user_id=current_user.id,
        role=current_user.role
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found"
        )

    sender_type = "agent" if current_user.role in ["support_agent", "admin"] else "customer"
    msg = ticket_service.add_message(
        db=db,
        ticket_id=ticket_id,
        sender_type=sender_type,
        content=msg_in.content
    )
    return msg
