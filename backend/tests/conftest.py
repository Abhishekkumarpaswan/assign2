import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LLM_PROVIDER"] = "mock"

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.models.models import User, Order, Ticket, Message, Refund, Escalation

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def seed_users_and_orders(db):
    now = datetime.utcnow()

    # User 1: Customer A
    user1 = User(
        id="cust_01",
        name="Customer Alice",
        email="alice@example.com",
        password_hash=get_password_hash("Secret123!"),
        role="customer"
    )
    # User 2: Customer B
    user2 = User(
        id="cust_02",
        name="Customer Bob",
        email="bob@example.com",
        password_hash=get_password_hash("Secret123!"),
        role="customer"
    )
    # User 3: Support Staff
    support = User(
        id="staff_01",
        name="Support Specialist",
        email="agent@kinetic.internal",
        password_hash=get_password_hash("StaffSecret123!"),
        role="support_agent"
    )

    db.add_all([user1, user2, support])
    db.commit()

    # Order 1: Eligible (Delivered 2 days ago, ₹1,999)
    ord_eligible = Order(
        id="ORD-ELIGIBLE",
        customer_id=user1.id,
        status="delivered",
        delivery_date=now - timedelta(days=2),
        total_amount=1999.0,
        category="Wellness & Care",
        item_details=[{"name": "Organic Herbal Elixir", "price": 1999.0, "qty": 1}]
    )

    # Order 2: Expired Return Window (Delivered 40 days ago, ₹2,500)
    ord_expired = Order(
        id="ORD-EXPIRED",
        customer_id=user1.id,
        status="delivered",
        delivery_date=now - timedelta(days=40),
        total_amount=2500.0,
        category="Wellness & Care",
        item_details=[{"name": "Vitamins Pack", "price": 2500.0, "qty": 1}]
    )

    # Order 3: High Value > ₹5,000 (Delivered 3 days ago, ₹7,499)
    ord_high = Order(
        id="ORD-HIGHVAL",
        customer_id=user1.id,
        status="delivered",
        delivery_date=now - timedelta(days=3),
        total_amount=7499.0,
        category="Health Tech & Devices",
        item_details=[{"name": "Smart Clinical Monitor", "price": 7499.0, "qty": 1}]
    )

    # Order 4: Belongs to Customer Bob
    ord_bob = Order(
        id="ORD-BOB-01",
        customer_id=user2.id,
        status="delivered",
        delivery_date=now - timedelta(days=1),
        total_amount=1200.0,
        category="Wellness & Care",
        item_details=[{"name": "Sleep Drops", "price": 1200.0, "qty": 1}]
    )

    db.add_all([ord_eligible, ord_expired, ord_high, ord_bob])
    db.commit()

    return {
        "alice": user1,
        "bob": user2,
        "staff": support,
        "orders": {
            "eligible": ord_eligible,
            "expired": ord_expired,
            "high": ord_high,
            "bob": ord_bob
        }
    }

def get_auth_headers(user_id: str, role: str) -> dict:
    token = create_access_token(subject=user_id, role=role)
    return {"Authorization": f"Bearer {token}"}
