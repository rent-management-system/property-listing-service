import httpx
import structlog
from app.config import settings
import json
import redis.asyncio as redis
from urllib.parse import urlparse

logger = structlog.get_logger(__name__)

# Parse REDIS_URL
redis_url = urlparse(settings.REDIS_URL)
redis_client = redis.Redis(
    host=redis_url.hostname, 
    port=redis_url.port, 
    db=0, # Default DB
    password=redis_url.password
)

GEBETA_GEOCODE_URL = "https://gebeta.app/api/v1/geocode"
CACHE_TTL = 3600 # 1 hour

async def get_geocoded_location(location_query: str):
    cache_key = f"geocode:{location_query}"
    
    # Try to get from cache
    cached_result = await redis_client.get(cache_key)
    if cached_result:
        logger.info("geocoding_cache_hit", location=location_query)
        return json.loads(cached_result)

    # If not in cache, call Gebeta Maps API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GEBETA_GEOCODE_URL,
                params={"query": location_query},
                timeout=5 # 5-second timeout
            )
            response.raise_for_status()
            data = response.json()

            if data and "lat" in data and "lon" in data:
                geocoded_data = {"lat": data["lat"], "lon": data["lon"]}
                await redis_client.setex(cache_key, CACHE_TTL, json.dumps(geocoded_data))
                logger.info("geocoding_success", location=location_query, lat=data["lat"], lon=data["lon"])
                return geocoded_data
            else:
                logger.warning("geocoding_no_results", location=location_query, response=data)
                return None
    except httpx.HTTPStatusError as e:
        logger.error("geocoding_http_error", location=location_query, status_code=e.response.status_code, detail=e.response.text)
        return None
    except httpx.RequestError as e:
        logger.error("geocoding_request_error", location=location_query, error=str(e))
        return None
    except Exception as e:
        logger.error("geocoding_unexpected_error", location=location_query, error=str(e))
        return None

async def geocode_location_with_fallback(location_query: str):
    geocoded_data = await get_geocoded_location(location_query)
    if geocoded_data:
        return geocoded_data
    
    # Fallback to Addis Ababa center
    fallback_lat = 9.03
    fallback_lon = 38.75
    logger.warning("geocoding_fallback", location=location_query, fallback_lat=fallback_lat, fallback_lon=fallback_lon)
    return {"lat": fallback_lat, "lon": fallback_lon}
