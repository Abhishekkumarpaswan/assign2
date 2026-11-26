from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.core.security import get_password_hash
from backend.app.models.models import User, Order, Ticket, Message, Refund, Escalation, AuditLog

def init_db():
    Base.metadata.create_all(bind=engine)

def _seed_kinetic_brand(db: Session):
    now = datetime.utcnow()

    # 1. Create Users
    customer1 = User(
        id="usr_aarav_01",
        name="Aarav Sharma",
        email="aarav@example.com",
        password_hash=get_password_hash("Password123!"),
        role="customer",
        created_at=now - timedelta(days=60)
    )

    customer2 = User(
        id="usr_meera_02",
        name="Meera Patel",
        email="meera@example.com",
        password_hash=get_password_hash("Password123!"),
        role="customer",
        created_at=now - timedelta(days=40)
    )

    support_agent = User(
        id="usr_staff_01",
        name="Kavita Reddy (Support Lead)",
        email="support@kinetic.internal",
        password_hash=get_password_hash("AdminPassword123!"),
        role="support_agent",
        created_at=now - timedelta(days=120)
    )

    admin_user = User(
        id="usr_admin_01",
        name="Alex Thorne (Admin)",
        email="admin@kinetic.internal",
        password_hash=get_password_hash("AdminPassword123!"),
        role="admin",
        created_at=now - timedelta(days=120)
    )

    db.add_all([customer1, customer2, support_agent, admin_user])
    db.commit()

    # 2. Create Orders for Customer 1 (Aarav)
    order_1001 = Order(
        id="ORD-1001",
        customer_id=customer1.id,
        status="delivered",
        delivery_date=now - timedelta(days=3),
        total_amount=2499.00,
        category="Wellness & Care",
        item_details=[
            {"name": "Organic Turmeric & Curcumin Extract 500mg", "qty": 1, "price": 1299.00, "category": "Wellness & Care"},
            {"name": "Ashwagandha KSM-66 Deep Sleep Elixir", "qty": 1, "price": 1200.00, "category": "Wellness & Care"}
        ],
        created_at=now - timedelta(days=6)
    )

    order_1002 = Order(
        id="ORD-1002",
        customer_id=customer1.id,
        status="delivered",
        delivery_date=now - timedelta(days=45),
        total_amount=3200.00,
        category="Wellness & Care",
        item_details=[
            {"name": "Premium Cold-Pressed Marine Collagen Complex", "qty": 2, "price": 1600.00, "category": "Wellness & Care"}
        ],
        created_at=now - timedelta(days=50)
    )

    order_1003 = Order(
        id="ORD-1003",
        customer_id=customer1.id,
        status="delivered",
        delivery_date=now - timedelta(days=4),
        total_amount=8750.00,
        category="Health Tech & Devices",
        item_details=[
            {"name": "Kinetic Continuous Glucose Monitoring Reader Kit", "qty": 1, "price": 6250.00, "category": "Health Tech & Devices"},
            {"name": "Hypoallergenic Bio-Sensor Patches (Pack of 3)", "qty": 1, "price": 2500.00, "category": "Health Tech & Devices"}
        ],
        created_at=now - timedelta(days=7)
    )

    order_1004 = Order(
        id="ORD-1004",
        customer_id=customer1.id,
        status="in_transit",
        delivery_date=None,
        total_amount=1850.00,
        category="Personal Care & Clinical",
        item_details=[
            {"name": "Clinical Barrier Repair Ceramide Emulsion", "qty": 1, "price": 1850.00, "category": "Personal Care & Clinical"}
        ],
        created_at=now - timedelta(days=1)
    )

    order_2001 = Order(
        id="ORD-2001",
        customer_id=customer2.id,
        status="delivered",
        delivery_date=now - timedelta(days=2),
        total_amount=1500.00,
        category="Herbal & Botanicals",
        item_details=[
            {"name": "Wildcrafted Holy Basil & Reishi Drops", "qty": 1, "price": 1500.00, "category": "Herbal & Botanicals"}
        ],
        created_at=now - timedelta(days=4)
    )

    db.add_all([order_1001, order_1002, order_1003, order_1004, order_2001])
    db.commit()

    # 3. Create Sample Pre-existing Ticket & Escalation
    ticket1 = Ticket(
        id="TCK-1001",
        customer_id=customer1.id,
        order_id="ORD-1003",
        subject="Sensor sync error and calibration defect",
        description="The sensor reader fails to pair with Bluetooth after 2 days. Requesting a full refund or urgent replacement.",
        category="refund",
        status="escalated",
        priority="high",
        created_at=now - timedelta(hours=6),
        updated_at=now - timedelta(hours=1)
    )
    db.add(ticket1)
    db.commit()

    msg1 = Message(
        ticket_id=ticket1.id,
        sender_type="customer",
        content="Hello, my sensor reader kit (Order ORD-1003) is completely malfunctioning. It gives error code E-42.",
        created_at=now - timedelta(hours=6)
    )
    msg2 = Message(
        ticket_id=ticket1.id,
        sender_type="ai",
        content="I am sorry to hear you are having issues with your Kinetic Glucose Monitoring Kit. Because the order total is ₹8,750 (which exceeds our automated threshold of ₹5,000), I have escalated this case directly to our senior clinical support staff for approval and assistance.",
        tool_calls=[
            {"tool": "get_order_details", "input": {"order_id": "ORD-1003"}, "output": {"status": "delivered", "amount": 8750.0}},
            {"tool": "search_return_policy", "input": {"category": "Health Tech & Devices"}, "output": {"window_days": 30}},
            {"tool": "process_refund", "input": {"order_id": "ORD-1003", "amount": 8750.0}, "output": {"escalated": True, "threshold": 5000.0}}
        ],
        created_at=now - timedelta(hours=5, minutes=58)
    )
    db.add_all([msg1, msg2])

    refund1 = Refund(
        id="REF-1001",
        order_id="ORD-1003",
        ticket_id=ticket1.id,
        amount=8750.00,
        reason="Hardware sensor Bluetooth sync defect",
        status="escalated",
        idempotency_key="seed_ref_ord_1003",
        requested_by=customer1.id,
        created_at=now - timedelta(hours=5, minutes=58),
        updated_at=now - timedelta(hours=5, minutes=58)
    )
    db.add(refund1)

    escalation1 = Escalation(
        id="ESC-1001",
        ticket_id=ticket1.id,
        summary="High-value refund request (₹8,750) for ORD-1003 - Glucose Reader Kit",
        priority="high",
        assigned_to=support_agent.id,
        decision="pending",
        internal_note="Customer reports error E-42. Health Tech warranty covers 30 days. Needs supervisor sign-off.",
        created_at=now - timedelta(hours=5, minutes=58),
        updated_at=now - timedelta(hours=5, minutes=58)
    )
    db.add(escalation1)

    audit1 = AuditLog(
        action="ticket_escalated",
        entity_type="ticket",
        entity_id=ticket1.id,
        user_id=customer1.id,
        details={"reason": "Amount > ₹5,000 threshold", "order_id": "ORD-1003"},
        created_at=now - timedelta(hours=5, minutes=58)
    )
    db.add(audit1)
    db.commit()

