import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def async_retry(attempts=3, backoff_factor=0.5):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(
                        f"Attempt {attempt} failed for {func.__name__}: {e}"
                    )
                    if attempt == attempts:
                        raise
                    await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))
        return wrapper
    return decorator
