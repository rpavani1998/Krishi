"""News service for fetching agricultural news and market intelligence."""

from typing import Dict, Any, List, Optional
import httpx
import logging
from datetime import datetime
from pydantic import ValidationError

from app.infrastructure.retry import retry_with_backoff
from app.infrastructure.circuit_breakers import news_circuit_breaker
from app.infrastructure.cache import CacheService
from app.models.validation import NewsResponse, NewsArticle
from app.core.config import settings

logger = logging.getLogger(__name__)


class NewsService:
    """
    Service for fetching agricultural news and market intelligence.
    
    Supports filtering by:
    - Crop type
    - Region/location
    - Language (en, te, hi)
    
    Features:
    - Retry logic with exponential backoff
    - Circuit breaker protection
    - Caching with 1-hour TTL
    - Fallback to empty list on failure
    """
    
    def __init__(self):
        """Initialize news service with cache and config."""
        # Initialize cache with 1-hour TTL for news data
        self.cache = CacheService(ttl_seconds={
            "news": 3600,  # 1 hour
        })
        
        # Load configuration
        self.api_url = settings.NEWS_API_URL
        self.api_key = settings.NEWS_API_KEY
        self.api_enabled = settings.NEWS_API_ENABLED
        
        # Region to Coordinates mapping for proximity search
        # APITube's location.name often fails for specific states, so we use geo-coordinates
        self.region_coordinates = {
            "andhra pradesh": {"lat": 15.9129, "lng": 79.7400, "radius": 400},
            "telangana": {"lat": 18.1124, "lng": 79.0193, "radius": 300},
            "telengana": {"lat": 18.1124, "lng": 79.0193, "radius": 300},
            "ap": {"lat": 15.9129, "lng": 79.7400, "radius": 400},
            "andhra": {"lat": 15.9129, "lng": 79.7400, "radius": 400},
            "ts": {"lat": 18.1124, "lng": 79.0193, "radius": 300},
            "south india": {"lat": 16.5, "lng": 79.5, "radius": 500},
        }

    def _get_effective_language(self, language: str, region: Optional[str]) -> str:
        if not language or language == "auto":
            if region:
                region_key = region.lower().strip()
                if region_key in {"andhra pradesh", "telangana", "ap", "ts"}:
                    return "te"
            return "en"
        return language
    
    async def get_news(
        self,
        crop: Optional[str] = None,
        region: Optional[str] = None,
        language: str = "en",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get agricultural news articles with filtering.
        
        Args:
            crop: Filter by crop type (e.g., "Tomato", "Onion")
            region: Filter by region/state (e.g., "Andhra Pradesh")
            language: Language code (en, te, hi)
            limit: Maximum number of articles to return
        
        Returns:
            Dictionary with articles list, data_source, and data_timestamp
            Falls back to empty list with indicator on failure
        """
        language = self._get_effective_language(language, region)

        # Create cache key based on filters
        cache_key = f"news:{crop or 'all'}:{region or 'all'}:{language}"
        
        # Check cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(
                "News data retrieved from cache",
                extra={
                    "crop": crop,
                    "region": region,
                    "language": language,
                    "cache_key": cache_key
                }
            )
            # Update data_source to indicate cached data
            cached_data["data_source"] = "cached"
            return cached_data
        
        try:
            # Use circuit breaker to protect against cascading failures
            data = await news_circuit_breaker.call(
                self._fetch_news_with_retry,
                crop,
                region,
                language,
                limit
            )
            
            # Cache the successful response
            await self.cache.set(cache_key, data)
            
            return data
        except Exception as e:
            logger.error(
                f"News service failed after retries and circuit breaker: {e}",
                extra={
                    "crop": crop,
                    "region": region,
                    "language": language,
                    "circuit_state": news_circuit_breaker.state
                }
            )
            # Return fallback data
            return self._get_fallback_news()
    
    @retry_with_backoff(max_attempts=3, base_delay=1.0, max_delay=10.0)
    async def _fetch_news_with_retry(
        self,
        crop: Optional[str],
        region: Optional[str],
        language: str,
        limit: int
    ) -> Dict[str, Any]:
        """
        Fetch news data with automatic retry on failures.
        
        Retries on:
        - Connection errors
        - Timeouts
        - 5xx status codes
        """
        # If API is not enabled, use mock data
        if not self.api_enabled or not self.api_key:
            logger.info("News API not configured, using mock data")
            return self._get_mock_news_data(crop, region, language, limit)
        
        # Use APITube news API for agriculture news
        api_url = "https://api.apitube.io/v1/news/everything"
        
        # Build query parameters
        params = {
            "api_key": self.api_key,
            "topic.id": "industry.agriculture_news",
            "limit": limit,
            "sort_by": "published_at",
            "order": "desc"
        }
        
        # Add location filter (Proximity search for specific regions)
        if region:
            region_key = region.lower().strip()
            if region_key in self.region_coordinates:
                coords = self.region_coordinates[region_key]
                params["location.lat"] = coords["lat"]
                params["location.lng"] = coords["lng"]
                params["location.radius"] = coords["radius"]
            else:
                # Fallback to location name for other regions (e.g., "India")
                params["location.name"] = region

        # Add language filter if supported
        if language in ["en", "hi", "te"]:
            params["language"] = language
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Transform APITube data into our format
                return self._transform_apitube_data(data, crop, region, language)
            except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
                # For prototype, return mock data instead of failing
                logger.warning(
                    f"APITube News API not available ({e}), using mock data",
                    extra={"crop": crop, "region": region, "language": language}
                )
                return self._get_mock_news_data(crop, region, language, limit)
    
    def _map_language_code(self, language: str) -> str:
        """Map our language codes to NewsAPI language codes."""
        # APITube supports en, hi, te directly (or we try to use them)
        mapping = {
            "en": "en",
            "te": "te",
            "hi": "hi",
        }
        return mapping.get(language, "en")
    
    def _transform_apitube_data(
        self,
        data: Dict[str, Any],
        crop: Optional[str],
        region: Optional[str],
        language: str
    ) -> Dict[str, Any]:
        """
        Transform APITube API response into our format.
        
        APITube response structure:
        {
            "results": [  # Or "data"
                {
                    "title": "...",
                    "description": "...",
                    "published_at": "...",
                    "source": {"name": "..."},
                    "url": "...",
                    "image": "..."
                }
            ],
            "total": 100
        }
        """
        articles_data = data.get("results", []) or data.get("data", [])
        
        # Transform each article
        transformed_articles = []
        for article in articles_data:
            try:
                # Validate using Pydantic model
                news_article = NewsArticle(
                    title=article.get("title", ""),
                    summary=article.get("description", article.get("summary", "")),
                    date=article.get("published_at", article.get("date", datetime.now().isoformat())),
                    source=article.get("source", {}).get("name", "Unknown") if isinstance(article.get("source"), dict) else str(article.get("source", "Unknown")),
                    url=article.get("url"),
                    image_url=article.get("image")
                )
                transformed_articles.append(news_article.model_dump())
            except ValidationError as e:
                logger.warning(
                    f"Skipping invalid news article from APITube: {e}",
                    extra={"article": article}
                )
                continue
        
        response_data = {
            "articles": transformed_articles,
            "total": len(transformed_articles),
            "filters": {
                "crop": crop,
                "region": region,
                "language": language
            },
            "data_source": "live",
            "data_timestamp": datetime.now().isoformat()
        }
        
        logger.info(
            "APITube news data fetched successfully",
            extra={
                "article_count": len(transformed_articles),
                "crop": crop,
                "region": region
            }
        )
        
        return response_data
    
    def _transform_news_data(
        self,
        data: Dict[str, Any],
        crop: Optional[str],
        region: Optional[str],
        language: str
    ) -> Dict[str, Any]:
        """
        Transform external API response into our format.
        
        Includes data_source and data_timestamp for transparency.
        Validates response using Pydantic models.
        """
        articles = data.get("articles", [])
        
        # Transform each article
        transformed_articles = []
        for article in articles:
            try:
                # Validate using Pydantic model
                news_article = NewsArticle(
                    title=article.get("title", ""),
                    summary=article.get("summary", article.get("description", "")),
                    date=article.get("publishedAt", article.get("date", datetime.now().isoformat())),
                    source=article.get("source", {}).get("name", "Unknown"),
                    url=article.get("url"),
                    image_url=article.get("urlToImage")
                )
                transformed_articles.append(news_article.model_dump())
            except ValidationError as e:
                logger.warning(
                    f"Skipping invalid news article: {e}",
                    extra={"article": article}
                )
                continue
        
        response_data = {
            "articles": transformed_articles,
            "total": len(transformed_articles),
            "filters": {
                "crop": crop,
                "region": region,
                "language": language
            },
            "data_source": "live",
            "data_timestamp": datetime.now().isoformat()
        }
        
        # Validate complete response
        try:
            news_response = NewsResponse(
                articles=[NewsArticle(**a) for a in transformed_articles],
                total=len(transformed_articles),
                filters={"crop": crop, "region": region, "language": language},
                data_source="live",
                data_timestamp=datetime.now()
            )
            
            logger.info(
                "News data validated successfully",
                extra={
                    "article_count": len(transformed_articles),
                    "crop": crop,
                    "region": region
                }
            )
        except ValidationError as e:
            logger.error(
                f"News data validation failed: {e}",
                extra={
                    "validation_errors": e.errors(),
                    "data": response_data
                }
            )
            # Return fallback on validation failure
            return self._get_fallback_news()
        
        return response_data
    
    def _get_mock_news_data(
        self,
        crop: Optional[str],
        region: Optional[str],
        language: str,
        limit: int
    ) -> Dict[str, Any]:
        """
        Generate mock news data for prototype testing.
        
        In production, this should be removed and replaced with actual API integration.
        """
        lang_prefix = language.split('-')[0].lower() if language else "en"
        
        # Sample news articles relevant to agriculture
        mock_articles = []
        
        if lang_prefix == "te":
            mock_articles = [
                {
                    "title": f"{crop or 'పంటల'} మార్కెట్ ధరలు పెరుగుతున్నాయి",
                    "summary": "వ్యవసాయ వస్తువులకు మార్కెట్‌లో మంచి ధరలు లభిస్తున్నాయి. రైతులు ఈ అవకాశాన్ని సద్వినియోగం చేసుకోవాలి.",
                    "date": datetime.now().isoformat(),
                    "source": "వ్యవసాయ వార్తలు",
                    "url": "https://example.com/news/1",
                    "image_url": None
                },
                {
                    "title": f"{region or 'వ్యవసాయ ప్రాంతాలకు'} వాతావరణం అనుకూలంగా ఉంది",
                    "summary": "రాబోయే రోజుల్లో వర్షాలు పడే అవకాశం ఉంది. పంటలకు ఇది మేలు చేస్తుంది.",
                    "date": datetime.now().isoformat(),
                    "source": "వాతావరణ శాఖ",
                    "url": "https://example.com/news/2",
                    "image_url": None
                },
                {
                    "title": "రైతులకు కొత్త మద్దతు పథకాలు ప్రకటించింది ప్రభుత్వం",
                    "summary": "ప్రభుత్వం విత్తనాలు మరియు ఎరువులపై రాయితీలను పెంచింది. చిన్న సన్నకారు రైతులకు ఇది ఊరటనిస్తుంది.",
                    "date": datetime.now().isoformat(),
                    "source": "ప్రభుత్వ వ్యవసాయ శాఖ",
                    "url": "https://example.com/news/3",
                    "image_url": None
                }
            ]
        elif lang_prefix == "hi":
            mock_articles = [
                {
                    "title": f"{crop or 'फसलों'} के बाजार मूल्य में वृद्धि",
                    "summary": "कृषि जिंसों के लिए बाजार में अच्छी कीमतें मिल रही हैं। किसानों को इस अवसर का लाभ उठाना चाहिए।",
                    "date": datetime.now().isoformat(),
                    "source": "कृषि समाचार",
                    "url": "https://example.com/news/1",
                    "image_url": None
                },
                {
                    "title": f"{region or 'कृषि क्षेत्रों'} के लिए मौसम अनुकूल",
                    "summary": "आने वाले दिनों में बारिश की संभावना है। यह फसलों के लिए फायदेमंद होगा।",
                    "date": datetime.now().isoformat(),
                    "source": "मौसम विभाग",
                    "url": "https://example.com/news/2",
                    "image_url": None
                },
                {
                    "title": "सरकार ने किसानों के लिए नई सहायता योजनाओं की घोषणा की",
                    "summary": "सरकार ने बीज और उर्वरकों पर सब्सिडी बढ़ाई है। इससे छोटे और सीमांत किसानों को राहत मिलेगी।",
                    "date": datetime.now().isoformat(),
                    "source": "सरकारी कृषि विभाग",
                    "url": "https://example.com/news/3",
                    "image_url": None
                }
            ]
        else:
            mock_articles = [
                {
                    "title": f"Market prices for {crop or 'crops'} show upward trend",
                    "summary": "Recent market analysis shows positive trends for agricultural commodities. Farmers are advised to monitor daily rates.",
                    "date": datetime.now().isoformat(),
                    "source": "Agricultural News Network",
                    "url": "https://example.com/news/1",
                    "image_url": None
                },
                {
                    "title": f"Weather forecast favorable for {region or 'farming regions'}",
                    "summary": "Meteorological department predicts good conditions for farming activities with expected rainfall in the coming week.",
                    "date": datetime.now().isoformat(),
                    "source": "Farm Weather Report",
                    "url": "https://example.com/news/2",
                    "image_url": None
                },
                {
                    "title": "Government announces new support schemes for farmers",
                    "summary": "New agricultural policies aim to support farmers with better prices, subsidies on seeds, and improved insurance coverage.",
                    "date": datetime.now().isoformat(),
                    "source": "Government Agricultural Portal",
                    "url": "https://example.com/news/3",
                    "image_url": None
                }
            ]
        
        # Limit articles
        articles = mock_articles[:limit]
        
        # Validate articles - don't skip on validation errors for mock data
        validated_articles = []
        for article in articles:
            try:
                news_article = NewsArticle(**article)
                validated_articles.append(news_article.model_dump())
            except ValidationError as e:
                logger.error(f"Mock article validation failed: {e}, article: {article}")
                # For mock data, still include it even if validation fails
                validated_articles.append(article)
        
        result = {
            "articles": validated_articles,
            "total": len(validated_articles),
            "filters": {
                "crop": crop,
                "region": region,
                "language": language
            },
            "data_source": "mock",
            "data_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Returning mock news data with {len(validated_articles)} articles")
        return result
    
    def _get_fallback_news(self) -> Dict[str, Any]:
        """
        Return empty news list with indicator on failure.
        
        Includes data_source="fallback" and timestamp for transparency.
        """
        logger.warning("Returning fallback news data (empty list)")
        return {
            "articles": [],
            "total": 0,
            "filters": {},
            "data_source": "fallback",
            "data_timestamp": datetime.now().isoformat()
        }


# Singleton instance
news_service = NewsService()
