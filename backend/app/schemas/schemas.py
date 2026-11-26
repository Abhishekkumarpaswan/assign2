from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, AliasChoices
from typing import Optional, List, Any, Dict
from datetime import datetime

# Token Schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

# User Schemas
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6)

    model_config = {"extra": "forbid"}

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# Order Schemas
class OrderItem(BaseModel):
    id: Optional[str] = None
    name: str
    quantity: int = 1
    price: float
    category: str

class OrderCreate(BaseModel):
    id: str
    customer_id: str
    status: str = "delivered"
    delivery_date: Optional[datetime] = None
    total_amount: float
    category: str = "Wellness & Care"
    item_details: List[Dict[str, Any]] = []

class OrderResponse(BaseModel):
    id: str
    customer_id: str
    status: str
    delivery_date: Optional[datetime] = None
    total_amount: float
    category: str
    item_details: List[Dict[str, Any]]
    created_at: datetime
    is_return_window_open: Optional[bool] = None
    days_since_delivery: Optional[int] = None

    class Config:
        from_attributes = True

# Refund Schemas
class RefundCreate(BaseModel):
    order_id: str
    ticket_id: str
    amount: float
    reason: str
    idempotency_key: Optional[str] = None

class RefundReview(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected|info_requested)$")
    decision_reason: Optional[str] = None

class RefundResponse(BaseModel):
    id: str
    order_id: str
    ticket_id: str
    amount: float
    reason: str
    status: str
    idempotency_key: Optional[str] = None
    requested_by: str
    reviewed_by: Optional[str] = None
    decision_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Escalation Schemas
class EscalationCreate(BaseModel):
    ticket_id: str
    summary: str
    priority: str = "high"
    internal_note: Optional[str] = None

class EscalationDecision(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected|info_requested)$")
    internal_note: Optional[str] = None

class EscalationResponse(BaseModel):
    id: str
    ticket_id: str
    summary: str
    priority: str
    decision: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SupportEscalationResponse(EscalationResponse):
    assigned_to: Optional[str] = None
    internal_note: Optional[str] = None

# Message Schemas
class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: str
    ticket_id: str
    sender_type: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

# Ticket Schemas
class TicketCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None)
    category: Optional[str] = "general"
    order_id: Optional[str] = Field(None, validation_alias=AliasChoices("order_id", "orderId"))
    priority: Optional[str] = "medium"

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @field_validator("order_id", mode="before")
    @classmethod
    def clean_order_id(cls, v):
        if not v or not str(v).strip():
            return None
        return str(v).strip()

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, v):
        if v is None or not str(v).strip():
            return None
        return str(v).strip()

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    internal_note: Optional[str] = None

class TicketResponse(BaseModel):
    id: str
    customer_id: str
    order_id: Optional[str] = None
    subject: str
    description: str
    category: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    customer: Optional[UserResponse] = None
    order: Optional[OrderResponse] = None

    class Config:
        from_attributes = True

class TicketDetailResponse(TicketResponse):
    messages: List[MessageResponse] = []
    refunds: List[RefundResponse] = []
    escalations: List[EscalationResponse] = []

    class Config:
        from_attributes = True

class SupportTicketDetailResponse(TicketDetailResponse):
    escalations: List[SupportEscalationResponse] = []

# Chat / AI Schemas
class ChatRequest(BaseModel):
    ticket_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    ticket_status: str
    refund_status: Optional[str] = None
    escalated: bool = False

# Return Policy Schemas
class ReturnPolicyItem(BaseModel):
    category: str
    window_days: int
    allowed_reasons: List[str]
    non_refundable_items: List[str]
    condition_required: str
    notes: str

TokenResponse.model_rebuild()
