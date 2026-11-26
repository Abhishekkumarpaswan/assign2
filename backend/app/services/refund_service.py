from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import Order, Ticket, Refund, Escalation, AuditLog, generate_id
from backend.app.services.policy_service import policy_service
from backend.app.core.config import settings

class RefundError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "REFUND_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code

class RefundService:
    @staticmethod
    def get_order_for_customer(db: Session, order_id: str, customer_id: str) -> Optional[Order]:
        """
        Secure retrieval: ensures customer can only access their own order.
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return None
        if order.customer_id != customer_id:
            # Does not disclose the existence of another customer's order
            return None
        return order

    @staticmethod
    def process_refund_request(
        db: Session,
        customer_id: str,
        order_id: str,
        ticket_id: str,
        amount: Optional[float] = None,
        reason: str = "Customer requested refund",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes strict backend guardrails for refunds:
        - Ownership verification
        - Delivery date & Return window verification (via Policy RAG)
        - Max auto-approval threshold (₹5,000 guardrail)
        - Duplicate / Idempotency protection
        - Audit trail logging
        """
        # 1. Ticket check
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise RefundError("Associated ticket not found", status_code=404, code="TICKET_NOT_FOUND")

        # 2. Ownership verification
        order = RefundService.get_order_for_customer(db, order_id=order_id, customer_id=customer_id)
        if not order:
            raise RefundError(
                f"Order '{order_id}' was not found or does not belong to your account.",
                status_code=403,
                code="UNAUTHORIZED_ORDER_ACCESS"
            )

        # 3. Order status check
        if order.status.lower() not in ["delivered", "processing", "in_transit"]:
            raise RefundError(
                f"Order {order_id} has status '{order.status}'. Refunds can only be initiated for delivered or in-transit orders.",
                status_code=400,
                code="INVALID_ORDER_STATUS"
            )

        # 4. Duplicate / Idempotency check
        if idempotency_key:
            existing_by_key = db.query(Refund).filter(Refund.idempotency_key == idempotency_key).first()
            if existing_by_key:
                return {
                    "success": True,
                    "duplicate": True,
                    "refund_id": existing_by_key.id,
                    "status": existing_by_key.status,
                    "amount": existing_by_key.amount,
                    "message": f"Refund request already processed with reference {existing_by_key.id} (Status: {existing_by_key.status})."
                }

        existing_refund = db.query(Refund).filter(
            Refund.order_id == order_id,
            Refund.status.in_(["approved", "escalated", "pending_review"])
        ).first()

        if existing_refund:
            return {
                "success": False,
                "duplicate": True,
                "refund_id": existing_refund.id,
                "status": existing_refund.status,
                "amount": existing_refund.amount,
                "error": f"A refund request ({existing_refund.id}) is already active or approved for order {order_id}."
            }

        # 5. Amount validation
        target_amount = amount if amount and amount > 0 else order.total_amount
        if target_amount > order.total_amount:
            target_amount = order.total_amount

        # 6. Return window check (via Category Policy)
        policy = policy_service.search_policy(order.category)
        window_days = policy.get("window_days", settings.DEFAULT_RETURN_WINDOW_DAYS)

        if order.delivery_date:
            days_since_delivery = (datetime.utcnow() - order.delivery_date).days
            if days_since_delivery > window_days:
                # Expired return window
                # Record ticket interaction and explain policy outcome
                ticket.status = "closed"
                ticket.updated_at = datetime.utcnow()

                audit = AuditLog(
                    action="refund_rejected_window_expired",
                    entity_type="order",
                    entity_id=order.id,
                    user_id=customer_id,
                    details={
                        "order_id": order.id,
                        "ticket_id": ticket.id,
                        "delivery_date": order.delivery_date.isoformat(),
                        "days_since_delivery": days_since_delivery,
                        "allowed_window_days": window_days,
                        "category": order.category
                    }
                )
                db.add(audit)
                db.commit()

                return {
                    "success": False,
                    "expired": True,
                    "window_days": window_days,
                    "days_since_delivery": days_since_delivery,
                    "category": order.category,
                    "error": f"The return window for '{order.category}' is {window_days} days. This order was delivered {days_since_delivery} days ago and is no longer eligible for automated refund."
                }

        # 7. Threshold Guardrail: > ₹5,000 must be escalated to human
        if target_amount > settings.MAX_AUTO_REFUND_AMOUNT:
            refund = Refund(
                id=generate_id("REF-"),
                order_id=order.id,
                ticket_id=ticket.id,
                amount=target_amount,
                reason=reason,
                status="escalated",
                idempotency_key=idempotency_key or f"ref_{order.id}_{datetime.utcnow().timestamp()}",
                requested_by=customer_id
            )
            db.add(refund)
            db.flush()

            escalation = Escalation(
                id=generate_id("ESC-"),
                ticket_id=ticket.id,
                summary=f"High-value refund request of ₹{target_amount:,.2f} for Order {order.id}",
                priority="urgent" if target_amount > 10000 else "high",
                decision="pending",
                internal_note=f"Automated guardrail: Amount ₹{target_amount:,.2f} exceeds auto-approval threshold of ₹5,000. Customer requested reason: '{reason}'. Policy window verified."
            )
            db.add(escalation)

            ticket.status = "escalated"
            ticket.priority = "high"
            ticket.updated_at = datetime.utcnow()

            audit = AuditLog(
                id=generate_id("AUD-"),
                action="refund_escalated_high_value",
                entity_type="refund",
                entity_id=refund.id,
                user_id=customer_id,
                details={
                    "order_id": order.id,
                    "ticket_id": ticket.id,
                    "amount": target_amount,
                    "threshold": settings.MAX_AUTO_REFUND_AMOUNT
                }
            )
            db.add(audit)
            db.commit()
            db.refresh(refund)

            return {
                "success": True,
                "escalated": True,
                "approved": False,
                "refund_id": refund.id,
                "amount": target_amount,
                "status": "escalated",
                "message": f"Refund of ₹{target_amount:,.2f} exceeds the automatic threshold of ₹{settings.MAX_AUTO_REFUND_AMOUNT:,.0f}. An escalation case has been opened and assigned to human support for review."
            }

        # 8. Auto-approve eligible refund <= ₹5,000
        refund = Refund(
            id=generate_id("REF-"),
            order_id=order.id,
            ticket_id=ticket.id,
            amount=target_amount,
            reason=reason,
            status="approved",
            idempotency_key=idempotency_key or f"ref_{order.id}_{datetime.utcnow().timestamp()}",
            requested_by=customer_id,
            decision_reason="Automated approval: verified ownership, category policy window, and amount threshold."
        )
        db.add(refund)
        db.flush()

        ticket.status = "resolved"
        ticket.updated_at = datetime.utcnow()

        audit = AuditLog(
            id=generate_id("AUD-"),
            action="refund_auto_approved",
            entity_type="refund",
            entity_id=refund.id,
            user_id=customer_id,
            details={
                "order_id": order.id,
                "ticket_id": ticket.id,
                "amount": target_amount,
                "category": order.category
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(refund)

        return {
            "success": True,
            "escalated": False,
            "approved": True,
            "refund_id": refund.id,
            "amount": target_amount,
            "status": "approved",
            "message": f"Refund of ₹{target_amount:,.2f} has been approved and credited back to your original payment method. Ticket {ticket.id} marked as resolved."
        }

refund_service = RefundService()
