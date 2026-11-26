from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.models.models import Ticket, Message, Escalation, Refund, AuditLog, Order, User, generate_id

class TicketService:
    @staticmethod
    def create_ticket(
        db: Session,
        customer_id: str,
        subject: str,
        description: str,
        category: str = "general",
        order_id: Optional[str] = None,
        priority: str = "medium"
    ) -> Ticket:
        # Validate order if provided
        if order_id:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order or order.customer_id != customer_id:
                raise ValueError("Specified order is invalid or does not belong to the user.")

        ticket = Ticket(
            customer_id=customer_id,
            order_id=order_id,
            subject=subject,
            description=description,
            category=category,
            status="open",
            priority=priority
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        # Record initial customer message
        initial_msg = Message(
            ticket_id=ticket.id,
            sender_type="customer",
            content=description
        )
        db.add(initial_msg)

        # Audit log
        audit = AuditLog(
            id=generate_id("AUD-"),
            action="ticket_created",
            entity_type="ticket",
            entity_id=ticket.id,
            user_id=customer_id,
            details={"category": category, "order_id": order_id, "subject": subject}
        )
        db.add(audit)
        db.commit()

        return ticket

    @staticmethod
    def get_ticket_for_user(db: Session, ticket_id: str, user_id: str, role: str) -> Optional[Ticket]:
        query = db.query(Ticket).filter(Ticket.id == ticket_id)
        if role == "customer":
            query = query.filter(Ticket.customer_id == user_id)
        return query.first()

    @staticmethod
    def list_tickets_for_user(
        db: Session,
        user_id: str,
        role: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Ticket]:
        query = db.query(Ticket)
        if role == "customer":
            query = query.filter(Ticket.customer_id == user_id)
        
        if status and status != "all":
            query = query.filter(Ticket.status == status)
        if priority and priority != "all":
            query = query.filter(Ticket.priority == priority)
        if category and category != "all":
            query = query.filter(Ticket.category == category)
        if search:
            search_fmt = f"%{search}%"
            query = query.filter(
                or_(
                    Ticket.id.ilike(search_fmt),
                    Ticket.subject.ilike(search_fmt),
                    Ticket.description.ilike(search_fmt),
                    Ticket.order_id.ilike(search_fmt)
                )
            )

        return query.order_by(Ticket.created_at.desc()).all()

    @staticmethod
    def add_message(
        db: Session,
        ticket_id: str,
        sender_type: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> Message:
        msg = Message(
            ticket_id=ticket_id,
            sender_type=sender_type,
            content=content,
            tool_calls=tool_calls
        )
        db.add(msg)
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def create_escalation(
        db: Session,
        ticket_id: str,
        summary: str,
        priority: str = "high",
        assigned_to: Optional[str] = None,
        internal_note: Optional[str] = None
    ) -> Escalation:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise ValueError("Ticket not found")

        escalation = Escalation(
            ticket_id=ticket_id,
            summary=summary,
            priority=priority,
            assigned_to=assigned_to,
            decision="pending",
            internal_note=internal_note
        )
        ticket.status = "escalated"
        ticket.priority = priority
        ticket.updated_at = datetime.utcnow()

        db.add(escalation)
        db.commit()
        db.refresh(escalation)

        # Audit log
        audit = AuditLog(
            id=generate_id("AUD-"),
            action="ticket_escalated",
            entity_type="ticket",
            entity_id=ticket_id,
            details={"summary": summary, "priority": priority}
        )
        db.add(audit)
        db.commit()

        return escalation

    @staticmethod
    def review_escalation(
        db: Session,
        escalation_id: str,
        staff_id: str,
        decision: str,
        internal_note: Optional[str] = None
    ) -> Escalation:
        escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not escalation:
            raise ValueError("Escalation record not found")

        escalation.decision = decision
        escalation.assigned_to = staff_id
        if internal_note:
            escalation.internal_note = (
                f"{escalation.internal_note or ''}\n[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] Staff: {internal_note}".strip()
            )
        escalation.updated_at = datetime.utcnow()

        ticket = db.query(Ticket).filter(Ticket.id == escalation.ticket_id).first()
        if ticket:
            if decision == "approved":
                ticket.status = "resolved"
            elif decision == "rejected":
                ticket.status = "closed"
            elif decision == "info_requested":
                ticket.status = "in_progress"
            ticket.updated_at = datetime.utcnow()

        # Update refund status if associated
        refund = db.query(Refund).filter(Refund.ticket_id == escalation.ticket_id).first()
        if refund and refund.status == "escalated":
            if decision in ["approved", "rejected"]:
                refund.status = decision
                refund.reviewed_by = staff_id
                refund.decision_reason = internal_note or f"Manually {decision} by support staff"
                refund.updated_at = datetime.utcnow()

        # Audit log
        audit = AuditLog(
            id=generate_id("AUD-"),
            action=f"escalation_{decision}",
            entity_type="escalation",
            entity_id=escalation.id,
            user_id=staff_id,
            details={"decision": decision, "ticket_id": escalation.ticket_id}
        )
        db.add(audit)
        db.commit()
        db.refresh(escalation)

        return escalation

ticket_service = TicketService()
