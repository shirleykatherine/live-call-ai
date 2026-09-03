"""
Support ticket tool — creates support tickets in the database.
"""
import logging
import uuid
from datetime import datetime
from app.database import SessionLocal
from app.models.customer import SupportTicket

logger = logging.getLogger(__name__)


def create_support_ticket(
    customer_id: str,
    issue_type: str,
    description: str,
    order_id: str = None,
    priority: str = "medium",
    call_id: str = None,
) -> dict:
    """
    Create a support ticket for a customer issue.

    Args:
        customer_id: Customer identifier
        issue_type: Type of issue (late_delivery, refund, defective_product, etc.)
        description: Detailed description of the issue
        order_id: Related order ID (optional)
        priority: low | medium | high | urgent
        call_id: ID of the current call (optional)
    """
    db = SessionLocal()
    try:
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        ticket = SupportTicket(
            id=ticket_id,
            customer_id=customer_id if customer_id else None,
            call_id=call_id,
            order_id=order_id,
            issue_type=issue_type,
            description=description,
            priority=priority,
            status="open",
            created_at=datetime.utcnow().isoformat(),
        )
        db.add(ticket)
        db.commit()

        logger.info(f"Support ticket created: {ticket_id}")
        return {
            "success": True,
            "data": {
                "ticket_id": ticket_id,
                "status": "open",
                "priority": priority,
                "issue_type": issue_type,
                "created_at": ticket.created_at,
                "message": f"Support ticket {ticket_id} created successfully. The team will follow up within 24 hours.",
            },
        }
    except Exception as e:
        logger.error(f"create_support_ticket error: {e}")
        return {"success": False, "error": str(e), "data": None}
    finally:
        db.close()
