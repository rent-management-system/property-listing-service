from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import httpx
from app.config import settings
from app.utils.retry import async_retry

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8004/api/v1/auth/login")

@async_retry()
async def get_user_data(token: str):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"{settings.USER_MANAGEMENT_URL}/auth/verify", headers=headers)
        response.raise_for_status() # Will raise an exception for 4xx/5xx responses
        return response.json()

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

async def get_current_owner(current_user: dict = Depends(get_current_user)):
    if current_user.get("role").lower() != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user is not an Owner"
        )
    return current_user