def _seed_spec_benchmark(db: Session):
    now = datetime.utcnow()
    priya = User(
        id="usr_priya_01",
        name="Priya Sharma",
        email="priya@example.com",
        password_hash=get_password_hash("Customer@123"),
        role="customer",
        created_at=now - timedelta(days=50)
    )
    rahul = User(
        id="usr_rahul_02",
        name="Rahul Verma",
        email="rahul@example.com",
        password_hash=get_password_hash("Customer@123"),
        role="customer",
        created_at=now - timedelta(days=45)
    )
    support_spec = User(
        id="usr_staff_spec",
        name="Support Agent",
        email="support@shop.local",
        password_hash=get_password_hash("Support@123"),
        role="support_agent",
        created_at=now - timedelta(days=120)
    )
    admin_spec = User(
        id="usr_admin_spec",
        name="Admin User",
        email="admin@shop.local",
        password_hash=get_password_hash("Admin@123"),
        role="admin",
        created_at=now - timedelta(days=120)
    )
    db.add_all([priya, rahul, support_spec, admin_spec])
    db.commit()

    order_p1 = Order(
        id="ORD-P1001",
        customer_id=priya.id,
        status="delivered",
        delivery_date=now - timedelta(days=2),
        total_amount=2499.00,
        category="Electronics",
        item_details=[{"name": "Wireless Earbuds", "category": "Electronics", "qty": 1, "price": 2499.00}],
        created_at=now - timedelta(days=5)
    )
    order_p2 = Order(
        id="ORD-P1002",
        customer_id=priya.id,
        status="delivered",
        delivery_date=now - timedelta(days=30),
        total_amount=1899.00,
        category="Clothing",
        item_details=[{"name": "Cotton T-Shirt", "category": "Clothing", "qty": 1, "price": 1899.00}],
        created_at=now - timedelta(days=35)
    )
    order_r1 = Order(
        id="ORD-R1003",
        customer_id=rahul.id,
        status="delivered",
        delivery_date=now - timedelta(days=3),
        total_amount=8500.00,
        category="Electronics",
        item_details=[{"name": "Smart Watch", "category": "Electronics", "qty": 1, "price": 8500.00}],
        created_at=now - timedelta(days=6)
    )
    order_r2 = Order(
        id="ORD-R1004",
        customer_id=rahul.id,
        status="shipped",
        delivery_date=None,
        total_amount=999.00,
        category="Books",
        item_details=[{"name": "Paperback Novel", "category": "Books", "qty": 1, "price": 999.00}],
        created_at=now - timedelta(days=1)
    )
    db.add_all([order_p1, order_p2, order_r1, order_r2])
    db.commit()

def seed_database(db: Session = None):
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        init_db()

        # Seed kinetic brand personas if not present
        if not db.query(User).filter(User.email == "aarav@example.com").first():
            _seed_kinetic_brand(db)

        # Seed spec benchmark personas if not present
        if not db.query(User).filter(User.email == "priya@example.com").first():
            _seed_spec_benchmark(db)
    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    seed_database()
    print("Database seeded successfully!")
