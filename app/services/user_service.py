import httpx
from app.config import settings
from app.utils.retry import async_retry
import structlog

logger = structlog.get_logger(__name__)

@async_retry()
async def get_user_by_id(user_id: str, access_token: str = None):
    """
    Fetches user details from the User Management Service by user_id.
    
    Args:
        user_id: The UUID of the user to fetch
        access_token: Optional access token for authentication
        
    Returns:
        dict: User data including contact information
    """
    async with httpx.AsyncClient() as client:
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
            
        try:
            response = await client.get(
                f"{settings.USER_MANAGEMENT_URL}/users/{user_id}",
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to fetch user data",
                user_id=user_id,
                status_code=e.response.status_code,
                error=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "Unexpected error fetching user data",
                user_id=user_id,
                error=str(e)
            )
            raise
