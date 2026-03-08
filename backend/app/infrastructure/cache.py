"""Cache service with TTL support (in-memory for prototype)."""

import time
from typing import Any, Optional, Dict, Tuple
import logging
from diskcache import Cache

logger = logging.getLogger(__name__)


class CacheService:
    """
    File-based cache service with TTL (Time To Live) support using DiskCache.
    
    Cache keys follow patterns:
    - price:{crop}:{location}:{date} - TTL: 6 hours
    - weather:{lat}:{lon}:{date} - TTL: 3 hours
    - decision:{hash} - TTL: 1 hour
    - mappings:ceda - TTL: 24 hours
    
    Args:
        ttl_seconds: Dictionary mapping cache key prefixes to TTL in seconds
    
    Example:
        cache = CacheService(ttl_seconds={
            "price": 6 * 3600,
            "weather": 3 * 3600,
            "decision": 3600,
            "mappings": 24 * 3600,
        })
        
        # Set value
        await cache.set("price:tomato:madanapalle:2024-01-15", price_data)
        
        # Get value (returns None if expired or not found)
        data = await cache.get("price:tomato:madanapalle:2024-01-15")
    """
    
    def __init__(self, ttl_seconds: Dict[str, int], cache_dir: str = "cache"):
        """
        Initialize cache service with TTL configuration.
        
        Args:
            ttl_seconds: Dictionary mapping cache key prefixes to TTL in seconds
            cache_dir: Directory to store cache files
        """
        self.cache = Cache(cache_dir)
        self.ttl = ttl_seconds
        self._default_ttl = 3600  # 1 hour default
        
        logger.info(
            "Cache service initialized",
            extra={"ttl_config": ttl_seconds, "cache_dir": cache_dir}
        )
    
    def _get_ttl(self, key: str) -> int:
        """Get TTL for a cache key based on its prefix."""
        prefix = key.split(':')[0] if ':' in key else key
        return self.ttl.get(prefix, self._default_ttl)
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value if found and not expired, None otherwise
        """
        return self.cache.get(key)
    
    async def set(self, key: str, value: Any) -> None:
        """
        Set value in cache with current timestamp.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        ttl = self._get_ttl(key)
        self.cache.set(key, value, expire=ttl)
        
        logger.debug(
            f"Cache set: {key}",
            extra={"ttl_seconds": ttl}
        )
    
    async def invalidate(self, pattern: str) -> int:
        """
        Invalidate all cache keys matching a pattern.
        
        Args:
            pattern: Pattern to match (substring match)
        
        Returns:
            Number of keys invalidated
        """
        # DiskCache doesn't support pattern deletion directly.
        # We need to iterate and delete keys.
        count = 0
        for key in list(self.cache.iterkeys()):
            if pattern in key:
                del self.cache[key]
                count += 1
        
        logger.info(
            f"Cache invalidated: {pattern}",
            extra={"keys_deleted": count}
        )
        
        return count
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        count = len(self.cache)
        self.cache.clear()
        
        logger.info(
            "Cache cleared",
            extra={"keys_deleted": count}
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        # DiskCache manages its own stats, so we can't get expired keys directly.
        total_keys = len(self.cache)
        
        # Count keys by prefix
        keys_by_prefix: Dict[str, int] = {}
        for key in self.cache.iterkeys():
            prefix = key.split(':')[0] if ':' in key else 'other'
            keys_by_prefix[prefix] = keys_by_prefix.get(prefix, 0) + 1
        
        return {
            "total_keys": total_keys,
            "keys_by_prefix": keys_by_prefix,
        }
