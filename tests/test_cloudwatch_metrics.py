"""
Tests for CloudWatch metrics integration.

These tests verify that CloudWatch metrics can be emitted for external API calls
and circuit breaker state changes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.app.infrastructure.cloudwatch_metrics import (
    CloudWatchMetrics,
    track_external_api_call,
    get_metrics_client
)


class TestCloudWatchMetrics:
    """Test CloudWatch metrics functionality."""
    
    def test_cloudwatch_metrics_initialization(self):
        """Test CloudWatch metrics client initialization."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            metrics = CloudWatchMetrics(namespace="Test/Namespace", region="us-east-1")
            
            assert metrics.namespace == "Test/Namespace"
            assert metrics.region == "us-east-1"
            assert metrics._enabled is True
            mock_boto3.client.assert_called_once_with('cloudwatch', region_name='us-east-1')
    
    def test_cloudwatch_metrics_disabled_on_import_error(self):
        """Test that metrics are disabled when boto3 is not available."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3', side_effect=ImportError("No boto3")):
            metrics = CloudWatchMetrics()
            
            assert metrics._enabled is False
            assert metrics._client is None
    
    def test_log_external_api_call_success(self):
        """Test logging successful external API call."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            metrics = CloudWatchMetrics()
            metrics.log_external_api_call("TestService", True, 123.45)
            
            # Verify put_metric_data was called
            mock_client.put_metric_data.assert_called_once()
            call_args = mock_client.put_metric_data.call_args
            
            # Verify namespace
            assert call_args[1]['Namespace'] == "Krishi/ExternalAPIs"
            
            # Verify metric data
            metric_data = call_args[1]['MetricData']
            assert len(metric_data) == 2  # APICallCount and APILatency
            
            # Check APICallCount metric
            call_count_metric = next(m for m in metric_data if m['MetricName'] == 'APICallCount')
            assert call_count_metric['Value'] == 1
            assert call_count_metric['Unit'] == 'Count'
            
            # Check dimensions
            dimensions = {d['Name']: d['Value'] for d in call_count_metric['Dimensions']}
            assert dimensions['Service'] == 'TestService'
            assert dimensions['Status'] == 'Success'
            
            # Check APILatency metric
            latency_metric = next(m for m in metric_data if m['MetricName'] == 'APILatency')
            assert latency_metric['Value'] == 123.45
            assert latency_metric['Unit'] == 'Milliseconds'
    
    def test_log_external_api_call_failure(self):
        """Test logging failed external API call."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            metrics = CloudWatchMetrics()
            metrics.log_external_api_call("TestService", False, 50.0)
            
            # Verify put_metric_data was called
            mock_client.put_metric_data.assert_called_once()
            call_args = mock_client.put_metric_data.call_args
            
            # Verify metric data
            metric_data = call_args[1]['MetricData']
            
            # Check status dimension
            call_count_metric = next(m for m in metric_data if m['MetricName'] == 'APICallCount')
            dimensions = {d['Name']: d['Value'] for d in call_count_metric['Dimensions']}
            assert dimensions['Status'] == 'Failure'
    
    def test_log_external_api_call_with_additional_dimensions(self):
        """Test logging API call with additional dimensions."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            metrics = CloudWatchMetrics()
            metrics.log_external_api_call(
                "TestService",
                True,
                100.0,
                additional_dimensions={"Region": "us-east-1", "Environment": "test"}
            )
            
            # Verify additional dimensions are included
            call_args = mock_client.put_metric_data.call_args
            metric_data = call_args[1]['MetricData']
            call_count_metric = next(m for m in metric_data if m['MetricName'] == 'APICallCount')
            
            dimensions = {d['Name']: d['Value'] for d in call_count_metric['Dimensions']}
            assert dimensions['Region'] == 'us-east-1'
            assert dimensions['Environment'] == 'test'
    
    def test_log_external_api_call_disabled(self):
        """Test that logging does nothing when metrics are disabled."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3', side_effect=ImportError("No boto3")):
            metrics = CloudWatchMetrics()
            
            # Should not raise an error
            metrics.log_external_api_call("TestService", True, 100.0)
    
    def test_log_external_api_call_handles_errors(self):
        """Test that logging errors don't crash the application."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3') as mock_boto3:
            mock_client = Mock()
            mock_client.put_metric_data.side_effect = Exception("CloudWatch error")
            mock_boto3.client.return_value = mock_client
            
            metrics = CloudWatchMetrics()
            
            # Should not raise an error
            metrics.log_external_api_call("TestService", True, 100.0)
    
    def test_log_circuit_breaker_state(self):
        """Test logging circuit breaker state changes."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            metrics = CloudWatchMetrics()
            metrics.log_circuit_breaker_state("TestService", "open", 5)
            
            # Verify put_metric_data was called
            mock_client.put_metric_data.assert_called_once()
            call_args = mock_client.put_metric_data.call_args
            
            # Verify metric data
            metric_data = call_args[1]['MetricData']
            assert len(metric_data) == 2  # CircuitBreakerState and CircuitBreakerFailures
            
            # Check CircuitBreakerState metric
            state_metric = next(m for m in metric_data if m['MetricName'] == 'CircuitBreakerState')
            assert state_metric['Value'] == 1  # open = 1
            
            # Check CircuitBreakerFailures metric
            failures_metric = next(m for m in metric_data if m['MetricName'] == 'CircuitBreakerFailures')
            assert failures_metric['Value'] == 5
    
    def test_log_ai_inference(self):
        """Test logging AI inference metrics."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            metrics = CloudWatchMetrics()
            metrics.log_ai_inference("test-model", True, 500.0, token_count=150)
            
            # Verify put_metric_data was called
            mock_client.put_metric_data.assert_called_once()
            call_args = mock_client.put_metric_data.call_args
            
            # Verify metric data
            metric_data = call_args[1]['MetricData']
            assert len(metric_data) == 3  # Count, Latency, TokenCount
            
            # Check metrics exist
            metric_names = {m['MetricName'] for m in metric_data}
            assert 'AIInferenceCount' in metric_names
            assert 'AIInferenceLatency' in metric_names
            assert 'AITokenCount' in metric_names
    
    def test_get_metrics_client_singleton(self):
        """Test that get_metrics_client returns a singleton instance."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            # Reset global client
            import backend.app.infrastructure.cloudwatch_metrics as metrics_module
            metrics_module._global_metrics_client = None
            
            client1 = get_metrics_client()
            client2 = get_metrics_client()
            
            assert client1 is client2


class TestTrackExternalAPICallDecorator:
    """Test the track_external_api_call decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_tracks_successful_async_call(self):
        """Test decorator tracks successful async function call."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            metrics = CloudWatchMetrics()
            
            @track_external_api_call("TestService", metrics_client=metrics)
            async def test_function():
                return "success"
            
            result = await test_function()
            
            assert result == "success"
            mock_client.put_metric_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_decorator_tracks_failed_async_call(self):
        """Test decorator tracks failed async function call."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            metrics = CloudWatchMetrics()
            
            @track_external_api_call("TestService", metrics_client=metrics)
            async def test_function():
                raise ValueError("Test error")
            
            with pytest.raises(ValueError):
                await test_function()
            
            # Verify metrics were still emitted
            mock_client.put_metric_data.assert_called_once()
            
            # Verify failure status
            call_args = mock_client.put_metric_data.call_args
            metric_data = call_args[1]['MetricData']
            call_count_metric = next(m for m in metric_data if m['MetricName'] == 'APICallCount')
            dimensions = {d['Name']: d['Value'] for d in call_count_metric['Dimensions']}
            assert dimensions['Status'] == 'Failure'
    
    def test_decorator_tracks_successful_sync_call(self):
        """Test decorator tracks successful sync function call."""
        with patch('backend.app.infrastructure.cloudwatch_metrics.boto3') as mock_boto3:
            mock_client = Mock()
            mock_boto3.client.return_value = mock_client
            
            metrics = CloudWatchMetrics()
            
            @track_external_api_call("TestService", metrics_client=metrics)
            def test_function():
                return "success"
            
            result = test_function()
            
            assert result == "success"
            mock_client.put_metric_data.assert_called_once()
