"""Circuit breaker instances for external services.

This module provides pre-configured circuit breaker instances for each external service.
Each service has its own circuit breaker to prevent cascading failures.

Configuration:
- Failure threshold: 5 consecutive failures
- Timeout: 60 seconds before attempting recovery
"""

from .circuit_breaker import CircuitBreaker

# Circuit breaker for CEDA market price service
ceda_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60,
    name="ceda"
)

# Circuit breaker for Weather service (OpenMeteo)
weather_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60,
    name="weather"
)

# Circuit breaker for News service (RSS feeds)
news_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60,
    name="news"
)

# Circuit breaker for AI service (AWS Bedrock or Local)
ai_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60,
    name="ai"
)

__all__ = [
    "ceda_circuit_breaker",
    "weather_circuit_breaker",
    "news_circuit_breaker",
    "ai_circuit_breaker",
]
