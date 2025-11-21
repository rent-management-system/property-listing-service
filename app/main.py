from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from app.core.logging import configure_logging
from app.routers import properties, payments
from app.config import settings
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.property_cleanup import cleanup_stale_pending_properties
from app.routers import properties

app.include_router(
    properties.router, 
    prefix="/api/v1/properties", 
    tags=["Properties"]
)

# Configure logging
configure_logging()
logger = structlog.get_logger(__name__)

# --- Create FastAPI app first ---
app = FastAPI(title="Property Listing Microservice")

# CORS Middleware
origins = ["*"]  # or parse from settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include routers after app is created ---
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

# --- Scheduler setup ---
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup():
    # Initialize Redis for FastAPILimiter
    redis_connection = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_connection)

    # Schedule background tasks
    scheduler.add_job(cleanup_stale_pending_properties, "interval", days=1)
    scheduler.start()
    logger.info("Scheduler started")

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
    logger.info("Scheduler shut down")

# --- Request logging middleware ---
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

# --- Health check ---
@app.get("/health")
def health_check():
    return {"status": "ok"}
