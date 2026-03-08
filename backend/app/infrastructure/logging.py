"""Structured logging setup with structlog."""

import logging
import sys
from typing import Any, Dict
import structlog
from structlog.types import EventDict, Processor


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log entries."""
    event_dict["app"] = "krishi"
    return event_dict


def setup_logging(
    log_level: str = "INFO",
    json_logs: bool = False,
) -> None:
    """
    Set up structured logging with structlog.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: If True, output logs in JSON format; otherwise use console format
    
    Example:
        # In main.py
        setup_logging(log_level="INFO", json_logs=False)
        
        # In any module
        logger = get_logger(__name__)
        logger.info("api_call_started", service="ceda", endpoint="/prices")
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_app_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if json_logs:
        # JSON output for production
        processors.extend([
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ])
    else:
        # Console output for development
        processors.extend([
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Set log level for httpx to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Structured logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("user_action", action="login", user_id="123")
        logger.error("api_error", service="ceda", error="timeout", retry_attempt=2)
    """
    return structlog.get_logger(name)


def log_api_call(
    logger: structlog.stdlib.BoundLogger,
    service: str,
    endpoint: str,
    method: str = "GET",
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Helper to log API calls with consistent structure.
    
    Args:
        logger: Structured logger instance
        service: Service name (e.g., "ceda", "weather")
        endpoint: API endpoint
        method: HTTP method
        **kwargs: Additional context to log
    
    Returns:
        Dictionary with log context for use in subsequent logs
    
    Example:
        context = log_api_call(logger, "ceda", "/prices", method="POST")
        # ... make API call ...
        logger.info("api_call_completed", **context, duration_ms=234, status=200)
    """
    context = {
        "service": service,
        "endpoint": endpoint,
        "method": method,
        **kwargs,
    }
    
    logger.info("api_call_started", **context)
    return context


def log_error(
    logger: structlog.stdlib.BoundLogger,
    error: Exception,
    context: Dict[str, Any],
) -> None:
    """
    Helper to log errors with consistent structure.
    
    Args:
        logger: Structured logger instance
        error: Exception that occurred
        context: Additional context about the error
    
    Example:
        try:
            result = await fetch_data()
        except Exception as e:
            log_error(logger, e, {
                "service": "ceda",
                "operation": "fetch_prices",
                "user_id": "123",
            })
    """
    logger.error(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        **context,
        exc_info=True,
    )
