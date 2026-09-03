"""
Order-related tools — used by the LangGraph agent.
"""
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.customer import Order, Customer

logger = logging.getLogger(__name__)


def get_order_status(order_id: str) -> dict:
    """
    Get detailed status of a specific order including tracking info.
    """
    db: Session = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {
                "success": False,
                "error": f"Order '{order_id}' not found. Please verify the order ID.",
                "data": None,
            }
        return {
            "success": True,
            "data": {
                "order_id": order.id,
                "customer_id": order.customer_id,
                "product_name": order.product_name,
                "status": order.status,
                "amount": order.amount,
                "order_date": order.order_date,
                "estimated_delivery": order.estimated_delivery,
                "tracking_number": order.tracking_number or "Not yet assigned",
                "carrier": order.carrier or "TBD",
                "shipping_address": order.shipping_address,
                "notes": order.notes,
            },
        }
    except Exception as e:
        logger.error(f"get_order_status error: {e}")
        return {"success": False, "error": str(e), "data": None}
    finally:
        db.close()


def get_customer_orders(customer_id: str) -> dict:
    """Get all orders for a given customer."""
    db: Session = SessionLocal()
    try:
        # Verify customer exists
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {
                "success": False,
                "error": f"Customer '{customer_id}' not found.",
                "data": None,
            }

        orders = db.query(Order).filter(Order.customer_id == customer_id).all()
        return {
            "success": True,
            "data": {
                "customer_name": customer.name,
                "customer_id": customer_id,
                "total_orders": len(orders),
                "orders": [
                    {
                        "order_id": o.id,
                        "product_name": o.product_name,
                        "status": o.status,
                        "amount": o.amount,
                        "order_date": o.order_date,
                        "estimated_delivery": o.estimated_delivery,
                    }
                    for o in orders
                ],
            },
        }
    except Exception as e:
        logger.error(f"get_customer_orders error: {e}")
        return {"success": False, "error": str(e), "data": None}
    finally:
        db.close()


def get_available_resolution_options(order_id: str) -> dict:
    """
    Determine what resolution options are available for a given order
    based on its status, age, and amount.
    """
    db: Session = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {
                "success": False,
                "error": f"Order '{order_id}' not found.",
                "data": None,
            }

        options = []
        status = order.status

        if status == "in_transit":
            options = [
                "Provide tracking update",
                "Contact carrier for expedited delivery",
                "Offer $10 store credit for delay over 5 days",
                "Reship if delivery fails",
            ]
        elif status == "processing":
            options = [
                "Provide processing status update",
                "Expedite processing (supervisor approval required for same-day)",
                "Cancel order if not yet shipped",
            ]
        elif status == "delivered":
            options = [
                "Initiate return (within 30-day window)",
                "Process refund if item is defective",
                "Exchange for different item",
                "Issue goodwill credit for minor issues",
            ]
        elif status == "cancelled":
            options = [
                "Re-order the item",
                "Confirm refund status",
                "Explain cancellation policy",
            ]
        else:
            options = ["Escalate to supervisor for unusual order status"]

        # Check if premium customer (more options)
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if customer and customer.membership_tier == "premium":
            options.append("Premium priority processing available")

        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "order_status": status,
                "product_name": order.product_name,
                "amount": order.amount,
                "available_options": options,
            },
        }
    except Exception as e:
        logger.error(f"get_available_resolution_options error: {e}")
        return {"success": False, "error": str(e), "data": None}
    finally:
        db.close()
