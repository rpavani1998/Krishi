"""Circuit breaker pattern for service failure protection."""

import time
from typing import Callable, TypeVar, Any, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Import CloudWatch metrics if available
try:
    from .cloudwatch_metrics import CloudWatchMetrics
    CLOUDWATCH_AVAILABLE = True
except ImportError:
    CLOUDWATCH_AVAILABLE = False
    CloudWatchMetrics = None

T = TypeVar("T")


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is in OPEN state."""
    
    def __init__(self, service_name: str, timeout: int):
        self.service_name = service_name
        self.timeout = timeout
        super().__init__(
            f"Circuit breaker for {service_name} is OPEN. "
            f"Service will be retried after {timeout} seconds."
        )


class CircuitBreaker:
    """
    Circuit breaker to prevent repeated calls to failing services.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests fail fast
    - HALF_OPEN: Testing if service has recovered
    
    Transitions:
    - CLOSED -> OPEN: After failure_threshold consecutive failures
    - OPEN -> HALF_OPEN: After timeout seconds
    - HALF_OPEN -> CLOSED: If test request succeeds
    - HALF_OPEN -> OPEN: If test request fails
    
    Args:
        failure_threshold: Number of consecutive failures before opening (default: 5)
        timeout: Seconds to wait before testing recovery (default: 60)
        name: Name of the service for logging (default: "unknown")
    
    Example:
        breaker = CircuitBreaker(failure_threshold=5, timeout=60, name="ceda")
        
        async def fetch_data():
            return await breaker.call(external_api_call, url, params)
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        name: str = "unknown",
        metrics_client: Optional[Any] = None,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        # Initialize CloudWatch metrics client if available
        self.metrics_client = metrics_client
        if self.metrics_client is None and CLOUDWATCH_AVAILABLE:
            try:
                self.metrics_client = CloudWatchMetrics()
            except Exception as e:
                logger.debug(f"CloudWatch metrics not available: {e}")
        
        logger.info(
            f"Circuit breaker initialized for {name}",
            extra={
                "service": name,
                "failure_threshold": failure_threshold,
                "timeout": timeout,
            }
        )
    
    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        
        Returns:
            The result of the function call
        
        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
            Exception: Any exception raised by the function
        """
        # Check if we should transition from OPEN to HALF_OPEN
        if self.state == "OPEN":
            if self.last_failure_time and time.time() - self.last_failure_time > self.timeout:
                logger.info(
                    f"Circuit breaker for {self.name} transitioning to HALF_OPEN",
                    extra={"service": self.name, "state": "HALF_OPEN"}
                )
                self.state = "HALF_OPEN"
                
                # Emit metric for state change
                if self.metrics_client:
                    self.metrics_client.log_circuit_breaker_state(
                        self.name, "half_open", self.failure_count
                    )
            else:
                # Still in OPEN state, fail fast
                raise CircuitBreakerOpenError(self.name, self.timeout)
        
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Success - reset failure count and close circuit if needed
            if self.state == "HALF_OPEN":
                logger.info(
                    f"Circuit breaker for {self.name} transitioning to CLOSED",
                    extra={"service": self.name, "state": "CLOSED"}
                )
                self.state = "CLOSED"
                self.failure_count = 0
                
                # Emit metric for state change
                if self.metrics_client:
                    self.metrics_client.log_circuit_breaker_state(
                        self.name, "closed", 0
                    )
            
            return result
            
        except Exception as e:
            # Failure - increment count and potentially open circuit
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            logger.warning(
                f"Circuit breaker for {self.name} recorded failure",
                extra={
                    "service": self.name,
                    "failure_count": self.failure_count,
                    "error": str(e),
                }
            )
            
            if self.failure_count >= self.failure_threshold:
                logger.error(
                    f"Circuit breaker for {self.name} transitioning to OPEN",
                    extra={
                        "service": self.name,
                        "state": "OPEN",
                        "failure_count": self.failure_count,
                    }
                )
                self.state = "OPEN"
                
                # Emit metric for state change
                if self.metrics_client:
                    self.metrics_client.log_circuit_breaker_state(
                        self.name, "open", self.failure_count
                    )
            
            raise
    
    def reset(self):
        """Manually reset the circuit breaker to CLOSED state."""
        logger.info(
            f"Circuit breaker for {self.name} manually reset",
            extra={"service": self.name}
        )
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
