# News Service Documentation

## Overview

The News Service provides agricultural news and market intelligence with built-in reliability features including retry logic, circuit breaker protection, and caching.

## Features

- **Retry Logic**: Automatic retry with exponential backoff (3 attempts)
- **Circuit Breaker**: Protection against cascading failures
- **Caching**: 1-hour TTL for news articles
- **Fallback**: Returns empty list with indicator on failure
- **Validation**: Pydantic models ensure data integrity
- **Multi-language**: Supports English (en), Telugu (te), and Hindi (hi)
- **Filtering**: Filter by crop type, region, and language

## Usage

### Basic Usage

```python
from app.services.news_service import news_service

# Get general agricultural news
result = await news_service.get_news(language="en", limit=10)

# Get news filtered by crop
result = await news_service.get_news(
    crop="Tomato",
    language="en",
    limit=5
)

# Get news filtered by region
result = await news_service.get_news(
    region="Andhra Pradesh",
    language="te",
    limit=5
)

# Get news with all filters
result = await news_service.get_news(
    crop="Onion",
    region="Telangana",
    language="hi",
    limit=10
)
```

### Response Format

```python
{
    "articles": [
        {
            "title": "Article title",
            "summary": "Article summary",
            "date": "2024-01-15T10:30:00",
            "source": "News Source",
            "url": "https://example.com/article",
            "image_url": "https://example.com/image.jpg"
        }
    ],
    "total": 3,
    "filters": {
        "crop": "Tomato",
        "region": "Andhra Pradesh",
        "language": "en"
    },
    "data_source": "live",  # or "cached" or "fallback"
    "data_timestamp": "2024-01-15T10:30:00"
}
```

### Data Sources

- **live**: Fresh data from external API
- **cached**: Data retrieved from cache (< 1 hour old)
- **fallback**: Empty list returned due to service failure

## Integration with Decision Service

The News service can be integrated into the decision-making process to provide market intelligence:

```python
from app.services.news_service import news_service
from app.services.decision_service import decision_service

async def get_harvest_decision_with_news(harvest_input):
    # Get decision scenarios
    decision = await decision_service.analyze_harvest(harvest_input)
    
    # Get relevant news
    news = await news_service.get_news(
        crop=harvest_input.crop,
        region=harvest_input.location,
        language=harvest_input.language,
        limit=5
    )
    
    # Combine decision with news
    return {
        "decision": decision,
        "market_news": news
    }
```

## Configuration

### Cache TTL

The cache TTL is configured in the NewsService constructor:

```python
self.cache = CacheService(ttl_seconds={
    "news": 3600,  # 1 hour
})
```

### Circuit Breaker

The circuit breaker is configured in `app/infrastructure/circuit_breakers.py`:

```python
news_circuit_breaker = CircuitBreaker(
    failure_threshold=5,  # Open after 5 failures
    timeout=60,           # Try recovery after 60 seconds
    name="news"
)
```

### Retry Logic

Retry logic is configured via the `@retry_with_backoff` decorator:

```python
@retry_with_backoff(
    max_attempts=3,      # Maximum 3 attempts
    base_delay=1.0,      # Start with 1 second delay
    max_delay=10.0       # Maximum 10 seconds between retries
)
```

## Testing

### Unit Tests

Run unit tests:

```bash
pytest tests/unit/test_news_service.py -v
```

### Integration Test

Run integration test:

```bash
python test_news_integration.py
```

## Production Deployment

### API Integration

For production, replace the mock data implementation with actual API integration:

1. Update `BASE_URL` in `NewsService` class
2. Implement proper API authentication
3. Remove or modify `_get_mock_news_data` method
4. Configure API keys in environment variables

### Recommended News APIs

- **NewsAPI**: https://newsapi.org/
- **Google News API**: https://newsapi.org/s/google-news-api
- **Agricultural News Sources**: Government agricultural portals, farming news websites

### Environment Variables

```bash
NEWS_API_URL=https://api.newsapi.org/v2/everything
NEWS_API_KEY=your_api_key_here
```

## Monitoring

The service logs all operations with structured logging:

```python
logger.info("News data retrieved from cache", extra={
    "crop": crop,
    "region": region,
    "language": language,
    "cache_key": cache_key
})

logger.error("News service failed after retries", extra={
    "crop": crop,
    "circuit_state": news_circuit_breaker.state
})
```

## Error Handling

The service handles errors gracefully:

1. **Connection Errors**: Automatic retry with exponential backoff
2. **Timeouts**: Retry up to 3 times, then return fallback
3. **Circuit Breaker Open**: Fast fail and return fallback
4. **Validation Errors**: Log error and return fallback

All errors are logged with full context for debugging.

## Cache Management

### Get Cache Statistics

```python
stats = news_service.cache.get_stats()
print(f"Total keys: {stats['total_keys']}")
print(f"Active keys: {stats['active_keys']}")
```

### Invalidate Cache

```python
# Invalidate all news cache entries
await news_service.cache.invalidate("news:")

# Clear entire cache
await news_service.cache.clear()
```

## Future Enhancements

1. **Sentiment Analysis**: Analyze news sentiment for market trends
2. **Personalization**: Recommend news based on user preferences
3. **Real-time Updates**: WebSocket support for live news updates
4. **Image Processing**: Extract insights from news images
5. **Multi-source Aggregation**: Combine news from multiple sources
