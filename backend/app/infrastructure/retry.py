"""Retry decorator with exponential backoff using tenacity library."""

from functools import wraps
from typing import Callable, TypeVar, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception,
    before_sleep_log,
    after_log,
)
import httpx
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that retries a function with exponential backoff.
    
    Retries on:
    - Connection errors
    - Timeouts
    - 5xx status codes
    - 429 rate limit errors
    
    Does not retry on:
    - 4xx client errors (except 429)
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds for exponential backoff (default: 1.0)
        max_delay: Maximum delay in seconds between retries (default: 10.0)
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @retry_with_backoff(max_attempts=3, base_delay=1.0, max_delay=10.0)
        async def fetch_data(url: str) -> dict:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
    """
    
    def should_retry(exception: Exception) -> bool:
        """Determine if the exception should trigger a retry."""
        # Always retry connection errors and timeouts
        if isinstance(exception, (httpx.ConnectError, httpx.TimeoutException)):
            return True
        
        # Retry on HTTP status errors for 5xx and 429
        if isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            # Retry on 5xx server errors and 429 rate limit
            if status_code >= 500 or status_code == 429:
                return True
        
        return False
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Apply tenacity retry decorator
        retry_decorator = retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=base_delay,
                max=max_delay,
            ),
            retry=retry_if_exception_type(Exception) & retry_if_exception(should_retry),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.DEBUG),
            reraise=True,
        )
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_decorator(func)(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            return retry_decorator(func)(*args, **kwargs)
        
        # Return appropriate wrapper based on whether function is async
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
