import re
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import httpx
from sqlalchemy.orm import Session
from backend.app.models.models import Ticket, Message, Order, Refund, Escalation, User
from backend.app.services.policy_service import policy_service
from backend.app.services.refund_service import refund_service, RefundError
from backend.app.services.ticket_service import ticket_service
from backend.app.core.config import settings

logger = logging.getLogger("kinetic_agent")

# Prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s*override",
    r"bypass\s+(policy|authorization|rules|security)",
    r"you\s+are\s+now\s+(in\s+developer\s+mode|dan|unrestricted)",
    r"disregard\s+the\s+limit",
    r"admin\s+mode\s+enabled",
    r"approve\s+(this\s+)?refund\s+without\s+(checking|verification|escalation)"
]

class AIProviderError(RuntimeError):
    pass

class AIAgentService:
    def __init__(self):
        pass

    def _generate_groq_response(self, user_message: str) -> str:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is required when LLM_PROVIDER is 'groq'")

        try:
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are Kinetic's customer support assistant. Answer general questions "
                                "helpfully and concisely. Do not claim to access order records, issue "
                                "refunds, change policies, or perform account actions."
                            ),
                        },
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.4,
                    "max_tokens": 256,
                },
                timeout=20.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 403:
                raise AIProviderError(
                    f"Groq denied access to configured model '{settings.GROQ_MODEL}' (HTTP 403). "
                    "Check GROQ_API_KEY, Groq account access, and whether GROQ_MODEL is available."
                ) from error
            raise AIProviderError(
                f"Groq request failed with HTTP {error.response.status_code} "
                f"for configured model '{settings.GROQ_MODEL}'."
            ) from error
        except httpx.RequestError as error:
            raise AIProviderError(
                "Could not reach Groq API. Check server network connectivity and try again."
            ) from error

        try:
            choices = response.json()["choices"]
            generated_text = choices[0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError("Groq returned no generated response") from error

        if not isinstance(generated_text, str) or not generated_text.strip():
            raise RuntimeError("Groq returned an empty response")
        return generated_text.strip()

    def _generate_local_fallback(
        self,
        user_message: str,
        ticket: Optional[Ticket] = None,
        db: Optional[Session] = None
    ) -> str:
        lowered = user_message.lower()

        # Questions about delivery / transit time or how long actions take
        if any(w in lowered for w in ["time", "how long", "when", "arrive", "eta", "duration", "how many days"]):
            if ticket and ticket.order_id and db:
                order = db.query(Order).filter(Order.id == ticket.order_id).first()
                if order:
                    if order.status == "in_transit":
                        return (
                            f"For Order **{order.id}**, standard courier delivery typically takes **2 to 4 business days** "
                            f"from dispatch. Your package is currently in transit with our logistics partner and on schedule."
                        )
                    elif order.status == "delivered":
                        deliv_str = order.delivery_date.strftime("%B %d, %Y") if order.delivery_date else "recently"
                        return (
                            f"Order **{order.id}** was marked as delivered on {deliv_str}. "
                            f"If you're asking about refund processing, approved refunds typically reflect in your account within **3 to 5 business days**."
                        )
            return (
                "Standard shipping delivery takes **2 to 4 business days**. "
                "Approved refunds are credited to your original payment method within **3 to 5 business days**, "
                "and senior support escalations are typically resolved within **24 to 48 hours**."
            )

        # Questions about policies / return rules
        if any(w in lowered for w in ["policy", "return window", "how to return", "conditions", "rules"]):
            return (
                "Our return policy allows returns within **14 days** of delivery for Wellness & Care items "
                "(and up to **30 days** for Health Tech & Devices), provided items remain in original condition with safety seals intact. "
                "Any refund above ₹5,000 is automatically escalated for senior staff review."
            )

        # Greetings
        if any(w in lowered for w in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]):
            return (
                "Hello! I am your Kinetic AI Support Assistant. I can help you check order delivery statuses, "
                "inspect category return policies, request refunds for eligible items, or connect you with human support. "
                "How may I assist you today?"
            )

        # Default helpful assistant response
        return (
            "I am here to assist with your Kinetic orders, return requests, delivery updates, and support inquiries. "
            "Please provide your Order ID or let me know how I can help!"
        )

    def generate_general_response(
        self,
        user_message: str,
        ticket: Optional[Ticket] = None,
        db: Optional[Session] = None
    ) -> str:
        provider = settings.LLM_PROVIDER.strip().lower()
        if provider == "auto":
            if settings.GEMINI_API_KEY:
                provider = "gemini"
            elif settings.GROQ_API_KEY:
                provider = "groq"
            else:
                provider = "mock"

        if provider == "mock":
            return self._generate_local_fallback(user_message, ticket, db)
        if provider == "groq":
            return self._generate_groq_response(user_message)
        if provider not in {"gemini"}:
            raise RuntimeError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")

        if not settings.GEMINI_API_KEY:
            if provider == "gemini":
                raise RuntimeError("GEMINI_API_KEY is required when LLM_PROVIDER is 'gemini'")
            return self._generate_local_fallback(user_message, ticket, db)

        try:
            response = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent",
                headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                json={
                    "systemInstruction": {
                        "parts": [{
                            "text": (
                                "You are Kinetic's customer support assistant. Answer general questions "
                                "helpfully and concisely. Do not claim to access order records, issue "
                                "refunds, change policies, or perform account actions."
                            )
                        }]
                    },
                    "contents": [{"role": "user", "parts": [{"text": user_message}]}],
                    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 256},
                },
                timeout=20.0,
            )
            response.raise_for_status()
            parts = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
            generated_text = "\n".join(
                part["text"]
                for part in parts
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ).strip()
            if generated_text:
                return generated_text
        except httpx.HTTPStatusError as error:
            if provider == "gemini":
                if error.response.status_code == 403:
                    raise AIProviderError(
                        f"Gemini denied access to configured model '{settings.GEMINI_MODEL}' (HTTP 403). "
                        "Check GEMINI_API_KEY, Generative Language API access, API-key restrictions, "
                        "and whether GEMINI_MODEL is available to your project."
                    ) from error
                raise AIProviderError(
                    f"Gemini request failed with HTTP {error.response.status_code} "
                    f"for configured model '{settings.GEMINI_MODEL}'."
                ) from error
            else:
                logger.warning(
                    f"Gemini API returned HTTP {error.response.status_code}. "
                    "Gracefully falling back to local support reasoning engine."
                )
                return self._generate_local_fallback(user_message, ticket, db)
        except httpx.RequestError as error:
            if provider == "gemini":
                raise AIProviderError(
                    "Could not reach Gemini API. Check server network connectivity and try again."
                ) from error
            else:
                logger.warning(f"Could not reach Gemini API ({error}). Falling back to local reasoning engine.")
                return self._generate_local_fallback(user_message, ticket, db)
        except Exception as error:
            if provider == "gemini":
                raise RuntimeError("Gemini returned no generated response") from error
            logger.warning(f"Gemini error: {error}. Falling back to local reasoning engine.")
            return self._generate_local_fallback(user_message, ticket, db)

        return self._generate_local_fallback(user_message, ticket, db)

    def detect_prompt_injection(self, message: str) -> bool:
        lowered = message.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, lowered):
                return True
        return False

    def extract_order_id(self, text: str, ticket: Ticket, db: Session) -> Optional[str]:
        # 1. Check if explicitly in text (e.g. ORD-1001, ord1001, ORD-2001)
        match = re.search(r"\b(ORD[-\s]?\d{3,6})\b", text, re.IGNORECASE)
        if match:
            raw = match.group(1).upper().replace(" ", "-")
            if not raw.startswith("ORD-"):
                raw = f"ORD-{raw.replace('ORD', '')}"
            return raw

        # 2. Check ticket's linked order_id
        if ticket.order_id:
            return ticket.order_id

        return None

    def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        db: Session,
        customer_id: str,
        ticket: Ticket
    ) -> Dict[str, Any]:
        """
        Server-side controlled tool execution with strict authorization.
        """
        if tool_name == "get_order_details":
            order_id = params.get("order_id")
            if not order_id:
                return {"error": "Missing order_id parameter"}
            order = refund_service.get_order_for_customer(db, order_id=order_id, customer_id=customer_id)
            if not order:
                return {
                    "error": f"Order '{order_id}' was not found or does not belong to your account."
                }
            
            # Calculate delivery days
            days_since = None
            if order.delivery_date:
                days_since = (datetime.utcnow() - order.delivery_date).days

            return {
                "order_id": order.id,
                "status": order.status,
                "category": order.category,
                "total_amount": order.total_amount,
                "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
                "days_since_delivery": days_since,
                "items": order.item_details
            }

        elif tool_name == "search_return_policy":
            category = params.get("category", "General")
            policy = policy_service.search_policy(category)
            return policy

        elif tool_name == "process_refund":
            order_id = params.get("order_id")
            amount = params.get("amount")
            reason = params.get("reason", "Customer initiated refund request")
            
            if not order_id:
                return {"error": "Cannot process refund: missing order_id"}

            try:
                result = refund_service.process_refund_request(
                    db=db,
                    customer_id=customer_id,
                    order_id=order_id,
                    ticket_id=ticket.id,
                    amount=amount,
                    reason=reason
                )
                return result
            except RefundError as e:
                return {"error": e.message, "code": e.code}

        elif tool_name == "escalate_to_human":
            summary = params.get("summary", f"Customer escalation on ticket {ticket.id}")
            priority = params.get("priority", "high")
            escalation = ticket_service.create_escalation(
                db=db,
                ticket_id=ticket.id,
                summary=summary,
                priority=priority,
                internal_note=f"Escalated via AI Agent: {params.get('note', 'Customer requested staff review')}"
            )
            return {
                "escalation_id": escalation.id,
                "priority": escalation.priority,
                "status": "escalated",
                "summary": escalation.summary
            }

        return {"error": f"Unknown tool: {tool_name}"}

    def process_chat_message(
        self,
        db: Session,
        ticket_id: str,
        customer_id: str,
        user_message: str
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Processes an incoming customer message:
        - Stores the customer message
        - Evaluates safety and prompt injection guardrails
        - Determines multi-turn intent (retrieve order, query policy, process refund, or escalate)
        - Executes authorized backend tools
        - Stores the AI response with tool audit record
        """
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise ValueError("Ticket not found")

        # 1. Record customer message
        ticket_service.add_message(
            db=db,
            ticket_id=ticket_id,
            sender_type="customer",
            content=user_message
        )

        tools_executed: List[Dict[str, Any]] = []
        extra_status: Dict[str, Any] = {}

        # 2. Check for Prompt Injection
        if self.detect_prompt_injection(user_message):
            ai_text = (
                "Security Notice: System override instructions and unauthorized policy modifications "
                "are strictly prohibited by Kinetic Security Guardrails. All refund and support actions "
                "remain subject to verified backend business policies and human audit."
            )
            ticket_service.add_message(
                db=db,
                ticket_id=ticket_id,
                sender_type="ai",
                content=ai_text,
                tool_calls=[{"tool": "security_guardrail", "status": "blocked_prompt_injection"}]
            )
            return ai_text, [{"tool": "security_guardrail", "status": "blocked_prompt_injection"}], {"status": ticket.status}

        lowered = user_message.lower()
        is_refund_intent = any(w in lowered for w in ["refund", "money back", "return", "cancel order", "reimburse", "defective"])
        is_order_intent = any(w in lowered for w in ["order", "track", "delivery", "status", "package", "where is", "time", "how long", "when", "eta", "arrive", "shipping", "transit"])
        is_escalation_intent = any(w in lowered for w in ["human", "agent", "manager", "representative", "person", "supervisor", "escalate"])

        order_id = self.extract_order_id(user_message, ticket, db)

        # 3. Handle Escalation to Human request
        if is_escalation_intent and not is_refund_intent:
            res = self.execute_tool(
                "escalate_to_human",
                {"summary": f"Customer requested live agent support: '{user_message[:80]}'", "priority": "medium"},
                db, customer_id, ticket
            )
            tools_executed.append({"tool": "escalate_to_human", "output": res})
            ai_text = (
                "I have escalated your ticket to our customer care team. A human support specialist "
                "will review your conversation history and respond shortly."
            )
            ticket_service.add_message(db, ticket_id, "ai", ai_text, tool_calls=tools_executed)
            return ai_text, tools_executed, {"status": "escalated"}

        # 4. Handle Refund Workflow
        if is_refund_intent:
            # Rule: Missing order ID
            if not order_id:
                ai_text = (
                    "I would be glad to help you with your return or refund request! "
                    "Could you please provide your Order ID (for example, ORD-1001) so I can verify "
                    "the order details and check the applicable return policy for your items?"
                )
                ticket_service.add_message(db, ticket_id, "ai", ai_text, tool_calls=[])
                return ai_text, [], {"status": ticket.status}

            # Link order to ticket if not already set
            if not ticket.order_id:
                ticket.order_id = order_id
                db.commit()

            # Tool 1: get_order_details
            order_data = self.execute_tool("get_order_details", {"order_id": order_id}, db, customer_id, ticket)
            tools_executed.append({"tool": "get_order_details", "input": {"order_id": order_id}, "output": order_data})

            if "error" in order_data:
                ai_text = (
                    f"I was unable to retrieve order '{order_id}'. Please ensure this order was placed "
                    f"under your registered account and that the ID is formatted correctly."
                )
                ticket_service.add_message(db, ticket_id, "ai", ai_text, tool_calls=tools_executed)
                return ai_text, tools_executed, {"status": ticket.status}

            category = order_data.get("category", "General")
            total_amount = order_data.get("total_amount", 0.0)

            # Tool 2: search_return_policy (RAG)
            policy = self.execute_tool("search_return_policy", {"category": category}, db, customer_id, ticket)
            tools_executed.append({"tool": "search_return_policy", "input": {"category": category}, "output": policy})

            # Tool 3: process_refund (Backend enforces all guardrails)
            refund_res = self.execute_tool(
                "process_refund",
                {
                    "order_id": order_id,
                    "amount": total_amount,
                    "reason": user_message
                },
                db, customer_id, ticket
            )
            tools_executed.append({"tool": "process_refund", "input": {"order_id": order_id, "amount": total_amount}, "output": refund_res})

            # Check refund outcomes
            if refund_res.get("duplicate"):
                ai_text = (
                    f"A refund has already been recorded for Order {order_id} (Status: {refund_res.get('status')}). "
                    f"Our system prevents duplicate submissions to protect your account."
                )
                extra_status["refund_status"] = refund_res.get("status")
                extra_status["escalated"] = (refund_res.get("status") == "escalated")

            elif refund_res.get("expired"):
                window_days = refund_res.get("window_days")
                days_since = refund_res.get("days_since_delivery")
                ai_text = (
                    f"I checked the return policy for **{category}**, which allows returns within **{window_days} days** of delivery. "
                    f"Since Order {order_id} was delivered **{days_since} days ago**, the automated return window has expired. "
                    f"As per company policy, we cannot auto-process a refund for this order."
                )
                extra_status["refund_status"] = "rejected_policy_expired"

            elif refund_res.get("escalated"):
                amt = refund_res.get("amount")
                ai_text = (
                    f"I have verified your order **{order_id}** ({category}) with a total of **₹{amt:,.2f}**. "
                    f"Because refunds above ₹5,000 require human authorization, I have escalated your case to our "
                    f"senior support team (Reference: {refund_res.get('refund_id')}). A support agent will review and process your request."
                )
                extra_status["refund_status"] = "escalated"
                extra_status["escalated"] = True

            elif refund_res.get("approved"):
                amt = refund_res.get("amount")
                ref_id = refund_res.get("refund_id")
                ai_text = (
                    f"Great news! Your refund of **₹{amt:,.2f}** for Order **{order_id}** has been **approved** "
                    f"(Transaction Ref: {ref_id}). The funds will be credited to your original payment method "
                    f"within 3-5 business days. Your ticket has been marked as resolved."
                )
                extra_status["refund_status"] = "approved"

            elif "error" in refund_res:
                ai_text = (
                    f"We encountered an issue processing your refund: {refund_res.get('error')}."
                )
                extra_status["refund_status"] = "error"
            else:
                ai_text = (
                    f"We have updated your request for Order {order_id}. Please review your dashboard for latest details."
                )

            ticket_service.add_message(db, ticket_id, "ai", ai_text, tool_calls=tools_executed)
            return ai_text, tools_executed, extra_status

        # 5. Handle General Order Inquiries
        if order_id and is_order_intent:
            order_data = self.execute_tool("get_order_details", {"order_id": order_id}, db, customer_id, ticket)
            tools_executed.append({"tool": "get_order_details", "input": {"order_id": order_id}, "output": order_data})
            if "error" in order_data:
                ai_text = f"I could not locate Order {order_id} in your account records."
            else:
                items_str = ", ".join([f"{item.get('name')} (x{item.get('qty', 1)})" for item in order_data.get('items', [])])
                status = order_data.get('status')
                if status == "in_transit":
                    ai_text = (
                        f"Order **{order_id}** is currently **IN TRANSIT**.\n"
                        f"- **Items**: {items_str}\n"
                        f"- **Total**: ₹{order_data.get('total_amount'):,.2f}\n"
                        f"- **Category**: {order_data.get('category')}\n\n"
                        f"Standard ground delivery takes **2 to 4 business days** from dispatch. Your package is on schedule!"
                    )
                else:
                    deliv = order_data.get('delivery_date') or "In transit"
                    ai_text = (
                        f"Order **{order_id}** status is **{status.upper()}**.\n"
                        f"- **Items**: {items_str}\n"
                        f"- **Total**: ₹{order_data.get('total_amount'):,.2f}\n"
                        f"- **Delivery**: {deliv}\n\n"
                        f"How can I assist you further with this order?"
                    )
            ticket_service.add_message(db, ticket_id, "ai", ai_text, tool_calls=tools_executed)
            return ai_text, tools_executed, {"status": ticket.status}

        # 6. Default Helpful Conversational Response
        ai_text = self.generate_general_response(user_message, ticket, db)
        ticket_service.add_message(db, ticket_id, "ai", ai_text, tool_calls=[])
        return ai_text, [], {"status": ticket.status}

ai_agent_service = AIAgentService()
