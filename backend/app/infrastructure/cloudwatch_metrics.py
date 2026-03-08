"""
CloudWatch Custom Metrics Module

This module provides functionality to emit custom metrics to Amazon CloudWatch
for monitoring external API calls and other application metrics.

Requirements: 6.6, 11.6
"""

import logging
import time
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)


class CloudWatchMetrics:
    """
    CloudWatch metrics client for emitting custom application metrics.
    
    This class provides methods to log external API calls, latencies, and
    other custom metrics to CloudWatch for monitoring and alerting.
    """
    
    def __init__(self, namespace: str = "Krishi/ExternalAPIs", region: str = "ap-south-1"):
        """
        Initialize CloudWatch metrics client.
        
        Args:
            namespace: CloudWatch namespace for metrics
            region: AWS region
        """
        self.namespace = namespace
        self.region = region
        self._client = None
        self._enabled = True
        
        # Try to initialize boto3 client
        try:
            import boto3
            self._client = boto3.client('cloudwatch', region_name=region)
            logger.info(f"CloudWatch metrics enabled for namespace: {namespace}")
        except Exception as e:
            logger.warning(f"CloudWatch metrics disabled: {e}")
            self._enabled = False
    
    def log_external_api_call(
        self,
        service_name: str,
        success: bool,
        latency_ms: float,
        additional_dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Log an external API call to CloudWatch.
        
        Emits two metrics:
        1. APICallCount - Count of API calls by service and status
        2. APILatency - Latency of API calls in milliseconds
        
        Args:
            service_name: Name of the external service (e.g., "CEDA", "OpenMeteo", "NewsAPI")
            success: Whether the API call succeeded
            latency_ms: Latency of the API call in milliseconds
            additional_dimensions: Optional additional dimensions for the metric
            
        Requirements: 6.6, 11.6
        """
        if not self._enabled or not self._client:
            logger.debug(f"CloudWatch metrics disabled, skipping metric for {service_name}")
            return
        
        try:
            # Base dimensions
            dimensions = [
                {'Name': 'Service', 'Value': service_name},
                {'Name': 'Status', 'Value': 'Success' if success else 'Failure'}
            ]
            
            # Add additional dimensions if provided
            if additional_dimensions:
                for key, value in additional_dimensions.items():
                    dimensions.append({'Name': key, 'Value': str(value)})
            
            # Prepare metric data
            metric_data = [
                {
                    'MetricName': 'APICallCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': dimensions,
                    'Timestamp': time.time()
                },
                {
                    'MetricName': 'APILatency',
                    'Value': latency_ms,
                    'Unit': 'Milliseconds',
                    'Dimensions': [d for d in dimensions if d['Name'] != 'Status'],  # Latency without status
                    'Timestamp': time.time()
                }
            ]
            
            # Emit metrics to CloudWatch
            self._client.put_metric_data(
                Namespace=self.namespace,
                MetricData=metric_data
            )
            
            logger.debug(
                f"Emitted CloudWatch metrics for {service_name}: "
                f"success={success}, latency={latency_ms:.2f}ms"
            )
            
        except Exception as e:
            # Don't fail the application if metrics fail
            logger.warning(f"Failed to emit CloudWatch metrics: {e}")
    
    def log_circuit_breaker_state(
        self,
        service_name: str,
        state: str,
        failure_count: int = 0
    ) -> None:
        """
        Log circuit breaker state changes to CloudWatch.
        
        Args:
            service_name: Name of the external service
            state: Circuit breaker state (open, closed, half_open)
            failure_count: Number of consecutive failures
        """
        if not self._enabled or not self._client:
            return
        
        try:
            metric_data = [
                {
                    'MetricName': 'CircuitBreakerState',
                    'Value': 1 if state == 'open' else 0,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': service_name},
                        {'Name': 'State', 'Value': state}
                    ],
                    'Timestamp': time.time()
                },
                {
                    'MetricName': 'CircuitBreakerFailures',
                    'Value': failure_count,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': service_name}
                    ],
                    'Timestamp': time.time()
                }
            ]
            
            self._client.put_metric_data(
                Namespace=self.namespace,
                MetricData=metric_data
            )
            
            logger.debug(
                f"Emitted circuit breaker metrics for {service_name}: "
                f"state={state}, failures={failure_count}"
            )
            
        except Exception as e:
            logger.warning(f"Failed to emit circuit breaker metrics: {e}")
    
    def log_ai_inference(
        self,
        model_name: str,
        success: bool,
        latency_ms: float,
        token_count: Optional[int] = None
    ) -> None:
        """
        Log AI inference metrics to CloudWatch.
        
        Args:
            model_name: Name of the AI model used
            success: Whether the inference succeeded
            latency_ms: Latency of the inference in milliseconds
            token_count: Optional token count for the inference
        """
        if not self._enabled or not self._client:
            return
        
        try:
            metric_data = [
                {
                    'MetricName': 'AIInferenceCount',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Model', 'Value': model_name},
                        {'Name': 'Status', 'Value': 'Success' if success else 'Failure'}
                    ],
                    'Timestamp': time.time()
                },
                {
                    'MetricName': 'AIInferenceLatency',
                    'Value': latency_ms,
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'Model', 'Value': model_name}
                    ],
                    'Timestamp': time.time()
                }
            ]
            
            # Add token count metric if provided
            if token_count is not None:
                metric_data.append({
                    'MetricName': 'AITokenCount',
                    'Value': token_count,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Model', 'Value': model_name}
                    ],
                    'Timestamp': time.time()
                })
            
            self._client.put_metric_data(
                Namespace=self.namespace,
                MetricData=metric_data
            )
            
            logger.debug(
                f"Emitted AI inference metrics for {model_name}: "
                f"success={success}, latency={latency_ms:.2f}ms"
            )
            
        except Exception as e:
            logger.warning(f"Failed to emit AI inference metrics: {e}")


def track_external_api_call(service_name: str, metrics_client: Optional[CloudWatchMetrics] = None):
    """
    Decorator to track external API calls with CloudWatch metrics.
    
    Usage:
        @track_external_api_call("CEDA")
        async def fetch_ceda_data():
            # API call logic
            pass
    
    Args:
        service_name: Name of the external service
        metrics_client: Optional CloudWatch metrics client (will create one if not provided)
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            client = metrics_client or CloudWatchMetrics()
            start_time = time.time()
            success = False
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                client.log_external_api_call(service_name, success, latency_ms)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            client = metrics_client or CloudWatchMetrics()
            start_time = time.time()
            success = False
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                client.log_external_api_call(service_name, success, latency_ms)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global metrics client instance
_global_metrics_client: Optional[CloudWatchMetrics] = None


def get_metrics_client() -> CloudWatchMetrics:
    """
    Get or create the global CloudWatch metrics client.
    
    Returns:
        CloudWatch metrics client instance
    """
    global _global_metrics_client
    
    if _global_metrics_client is None:
        _global_metrics_client = CloudWatchMetrics()
    
    return _global_metrics_client
