"""
SQLAlchemy database setup with SQLite.
Provides session management and base model class.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Required for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and seed initial data."""
    # Import models so they register with Base metadata
    from app.models import call, customer  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Seed demo data if tables are empty
    db = SessionLocal()
    try:
        _seed_demo_data(db)
    finally:
        db.close()


def _seed_demo_data(db):
    """Populate the database with realistic demo data."""
    from app.models.customer import Customer, Order

    if db.query(Customer).count() > 0:
        return  # Already seeded

    customers = [
        Customer(
            id="CUST-001",
            name="Sarah Johnson",
            email="sarah.johnson@email.com",
            phone="+1-555-0101",
            account_status="active",
            membership_tier="premium",
            join_date="2022-03-15",
            total_orders=24,
            notes="Loyal premium customer. Prefers email communication.",
        ),
        Customer(
            id="CUST-002",
            name="Michael Chen",
            email="m.chen@email.com",
            phone="+1-555-0102",
            account_status="active",
            membership_tier="standard",
            join_date="2023-07-20",
            total_orders=8,
            notes="",
        ),
        Customer(
            id="CUST-003",
            name="Emma Rodriguez",
            email="emma.r@email.com",
            phone="+1-555-0103",
            account_status="active",
            membership_tier="premium",
            join_date="2021-11-05",
            total_orders=41,
            notes="VIP customer. High order volume. Priority support.",
        ),
        Customer(
            id="CUST-004",
            name="David Kim",
            email="d.kim@email.com",
            phone="+1-555-0104",
            account_status="suspended",
            membership_tier="standard",
            join_date="2024-01-10",
            total_orders=3,
            notes="Account suspended due to payment issue.",
        ),
        Customer(
            id="CUST-005",
            name="Lisa Thompson",
            email="lisa.t@email.com",
            phone="+1-555-0105",
            account_status="active",
            membership_tier="standard",
            join_date="2023-02-28",
            total_orders=15,
            notes="",
        ),
    ]
    db.add_all(customers)

    orders = [
        Order(
            id="ORD-10001",
            customer_id="CUST-001",
            product_name="Wireless Noise-Cancelling Headphones",
            status="in_transit",
            amount=249.99,
            order_date="2026-08-10",
            estimated_delivery="2026-08-20",
            tracking_number="TRK-9821347",
            carrier="FedEx",
            shipping_address="123 Maple St, Portland, OR 97201",
            notes="Delayed due to carrier backlog in Portland hub.",
        ),
        Order(
            id="ORD-10002",
            customer_id="CUST-001",
            product_name="Smart Home Hub",
            status="delivered",
            amount=89.99,
            order_date="2026-07-25",
            estimated_delivery="2026-08-01",
            tracking_number="TRK-8743291",
            carrier="UPS",
            shipping_address="123 Maple St, Portland, OR 97201",
            notes="",
        ),
        Order(
            id="ORD-10003",
            customer_id="CUST-002",
            product_name="4K Gaming Monitor",
            status="processing",
            amount=499.99,
            order_date="2026-08-16",
            estimated_delivery="2026-08-24",
            tracking_number=None,
            carrier="DHL",
            shipping_address="456 Oak Ave, Seattle, WA 98101",
            notes="",
        ),
        Order(
            id="ORD-10004",
            customer_id="CUST-003",
            product_name="Mechanical Keyboard Pro",
            status="delivered",
            amount=179.99,
            order_date="2026-08-05",
            estimated_delivery="2026-08-12",
            tracking_number="TRK-7654321",
            carrier="UPS",
            shipping_address="789 Pine Rd, San Francisco, CA 94102",
            notes="",
        ),
        Order(
            id="ORD-10005",
            customer_id="CUST-003",
            product_name='Ultrawide Curved Monitor 34"',
            status="in_transit",
            amount=799.99,
            order_date="2026-08-12",
            estimated_delivery="2026-08-19",
            tracking_number="TRK-6543210",
            carrier="FedEx",
            shipping_address="789 Pine Rd, San Francisco, CA 94102",
            notes="Large item — requires signature.",
        ),
        Order(
            id="ORD-10006",
            customer_id="CUST-005",
            product_name="Ergonomic Office Chair",
            status="cancelled",
            amount=329.99,
            order_date="2026-08-08",
            estimated_delivery=None,
            tracking_number=None,
            carrier=None,
            shipping_address="321 Elm St, Austin, TX 78701",
            notes="Customer requested cancellation.",
        ),
        Order(
            id="ORD-10007",
            customer_id="CUST-005",
            product_name="Standing Desk Frame",
            status="in_transit",
            amount=449.99,
            order_date="2026-08-14",
            estimated_delivery="2026-08-22",
            tracking_number="TRK-5432109",
            carrier="UPS",
            shipping_address="321 Elm St, Austin, TX 78701",
            notes="",
        ),
    ]
    db.add_all(orders)
    db.commit()
