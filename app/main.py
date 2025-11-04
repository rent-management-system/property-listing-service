from fastapi import Depends, FastAPI, Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from app.core.logging import configure_logging
from app.routers import properties
from app.config import settings
import structlog

configure_logging()
logger = structlog.get_logger(__name__)

app = FastAPI(title="Property Listing Microservice")

@app.on_event("startup")
async def startup():
    # In a real production environment, you would use a persistent Redis instance.
    # For this example, we use an in-memory store which is not suitable for production.
    redis_connection = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_connection)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        path=request.url.path,
        method=request.method,
        client_host=request.client.host,
    )
    response = await call_next(request)
    logger.info("Request completed", status_code=response.status_code)
    return response

app.include_router(
    properties.router, 
    prefix="/api/v1/properties", 
    tags=["Properties"],
    dependencies=[Depends(RateLimiter(times=10, minutes=1))]
)

@app.get("/health")
def health_check():
    return {"status": "ok"}
