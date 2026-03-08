"""Pydantic validation models for all external API responses."""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, List, Optional, Tuple
from datetime import datetime


# CEDA Service Models

class MandiInfo(BaseModel):
    """Information about a mandi (market)."""
    name: str
    distance_km: float = Field(ge=0)
    price_min: float = Field(gt=0)
    price_max: float = Field(gt=0)
    trend: Literal["RISING", "FALLING", "STABLE"]
    
    @field_validator('price_max')
    @classmethod
    def max_greater_than_min(cls, v: float, info) -> float:
        """Validate that max_price >= min_price."""
        if 'price_min' in info.data and v < info.data['price_min']:
            raise ValueError('price_max must be >= price_min')
        return v


class CEDAPrice(BaseModel):
    """CEDA price data for a commodity."""
    commodity_id: int
    commodity_name: str
    min_price: float = Field(gt=0)
    max_price: float = Field(gt=0)
    modal_price: float = Field(gt=0)
    date: str
    
    @field_validator('max_price')
    @classmethod
    def max_greater_than_min(cls, v: float, info) -> float:
        """Validate that max_price >= min_price."""
        if 'min_price' in info.data and v < info.data['min_price']:
            raise ValueError('max_price must be >= min_price')
        return v
    
    @field_validator('modal_price')
    @classmethod
    def modal_in_range(cls, v: float, info) -> float:
        """Validate that modal_price is between min and max."""
        if 'min_price' in info.data and 'max_price' in info.data:
            if not (info.data['min_price'] <= v <= info.data['max_price']):
                raise ValueError('modal_price must be between min_price and max_price')
        return v


class CEDAPriceResponse(BaseModel):
    """Response from CEDA service with price data."""
    current_price: float = Field(gt=0)
    current_price_range: Tuple[float, float]
    trend: Literal["RISING", "FALLING", "STABLE"]
    nearby_mandis: List[MandiInfo]
    price_history: List[CEDAPrice] = []
    recommendation: str
    data_source: Literal["live", "cached", "fallback"]
    data_timestamp: datetime
    
    @field_validator('current_price_range')
    @classmethod
    def validate_price_range(cls, v: Tuple[float, float]) -> Tuple[float, float]:
        """Validate that price range is valid."""
        min_price, max_price = v
        if min_price <= 0 or max_price <= 0:
            raise ValueError('Price range values must be positive')
        if max_price < min_price:
            raise ValueError('max_price must be >= min_price')
        return v


# Weather Service Models

class WeatherForecast(BaseModel):
    """Weather forecast data."""
    temperature_celsius: float
    rain_risk_24h: bool
    rain_risk_48h: bool
    rain_probability: float = Field(ge=0, le=100)
    wind_speed_kmh: float = Field(ge=0)
    conditions: str
    forecast_date: str
    
    @field_validator('forecast_date')
    @classmethod
    def date_in_future(cls, v: str) -> str:
        """Validate that forecast_date is in the future."""
        try:
            forecast_dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            if forecast_dt < datetime.now(forecast_dt.tzinfo):
                raise ValueError('forecast_date must be in the future')
        except ValueError as e:
            if 'future' in str(e):
                raise
            # If it's a parsing error, let it pass for now
            pass
        return v


class WeatherResponse(BaseModel):
    """Response from Weather service."""
    forecast: WeatherForecast
    data_source: Literal["live", "cached", "fallback"]
    data_timestamp: datetime


# AI Service Models

class AIResponse(BaseModel):
    """Response from AI service (intent analysis)."""
    intent: str
    response_text: str
    data: Optional[dict] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)


class TranscriptionResponse(BaseModel):
    """Response from transcription service."""
    transcript: str
    confidence: Optional[float] = Field(None, ge=0, le=1)
    language: Optional[str] = None
    error: Optional[str] = None


# Decision Service Models

class RiskAssessment(BaseModel):
    """Risk assessment for a decision scenario."""
    spoilage: Literal["LOW", "MEDIUM", "HIGH"]
    weather: Literal["LOW", "MEDIUM", "HIGH"]
    price: Literal["LOW", "MEDIUM", "HIGH"]
    overall: Literal["LOW", "MEDIUM", "HIGH"]


class DecisionScenario(BaseModel):
    """A decision scenario for harvest timing."""
    id: str
    title: str
    description: str
    risk_assessment: RiskAssessment
    price_projection: Literal["RISING", "FALLING", "STABLE"]
    expected_revenue_range: Tuple[float, float]
    loss_reduction_actions: List[str]
    uncertainty_factors: List[str]
    recommended: bool = False
    
    @field_validator('expected_revenue_range')
    @classmethod
    def validate_revenue_range(cls, v: Tuple[float, float]) -> Tuple[float, float]:
        """Validate that revenue range is valid."""
        min_rev, max_rev = v
        if min_rev < 0 or max_rev < 0:
            raise ValueError('Revenue values cannot be negative')
        if max_rev < min_rev:
            raise ValueError('max_revenue must be >= min_revenue')
        return v


class MarketIntelligence(BaseModel):
    """Market intelligence summary."""
    price_trend: Literal["RISING", "FALLING", "STABLE"]
    demand_level: Literal["LOW", "MEDIUM", "HIGH"]
    supply_level: Literal["LOW", "MEDIUM", "HIGH"]
    summary: str


class HarvestDecision(BaseModel):
    """Complete harvest decision with scenarios."""
    scenarios: List[DecisionScenario]
    market_intelligence: MarketIntelligence
    weather_summary: str
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"]
    data_freshness: dict  # Timestamps for each data source
    
    @field_validator('scenarios')
    @classmethod
    def at_least_one_scenario(cls, v: List[DecisionScenario]) -> List[DecisionScenario]:
        """Validate that at least one scenario is provided."""
        if len(v) == 0:
            raise ValueError('At least one scenario must be provided')
        return v


# News Service Models

class NewsArticle(BaseModel):
    """A single news article."""
    title: str
    summary: str
    date: str
    source: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    
    @field_validator('date')
    @classmethod
    def date_not_in_future(cls, v: str) -> str:
        """Validate that article date is not in the future."""
        try:
            article_dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            now = datetime.now(article_dt.tzinfo) if article_dt.tzinfo else datetime.now()
            if article_dt > now:
                raise ValueError('Article date cannot be in the future')
        except ValueError as e:
            if 'future' in str(e):
                raise
            # If it's a parsing error, let it pass for now
            pass
        return v


class NewsResponse(BaseModel):
    """Response from News service."""
    articles: List[NewsArticle]
    total: int
    filters: dict
    data_source: Literal["live", "cached", "fallback"]
    data_timestamp: datetime
    
    @field_validator('total')
    @classmethod
    def total_matches_articles(cls, v: int, info) -> int:
        """Validate that total matches the number of articles."""
        if 'articles' in info.data and v != len(info.data['articles']):
            raise ValueError('total must match the number of articles')
        return v


# Error Response Model

class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str  # Error code (e.g., "SERVICE_UNAVAILABLE")
    message: str  # User-friendly message
    details: Optional[dict] = None  # Additional context
    recoverable: bool  # Can user retry?
    retry_after: Optional[int] = None  # Seconds to wait before retry
    actions: List[str] = []  # Suggested actions for user
