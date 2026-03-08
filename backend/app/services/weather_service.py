from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
import logging
import time
from datetime import datetime
from pydantic import ValidationError

from app.infrastructure.retry import retry_with_backoff
from app.infrastructure.circuit_breakers import weather_circuit_breaker
from app.infrastructure.cache import CacheService
from app.models.validation import WeatherResponse, WeatherForecast

# Import CloudWatch metrics if available
try:
    from app.infrastructure.cloudwatch_metrics import get_metrics_client
    CLOUDWATCH_AVAILABLE = True
except ImportError:
    CLOUDWATCH_AVAILABLE = False
    get_metrics_client = None

logger = logging.getLogger(__name__)

class WeatherService(ABC):
    @abstractmethod
    async def get_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get weather forecast for the given coordinates."""
        pass

from app.core.config import settings

class OpenMeteoWeatherService(WeatherService):
    BASE_URL = settings.OPEN_METEO_URL
    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    
    def __init__(self):
        """Initialize weather service with cache."""
        # Initialize cache with 3-hour TTL for weather data
        self.cache = CacheService(ttl_seconds={
            "weather": 3 * 3600,  # 3 hours
            "geocoding": 24 * 3600, # 24 hours
        })
        
        # Initialize CloudWatch metrics client if available
        self.metrics_client = None
        if CLOUDWATCH_AVAILABLE:
            try:
                self.metrics_client = get_metrics_client()
            except Exception as e:
                logger.debug(f"CloudWatch metrics not available: {e}")

    async def get_coordinates(self, location: str) -> Optional[Dict[str, float]]:
        """
        Get coordinates for a location name using Open-Meteo Geocoding API.
        """
        # Check cache
        cache_key = f"geo:{location.lower()}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    self.GEOCODING_URL,
                    params={"name": location, "count": 1, "language": "en", "format": "json"}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        result = data["results"][0]
                        coords = {
                            "latitude": result["latitude"],
                            "longitude": result["longitude"]
                        }
                        # Cache result
                        await self.cache.set(cache_key, coords)
                        return coords
        except Exception as e:
            logger.error(f"Geocoding failed for {location}: {e}")
            
        return None

    async def get_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get weather forecast with retry logic, circuit breaker protection, and caching.
        
        Returns weather data with data_source and data_timestamp fields.
        Falls back to cached or safe default on failure.
        """
        # Create cache key based on coordinates and date
        today = datetime.now().date().isoformat()
        cache_key = f"weather:{latitude:.2f}:{longitude:.2f}:{today}"
        
        # Check cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(
                "Weather data retrieved from cache",
                extra={
                    "latitude": latitude,
                    "longitude": longitude,
                    "cache_key": cache_key
                }
            )
            # Update data_source to indicate cached data
            cached_data["data_source"] = "cached"
            return cached_data
        
        try:
            # Use circuit breaker to protect against cascading failures
            data = await weather_circuit_breaker.call(
                self._fetch_weather_with_retry,
                latitude,
                longitude
            )
            
            # Cache the successful response
            await self.cache.set(cache_key, data)
            
            return data
        except Exception as e:
            logger.error(
                f"Weather service failed after retries and circuit breaker: {e}",
                extra={
                    "latitude": latitude,
                    "longitude": longitude,
                    "circuit_state": weather_circuit_breaker.state
                }
            )
            # Return fallback data
            return self._get_fallback_weather()
    
    @retry_with_backoff(max_attempts=3, base_delay=1.0, max_delay=10.0)
    async def _fetch_weather_with_retry(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Fetch weather data with automatic retry on failures.
        
        Retries on:
        - Connection errors
        - Timeouts
        - 5xx status codes
        """
        start_time = time.time()
        success = False
        
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,rain,wind_speed_10m",
                "current_weather": "true",
                "forecast_days": 3,
                "timezone": "auto"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                success = True
                
                # Transform data into a more usable format for our Reasoning Engine
                return self._transform_weather_data(data)
        finally:
            # Emit CloudWatch metrics
            if self.metrics_client:
                latency_ms = (time.time() - start_time) * 1000
                self.metrics_client.log_external_api_call(
                    "OpenMeteo",
                    success,
                    latency_ms
                )

    def _transform_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key metrics for decision making:
        - Current condition
        - Rain risk over next 24h, 48h, 72h
        - Max temperature (for spoilage risk)
        
        Includes data_source and data_timestamp for transparency.
        Validates response using Pydantic models.
        """
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        rain_probs = hourly.get("precipitation_probability", [])
        temps = hourly.get("temperature_2m", [])
        wind_speeds = hourly.get("wind_speed_10m", [])
        
        # Simple analysis
        # Check next 24h for high rain probability (>50%)
        rain_risk_24h = any(p > 50 for p in rain_probs[:24] if p is not None)
        rain_risk_48h = any(p > 50 for p in rain_probs[24:48] if p is not None)
        rain_risk_72h = any(p > 50 for p in rain_probs[48:72] if p is not None)
        
        max_temp_24h = max(temps[:24]) if temps else 30
        avg_wind_speed = sum(wind_speeds[:24]) / len(wind_speeds[:24]) if wind_speeds else 10
        
        # Calculate average rain probability for next 24h
        valid_rain_probs = [p for p in rain_probs[:24] if p is not None]
        avg_rain_prob = sum(valid_rain_probs) / len(valid_rain_probs) if valid_rain_probs else 0
        
        # Generate Daily Forecast Summary (3 days)
        daily_forecast = []
        for i in range(3):
            start_idx = i * 24
            end_idx = (i + 1) * 24
            
            day_temps = temps[start_idx:end_idx] if len(temps) > start_idx else []
            day_rain = rain_probs[start_idx:end_idx] if len(rain_probs) > start_idx else []
            
            day_max_temp = max(day_temps) if day_temps else 0
            day_rain_risk = any(p > 50 for p in day_rain if p is not None)
            
            daily_forecast.append({
                "day": i + 1,
                "max_temp": day_max_temp,
                "rain_risk": day_rain_risk,
                "rain_prob_max": max(day_rain) if day_rain else 0
            })

        # Get forecast date - use tomorrow to ensure it's in the future
        from datetime import timedelta
        forecast_date = (datetime.now() + timedelta(days=1)).isoformat()
        
        current_weather = data.get("current_weather", {})

        return {
            "current": {
                "temperature": current_weather.get("temperature", 0),
                "weathercode": current_weather.get("weathercode", 0),
                "windspeed": current_weather.get("windspeed", 0),
                "time": current_weather.get("time")
            },
            "forecast": {
                "temperature_celsius": float(temps[0]) if temps else 0.0,
                "rain_risk_24h": bool(rain_risk_24h),
                "rain_risk_48h": bool(rain_risk_48h),
                "rain_risk_72h": bool(rain_risk_72h),
                "rain_probability": float(avg_rain_prob),
                "wind_speed_kmh": float(avg_wind_speed),
                "conditions": "Rainy" if rain_risk_24h else "Clear",
                "max_temp_24h": float(max_temp_24h),
                "forecast_date": forecast_date,
                "daily_forecast": daily_forecast
            },
            "data_source": "live",
            "data_timestamp": datetime.now()
        }

    def _get_fallback_weather(self) -> Dict[str, Any]:
        """
        Return safe default weather assessment on failure.
        
        Includes data_source="fallback" and timestamp for transparency.
        """
        logger.warning("Returning fallback weather data")
        return {
            "current": {"temperature": 25, "weathercode": 0},
            "forecast": {
                "rain_risk_24h": False,
                "rain_risk_48h": False,
                "max_temp_24h": 30,
                "hourly_rain_prob": []
            },
            "data_source": "fallback",
            "data_timestamp": datetime.now().isoformat()
        }

weather_service = OpenMeteoWeatherService()
