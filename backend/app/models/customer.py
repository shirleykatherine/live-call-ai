"""ORM models for customers and orders."""
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    account_status = Column(String, default="active")
    membership_tier = Column(String, default="standard")
    join_date = Column(String, nullable=True)
    total_orders = Column(Integer, default=0)
    notes = Column(Text, default="")

    orders = relationship("Order", back_populates="customer")
    calls = relationship("Call", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    product_name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # processing, in_transit, delivered, cancelled, returned
    amount = Column(Float, nullable=False)
    order_date = Column(String, nullable=False)
    estimated_delivery = Column(String, nullable=True)
    tracking_number = Column(String, nullable=True)
    carrier = Column(String, nullable=True)
    shipping_address = Column(Text, nullable=True)
    notes = Column(Text, default="")

    customer = relationship("Customer", back_populates="orders")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)
    call_id = Column(String, nullable=True)
    order_id = Column(String, nullable=True)
    issue_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, default="medium")
    status = Column(String, default="open")
    created_at = Column(String, nullable=False)
    resolution = Column(Text, nullable=True)
