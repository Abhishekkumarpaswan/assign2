import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.models import User, Ticket, Message
from backend.app.schemas.schemas import ChatRequest, ChatResponse
from backend.app.services.agent_service import AIProviderError, ai_agent_service

router = APIRouter(tags=["AI Chat Support"])
logger = logging.getLogger(__name__)

class DirectChatRequest(BaseModel):
    ticketId: Optional[str] = None
    ticket_id: Optional[str] = None
    message: str = Field(..., min_length=1)

@router.post("/tickets/{ticket_id}/chat", response_model=ChatResponse)
def chat_with_support_agent(
    ticket_id: str,
    chat_in: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found"
        )

    if current_user.role == "customer" and ticket.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this support conversation"
        )

    try:
        reply_text, _, extra = ai_agent_service.process_chat_message(
            db=db,
            ticket_id=ticket_id,
            customer_id=current_user.id,
            user_message=chat_in.message
        )

        db.refresh(ticket)

        return ChatResponse(
            response=reply_text,
            ticket_status=ticket.status,
            refund_status=extra.get("refund_status"),
            escalated=extra.get("escalated", False) or ticket.status == "escalated"
        )
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        ) from e
    except Exception:
        logger.exception("Support chat processing failed for ticket %s", ticket_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process your support request right now. Please try again later."
        ) from None

@router.post("/chat")
def direct_chat_endpoint(
    chat_in: DirectChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_ticket_id = chat_in.ticketId or chat_in.ticket_id
    ticket = None
    if target_ticket_id:
        ticket = db.query(Ticket).filter(Ticket.id == target_ticket_id).first()
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket '{target_ticket_id}' not found"
            )
        if current_user.role == "customer" and ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this support conversation"
            )
    else:
        # Create ticket automatically if absent per spec 07 §6
        ticket = Ticket(
            customer_id=current_user.id,
            subject=chat_in.message[:60] if chat_in.message else "Support Chat",
            description=chat_in.message,
            category="refund" if any(w in chat_in.message.lower() for w in ["refund", "return", "replace"]) else "general",
            status="open",
            priority="medium"
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

    try:
        reply_text, _, extra = ai_agent_service.process_chat_message(
            db=db,
            ticket_id=ticket.id,
            customer_id=current_user.id,
            user_message=chat_in.message
        )
        db.refresh(ticket)
        return {
            "reply": reply_text,
            "response": reply_text,
            "ticketId": ticket.id,
            "ticket_id": ticket.id,
            "ticket_status": ticket.status,
            "refund_status": extra.get("refund_status"),
            "escalated": extra.get("escalated", False) or ticket.status == "escalated",
            "actions": [{"type": "support_interaction", "summary": extra.get("refund_status", "reply_generated")}]
        }
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        ) from e
    except Exception:
        logger.exception("Direct chat processing failed for ticket %s", ticket.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process your support request right now. Please try again later."
        ) from None

@router.get("/chat/history/{ticket_id}")
def get_chat_history(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role == "customer" and ticket.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    messages = db.query(Message).filter(Message.ticket_id == ticket_id).order_by(Message.created_at.asc()).all()
    return [{
        "id": m.id,
        "sender_type": m.sender_type,
        "content": m.content,
        "created_at": m.created_at.isoformat()
    } for m in messages]
