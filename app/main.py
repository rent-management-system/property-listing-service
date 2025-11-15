from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware # Added import
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from app.core.logging import configure_logging
from app.routers import properties, payments
from app.config import settings
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler # Added import
from app.services.property_cleanup import cleanup_stale_pending_properties # Added import

configure_logging()
logger = structlog.get_logger(__name__)

app = FastAPI(title="Property Listing Microservice")

# CORS Middleware
# origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = AsyncIOScheduler() # Initialize scheduler

@app.on_event("startup")
async def startup():
    # Initialize Redis for FastAPILimiter
    redis_connection = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_connection)

    # Schedule background tasks
    scheduler.add_job(cleanup_stale_pending_properties, "interval", days=1) # Run daily
    scheduler.start()
    logger.info("Scheduler started")

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
    logger.info("Scheduler shut down")

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

app.include_router(
    payments.router,
    prefix="/api/v1",
    tags=["Payments"]
)

@app.get("/health")
def health_check():
    return {"status": "ok"}
