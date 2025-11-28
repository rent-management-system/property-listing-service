import asyncio
import structlog # Changed from logging to structlog
from functools import wraps

logger = structlog.get_logger(__name__) # Get structlog logger

def async_retry(attempts=5, backoff_factor=0.5): # Increased attempts to 5
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(
                        f"Attempt {attempt} failed for {func.__name__}",
                        attempt=attempt,
                        function=func.__name__,
                        error_message=str(e),
                        error_type=type(e).__name__,
                        exc_info=True if attempt == attempts else False # Log traceback only on final attempt
                    )
                    if attempt == attempts:
                        raise
                    await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))
        return wrapper
    return decorator
