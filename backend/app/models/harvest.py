from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date

class HarvestInput(BaseModel):
    crop: str
    quantity: float  # In Quintals or Kg
    quantity_unit: str = "quintals"
    location: str
    latitude: float
    longitude: float
    harvest_date: Optional[date] = None # ISO format "YYYY-MM-DD"
    storage_condition: str = "open" # open, covered, cold_storage

class Scenario(BaseModel):
    id: str # "sell_now", "wait_24h", "wait_48h"
    title: str # "Sell Now", "Wait 24 Hours"
    description: str
    risk_assessment: Dict[str, Any] # { "spoilage": "LOW", "weather": "HIGH" }
    price_projection: str # "RISING", "FALLING"
    expected_revenue_range: tuple[float, float]
    loss_reduction_actions: List[str]
    uncertainty_factors: List[str]
    upside: Optional[str] = None # Positive outcome description (e.g., "+₹2,000 Profit")
    downside: Optional[str] = None # Negative outcome description (e.g., "Rain risk 40%")
    tag: Optional[str] = None # UI Tag (e.g., "Recommended", "High Risk")

class HarvestDecision(BaseModel):
    scenarios: List[Scenario]
    market_intelligence: Dict[str, Any] # Nearby mandis info
    weather_summary: str
    recommendation: str # "sell_now" or "wait"
    recommendation_text: Optional[str] = None
