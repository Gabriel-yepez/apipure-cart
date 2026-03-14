from fastapi import HTTPException, status

from app.database import get_supabase
from app.trace.logger import logger

PM_FIELDS = "id, name, label, provider, is_active, created_at"


def list_payment_methods() -> list[dict]:
    """Return all active payment methods (public catalog)."""
    db = get_supabase()
    try:
        result = (
            db.table("payment_methods")
            .select(PM_FIELDS)
            .eq("is_active", True)
            .order("label")
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.error("Error fetching payment methods", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve payment methods",
        ) from e


def get_payment_method(method_id: str) -> dict:
    """Get a single payment method by ID."""
    db = get_supabase()
    try:
        result = (
            db.table("payment_methods")
            .select(PM_FIELDS)
            .eq("id", method_id)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found",
            )
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching payment method {method_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve payment method",
        ) from e
