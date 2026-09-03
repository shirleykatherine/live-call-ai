"""REST API routes for customer and order data (used for pre-loading dashboard)."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer, Order

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["customers"])


@router.get("/customers/{customer_id}")
def get_customer_endpoint(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "account_status": customer.account_status,
        "membership_tier": customer.membership_tier,
        "join_date": customer.join_date,
        "total_orders": customer.total_orders,
    }


@router.get("/customers")
def list_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    return [
        {"id": c.id, "name": c.name, "email": c.email, "membership_tier": c.membership_tier}
        for c in customers
    ]


@router.get("/orders/{order_id}")
def get_order_endpoint(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "product_name": order.product_name,
        "status": order.status,
        "amount": order.amount,
        "order_date": order.order_date,
        "estimated_delivery": order.estimated_delivery,
        "tracking_number": order.tracking_number,
        "carrier": order.carrier,
        "shipping_address": order.shipping_address,
    }


@router.get("/stt/info")
def get_stt_info():
    from app.services.stt_service import get_stt_service
    return get_stt_service().get_provider_info()
