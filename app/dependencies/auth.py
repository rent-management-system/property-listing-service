from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import httpx
from app.config import settings
from app.utils.retry import async_retry
import redis.asyncio as redis # Added import
import json # Added import
from urllib.parse import urlparse # Added import

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="https://rent-managment-system-user-magt.onrender.com/api/v1/auth/login")

# Initialize Redis client for caching
redis_url = urlparse(settings.REDIS_URL)
redis_client = redis.Redis(
    host=redis_url.hostname, 
    port=redis_url.port, 
    db=0, # Default DB
    password=redis_url.password
)
USER_CACHE_TTL = 300 # 5 minutes

@async_retry()
async def get_user_data(token: str):
    cache_key = f"user_data:{token}"
    
    # Try to get from cache
    cached_user_data = await redis_client.get(cache_key)
    if cached_user_data:
        return json.loads(cached_user_data)

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"{settings.USER_MANAGEMENT_URL}/auth/verify", headers=headers)
        response.raise_for_status() # Will raise an exception for 4xx/5xx responses
        user_data = response.json()
        
        # Cache the user data
        await redis_client.setex(cache_key, USER_CACHE_TTL, json.dumps(user_data))
        return user_data

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_data = await get_user_data(token)
        return user_data
    except (JWTError, httpx.HTTPStatusError):
        raise credentials_exception

async def get_current_owner(current_user: dict = Depends(get_current_user), token: str = Depends(oauth2_scheme)):
    if current_user.get("role").lower() != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not an Owner"
        )
    return {"user": current_user, "token": token}
