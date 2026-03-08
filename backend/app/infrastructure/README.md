# Infrastructure Components

This directory contains reliability and observability infrastructure components for the Krishi backend.

## Components

### 1. Retry Decorator (`retry.py`)

Provides automatic retry logic with exponential backoff for external API calls.

**Usage:**

```python
from app.infrastructure import retry_with_backoff
import httpx

@retry_with_backoff(max_attempts=3, base_delay=1.0, max_delay=10.0)
async def fetch_market_prices(crop: str, location: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/prices?crop={crop}")
        response.raise_for_status()
        return response.json()
```

**Retry Behavior:**
- Retries on: Connection errors, timeouts, 5xx status codes, 429 rate limit
- Does not retry on: 4xx client errors (except 429)
- Exponential backoff: delay = base_delay * (2 ** attempt)

### 2. Circuit Breaker (`circuit_breaker.py`)

Prevents repeated calls to failing services and provides fast failures.

**Pre-configured Instances (`circuit_breakers.py`):**

The application provides pre-configured circuit breaker instances for each external service:

```python
from app.infrastructure import (
    ceda_circuit_breaker,
    weather_circuit_breaker,
    news_circuit_breaker,
    ai_circuit_breaker,
)

# All instances are configured with:
# - failure_threshold: 5 consecutive failures
# - timeout: 60 seconds before attempting recovery
# - Separate state for each service

async def get_prices_with_circuit_breaker(crop: str):
    try:
        return await ceda_circuit_breaker.call(fetch_market_prices, crop)
    except CircuitBreakerOpenError:
        # Circuit is open, return fallback data
        return get_fallback_prices(crop)
```

**Custom Circuit Breaker:**

You can also create custom circuit breaker instances:

```python
from app.infrastructure import CircuitBreaker, CircuitBreakerOpenError

# Create a circuit breaker for a new service
custom_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60,
    name="custom_service"
)
```

**States:**
- CLOSED: Normal operation
- OPEN: Service is failing, requests fail fast
- HALF_OPEN: Testing if service has recovered

**Available Instances:**
- `ceda_circuit_breaker` - For CEDA market price API
- `weather_circuit_breaker` - For OpenMeteo weather API
- `news_circuit_breaker` - For RSS news feeds
- `ai_circuit_breaker` - For AI services (AWS Bedrock or Local)

### 3. Cache Service (`cache.py`)

In-memory cache with TTL support for reducing external API calls.

**Usage:**

```python
from app.infrastructure import CacheService

# Initialize cache with TTL configuration
cache = CacheService(ttl_seconds={
    "price": 6 * 3600,      # 6 hours
    "weather": 3 * 3600,    # 3 hours
    "decision": 3600,       # 1 hour
    "mappings": 24 * 3600,  # 24 hours
})

# Set value
await cache.set("price:tomato:madanapalle:2024-01-15", price_data)

# Get value (returns None if expired or not found)
data = await cache.get("price:tomato:madanapalle:2024-01-15")

# Invalidate by pattern
await cache.invalidate("price:tomato")

# Get statistics
stats = cache.get_stats()
```

**Cache Key Patterns:**
- `price:{crop}:{location}:{date}` - Price data
- `weather:{lat}:{lon}:{date}` - Weather forecasts
- `decision:{hash}` - Decision scenarios
- `mappings:ceda` - CEDA commodity/geography mappings

### 4. Structured Logging (`logging.py`)

Structured logging with consistent format for debugging and monitoring.

**Usage:**

```python
from app.infrastructure import setup_logging, get_logger

# In main.py - set up logging once
setup_logging(log_level="INFO", json_logs=False)

# In any module - get a logger
logger = get_logger(__name__)

# Log with structured data
logger.info(
    "api_call_started",
    service="ceda",
    endpoint="/prices",
    crop="tomato",
    location="madanapalle"
)

logger.error(
    "api_call_failed",
    service="ceda",
    error="timeout",
    retry_attempt=2,
    duration_ms=5000
)
```

**Log Format:**
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "event": "api_call_started",
  "service": "ceda",
  "endpoint": "/prices",
  "crop": "tomato",
  "location": "madanapalle"
}
```

## Validation Models

Pydantic models for validating external API responses are in `app/models/validation.py`.

**Usage:**

```python
from app.models.validation import CEDAPriceResponse, WeatherResponse
from pydantic import ValidationError

try:
    # Validate API response
    price_response = CEDAPriceResponse(**api_data)
    
    # Use validated data
    print(f"Current price: {price_response.current_price}")
    print(f"Data source: {price_response.data_source}")
    
except ValidationError as e:
    logger.error("validation_failed", error=str(e))
    # Return fallback data
    return get_fallback_data()
```

## Complete Example

Here's how to use all components together:

```python
from app.infrastructure import (
    retry_with_backoff,
    ceda_circuit_breaker,
    CircuitBreakerOpenError,
    CacheService,
    get_logger,
)
from app.models.validation import CEDAPriceResponse
import httpx

logger = get_logger(__name__)

# Initialize cache
cache = CacheService(ttl_seconds={"price": 6 * 3600})

@retry_with_backoff(max_attempts=3, base_delay=1.0)
async def _fetch_prices_from_api(crop: str, location: str):
    """Internal function with retry logic."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"https://api.ceda.com/prices",
            params={"crop": crop, "location": location}
        )
        response.raise_for_status()
        return response.json()

async def get_market_prices(crop: str, location: str):
    """Public function with full error handling."""
    cache_key = f"price:{crop}:{location}"
    
    # Check cache first
    cached_data = await cache.get(cache_key)
    if cached_data:
        logger.info("cache_hit", key=cache_key)
        return cached_data
    
    try:
        # Try to fetch from API through circuit breaker
        data = await ceda_circuit_breaker.call(_fetch_prices_from_api, crop, location)
        
        # Validate response
        validated = CEDAPriceResponse(**data)
        
        # Cache the result
        await cache.set(cache_key, validated.dict())
        
        logger.info("api_success", crop=crop, location=location)
        return validated.dict()
        
    except CircuitBreakerOpenError:
        logger.warning("circuit_breaker_open", service="ceda")
        return get_fallback_prices(crop, location)
        
    except Exception as e:
        logger.error("api_error", error=str(e), crop=crop, location=location)
        return get_fallback_prices(crop, location)
```

## Testing

Run tests with:

```bash
# Run all infrastructure tests
pytest tests/unit/test_infrastructure.py -v

# Run validation tests
pytest tests/unit/test_validation.py -v

# Run with coverage
pytest tests/unit/ --cov=app/infrastructure --cov=app/models/validation
```

## Migration Notes

For production deployment:

1. **Cache**: Migrate from in-memory to Redis for:
   - Persistence across restarts
   - Distributed caching
   - Better memory management

2. **Logging**: Configure log aggregation (ELK stack or CloudWatch)

3. **Monitoring**: Add metrics collection for:
   - Circuit breaker state changes
   - Cache hit/miss rates
   - Retry attempt counts
   - API response times
