"""
Customer-related tools — used by the LangGraph agent.
These query the SQLite database; never fabricate data.
"""
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.customer import Customer

logger = logging.getLogger(__name__)


def get_customer(customer_id: str) -> dict:
    """
    Retrieve customer information by customer ID.
    Returns customer details or an error message if not found.
    """
    db: Session = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {
                "success": False,
                "error": f"Customer with ID '{customer_id}' not found.",
                "data": None,
            }
        return {
            "success": True,
            "data": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "account_status": customer.account_status,
                "membership_tier": customer.membership_tier,
                "join_date": customer.join_date,
                "total_orders": customer.total_orders,
                "notes": customer.notes,
            },
        }
    except Exception as e:
        logger.error(f"get_customer error: {e}")
        return {"success": False, "error": str(e), "data": None}
    finally:
        db.close()


def search_customer_by_email(email: str) -> dict:
    """Find a customer by email address."""
    db: Session = SessionLocal()
    try:
        customer = db.query(Customer).filter(
            Customer.email.ilike(f"%{email}%")
        ).first()
        if not customer:
            return {
                "success": False,
                "error": f"No customer found with email matching '{email}'.",
                "data": None,
            }
        return {
            "success": True,
            "data": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "account_status": customer.account_status,
                "membership_tier": customer.membership_tier,
            },
        }
    except Exception as e:
        logger.error(f"search_customer_by_email error: {e}")
        return {"success": False, "error": str(e), "data": None}
    finally:
        db.close()
