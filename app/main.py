from fastapi import Depends, FastAPI, Request, APIRouter
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
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.dependencies.database import get_db
from app.models.property import Property, PropertyStatus, PaymentStatus
from app.schemas.property import MetricsResponse, PropertyListResponse
from decimal import Decimal
from typing import List

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

# Create a separate router for public endpoints
public_router = APIRouter()

# Public endpoint for reserved properties
@public_router.get("/properties/reserved", response_model=PropertyListResponse, include_in_schema=True)
async def get_reserved_properties(
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves all reserved properties with total count.
    This endpoint is publicly accessible.
    """
    # Get total count of reserved properties
    total = await db.scalar(
        select(func.count(Property.id))
        .where(Property.status == PropertyStatus.RESERVED)
    )
    
    # Get all reserved properties
    result = await db.execute(
        select(Property)
        .where(Property.status == PropertyStatus.RESERVED)
        .order_by(Property.created_at.desc())
    )
    items = result.scalars().all()
    
    return {
        "total": total or 0,
        "items": items
    }

# Include the public router first (no prefix to avoid /api/v1/api/v1)
app.include_router(public_router, prefix="/api/v1", tags=["Public"])

# Include the main properties router with authentication
app.include_router(
    properties.router, 
    prefix="/api/v1/properties", 
    tags=["Properties"]
)

app.include_router(
    payments.router,
    prefix="/api/v1",
    tags=["Payments"]
)

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/v1/metrics", response_model=MetricsResponse)
async def service_metrics(db: AsyncSession = Depends(get_db)):
    """Top-level service metrics for listing counts."""
    total_listings = await db.scalar(select(func.count(Property.id)))
    pending = await db.scalar(select(func.count(Property.id)).where(Property.status == PropertyStatus.PENDING))
    approved = await db.scalar(select(func.count(Property.id)).where(Property.status == PropertyStatus.APPROVED))
    rejected = await db.scalar(select(func.count(Property.id)).where(Property.status == PropertyStatus.REJECTED))
    total_revenue = await db.scalar(
        select(func.coalesce(func.sum(Property.price), 0)).where(
            Property.payment_status.in_([PaymentStatus.SUCCESS, PaymentStatus.PAID])
        )
    )
    return MetricsResponse(
        total_listings=total_listings or 0,
        pending=pending or 0,
        approved=approved or 0,
        rejected=rejected or 0,
        total_revenue=total_revenue if total_revenue is not None else Decimal("0")
    )
