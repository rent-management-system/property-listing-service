from fastapi import Security, HTTPException, status, Request # Added Request
from fastapi.security.api_key import APIKeyHeader
from app.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(API_KEY_HEADER), request: Request = None): # Added request
    """
    Dependency to validate the X-API-Key header for server-to-server communication.
    Includes a placeholder for IP whitelisting.
    """
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="X-API-Key header missing",
        )
    
    # Placeholder for IP whitelisting
    # In a real scenario, you would fetch allowed IPs from settings
    # and check request.client.host against that list.
    # For example:
    # ALLOWED_IPS = ["127.0.0.1", "192.168.1.100"] # From settings
    # if request and request.client and request.client.host not in ALLOWED_IPS:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Unauthorized IP address",
    #     )

    # Validate the API key itself
    if api_key_header == settings.PAYMENT_SERVICE_API_KEY or \
       api_key_header == settings.PROPERTY_WEBHOOK_API_KEY: # Allow both payment service and property webhook keys
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )

