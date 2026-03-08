import logging
from fastapi import HTTPException, status
from app.database import get_supabase
from app.trace.logger import logger # Using the pre-configured app logger

# Use the app's logger scope
u_logger = logging.getLogger("apipure.users")

USER_FIELDS = "id, email, full_name, avatar_url, role, created_at"


def get_user_profile(user_id: str) -> dict:
    """Get a user by ID, raising 404 if not found."""
    u_logger.info(f"Fetching profile for user_id: {user_id}")
    db = get_supabase()
    
    try:
        result = (
            db.table("users")
            .select(USER_FIELDS)
            .eq("id", user_id)
            .single()
            .execute()
        )
        
        if not result.data:
            u_logger.warning(f"User profile with id {user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
            
        u_logger.info(f"Successfully retrieved profile for user_id: {user_id}")
        return result.data

    except HTTPException:
        raise
    except Exception as e:
        u_logger.error(f"Error fetching user profile for id {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user profile"
        )


def update_user_profile(user_id: str, data: dict) -> dict:
    """Update a user's profile, raising 400 if no fields provided."""
    if not data:
        u_logger.warning(f"Update attempt for user_id {user_id} with no data provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update",
        )
        
    u_logger.info(f"Updating profile for user_id: {user_id} with data keys: {list(data.keys())}")
    db = get_supabase()
    
    try:
        result = (
            db.table("users")
            .update(data)
            .eq("id", user_id)
            .select(USER_FIELDS)
            .single()
            .execute()
        )
        
        u_logger.info(f"Successfully updated profile for user_id: {user_id}")
        return result.data
        
    except Exception as e:
        u_logger.error(f"Error updating user profile for id {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user profile"
        )
