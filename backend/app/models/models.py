import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, Boolean
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_id(prefix: str = "") -> str:
    short_uuid = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{short_uuid}" if prefix else short_uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("usr_"), index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="customer")  # 'customer', 'support_agent', 'admin'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="customer", foreign_keys="Ticket.customer_id", cascade="all, delete-orphan")

class Order(Base):
    __tablename__ = "orders"

    id = Column(String(50), primary_key=True, index=True)  # e.g. ORD-1001
    customer_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="delivered")  # delivered, in_transit, processing, cancelled, returned
    delivery_date = Column(DateTime, nullable=True)
    total_amount = Column(Float, nullable=False)  # in ₹ INR
    category = Column(String(50), nullable=False, default="Wellness & Care")
    item_details = Column(JSON, nullable=False, default=list)  # list of items: [{name, qty, price, category}]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("User", back_populates="orders")
    tickets = relationship("Ticket", back_populates="order")
    refunds = relationship("Refund", back_populates="order")

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("TCK-"), index=True)
    customer_id = Column(String(50), ForeignKey("users.id"), nullable=False, index=True)
    order_id = Column(String(50), ForeignKey("orders.id"), nullable=True, index=True)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="general")  # refund, order_status, product_issue, general
    status = Column(String(30), nullable=False, default="open")  # open, in_progress, escalated, resolved, closed
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, urgent
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer = relationship("User", back_populates="tickets", foreign_keys=[customer_id])
    order = relationship("Order", back_populates="tickets")
    messages = relationship("Message", back_populates="ticket", cascade="all, delete-orphan", order_by="Message.created_at")
    refunds = relationship("Refund", back_populates="ticket", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="ticket", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("msg_"), index=True)
    ticket_id = Column(String(50), ForeignKey("tickets.id"), nullable=False, index=True)
    sender_type = Column(String(20), nullable=False)  # 'customer', 'ai', 'agent', 'system'
    content = Column(Text, nullable=False)
    tool_calls = Column(JSON, nullable=True)  # log of AI tool calls for transparency
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="messages")

class Refund(Base):
    __tablename__ = "refunds"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("REF-"), index=True)
    order_id = Column(String(50), ForeignKey("orders.id"), nullable=False, index=True)
    ticket_id = Column(String(50), ForeignKey("tickets.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(String(30), nullable=False, default="pending_review")  # pending_review, escalated, approved, rejected
    idempotency_key = Column(String(100), unique=True, index=True, nullable=True)
    requested_by = Column(String(50), ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(String(50), ForeignKey("users.id"), nullable=True)
    decision_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    order = relationship("Order", back_populates="refunds")
    ticket = relationship("Ticket", back_populates="refunds")

class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("ESC-"), index=True)
    ticket_id = Column(String(50), ForeignKey("tickets.id"), nullable=False, index=True)
    summary = Column(String(255), nullable=False)
    priority = Column(String(20), nullable=False, default="high")  # low, medium, high, urgent
    assigned_to = Column(String(50), ForeignKey("users.id"), nullable=True)
    decision = Column(String(30), nullable=False, default="pending")  # pending, approved, rejected, info_requested
    internal_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="escalations")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("AUD-"), index=True)
    action = Column(String(50), nullable=False)  # refund_requested, refund_approved, refund_rejected, ticket_escalated, etc.
    entity_type = Column(String(30), nullable=False)  # refund, ticket, order
    entity_id = Column(String(50), nullable=False, index=True)
    user_id = Column(String(50), nullable=True, index=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
