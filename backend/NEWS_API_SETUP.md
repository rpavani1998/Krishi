# News API Configuration Guide

## Overview

The News Service can work in two modes:
1. **Mock Mode** (default): Uses sample data for prototype testing
2. **Live Mode**: Fetches real news from NewsAPI.org

## Quick Start (Mock Mode)

By default, the service uses mock data. No configuration needed!

```python
from app.services.news_service import news_service

# This will use mock data
result = await news_service.get_news(crop="Tomato", language="en")
```

## Setup for Live News API

### Step 1: Get a NewsAPI Key

1. Go to [NewsAPI.org](https://newsapi.org/)
2. Click "Get API Key" (free tier available)
3. Sign up for a free account
4. Copy your API key

**Free Tier Limits:**
- 100 requests per day
- News up to 1 month old
- Perfect for development/testing

### Step 2: Configure Environment Variables

Add these to your `backend/.env` file:

```bash
# News Service Configuration
NEWS_API_URL="https://newsapi.org/v2/everything"
NEWS_API_KEY="your_api_key_here"
NEWS_API_ENABLED=True
```

**Example:**
```bash
NEWS_API_URL="https://newsapi.org/v2/everything"
NEWS_API_KEY="abc123def456ghi789"
NEWS_API_ENABLED=True
```

### Step 3: Restart the Backend

```bash
# Stop the backend if running
# Then start it again
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python -m uvicorn app.main:app --reload
```

### Step 4: Test the Integration

```bash
cd backend
python test_news_integration.py
```

You should see real news articles instead of mock data!

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NEWS_API_URL` | NewsAPI endpoint | `https://newsapi.org/v2/everything` | No |
| `NEWS_API_KEY` | Your NewsAPI key | `None` | Yes (for live mode) |
| `NEWS_API_ENABLED` | Enable live API calls | `False` | No |

### Behavior

- **When `NEWS_API_ENABLED=False`**: Always uses mock data
- **When `NEWS_API_ENABLED=True` but no API key**: Falls back to mock data
- **When `NEWS_API_ENABLED=True` with API key**: Fetches real news
- **When API fails**: Falls back to mock data (graceful degradation)

## Alternative News APIs

If you prefer a different news source, you can modify the service:

### Option 1: Google News RSS

Free, no API key needed, but limited filtering:

```python
# In news_service.py
self.api_url = "https://news.google.com/rss/search"
# Modify _fetch_news_with_retry to parse RSS instead of JSON
```

### Option 2: Agricultural News Sources

Use specialized agricultural news APIs:

- **USDA News**: https://www.usda.gov/media/news-releases
- **FAO News**: http://www.fao.org/news/
- **Agricultural News Network**: Various regional sources

### Option 3: Custom RSS Aggregator

Aggregate multiple RSS feeds:

```python
feeds = [
    "https://www.agriculture.com/rss",
    "https://www.farmersweekly.co.za/feed/",
    # Add more feeds
]
```

## Monitoring

### Check if API is Working

```python
from app.services.news_service import news_service

result = await news_service.get_news(crop="Tomato")
print(f"Data source: {result['data_source']}")
# Should print "live" if API is working
# Will print "cached" if using cached data
# Will print "fallback" if completely failed
```

### View Logs

The service logs all API calls:

```bash
# Check logs for API status
tail -f backend/logs/app.log | grep "News"
```

## Troubleshooting

### Issue: Still seeing mock data after configuration

**Check:**
1. Is `NEWS_API_ENABLED=True` in your `.env`?
2. Is your API key correct?
3. Did you restart the backend?
4. Check logs for error messages

**Solution:**
```bash
# Verify environment variables are loaded
cd backend
python -c "from app.core.config import settings; print(f'API Enabled: {settings.NEWS_API_ENABLED}, Has Key: {bool(settings.NEWS_API_KEY)}')"
```

### Issue: API rate limit exceeded

**Error:** `429 Too Many Requests`

**Solution:**
- Free tier: 100 requests/day
- Increase cache TTL to reduce API calls
- Upgrade to paid plan
- Use mock data for development

### Issue: No news for Telugu/Hindi

**Note:** NewsAPI primarily has English content. For regional languages:
- Use mock data (already includes Telugu/Hindi)
- Integrate with regional news sources
- Use translation APIs

## Production Recommendations

### 1. Use Paid API Plan

Free tier is limited. For production:
- NewsAPI Business: $449/month (unlimited requests)
- Or use multiple free APIs with rotation

### 2. Increase Cache TTL

Reduce API calls by caching longer:

```python
# In news_service.py
self.cache = CacheService(ttl_seconds={
    "news": 6 * 3600,  # 6 hours instead of 1
})
```

### 3. Add Request Throttling

Prevent rate limit issues:

```python
from app.infrastructure.rate_limiter import RateLimiter

rate_limiter = RateLimiter(max_requests=90, window_seconds=86400)
```

### 4. Monitor API Usage

Track API calls to avoid surprises:

```python
logger.info("News API call", extra={
    "api_calls_today": api_call_counter,
    "remaining_quota": 100 - api_call_counter
})
```

## Cost Estimation

### NewsAPI Pricing

- **Free**: 100 requests/day = $0
- **Developer**: 250 requests/day = $49/month
- **Business**: Unlimited = $449/month

### Estimated Usage

With 1-hour cache TTL:
- 100 users/day × 2 news checks = 200 API calls
- With cache: ~50 actual API calls/day
- **Free tier is sufficient for MVP testing!**

## Support

For issues with:
- **NewsAPI**: https://newsapi.org/docs
- **This integration**: Check logs or contact dev team
- **Alternative APIs**: See documentation for specific provider
