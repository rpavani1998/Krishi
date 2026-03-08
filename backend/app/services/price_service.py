from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import date
import random

class PriceService(ABC):
    @abstractmethod
    async def get_price_trends(self, crop: str, location: str, harvest_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get price trends for a specific crop and location.
        Returns:
            - current_price_range: (min, max)
            - trend: "RISING", "FALLING", "STABLE"
            - nearby_mandis: List of nearby market prices
        """
        pass

class MockPriceService(PriceService):
    """
    Mock implementation mimicking AP/Telangana mandi prices.
    """
    
    MOCK_DATA = {
        "Tomato": {
            "Guntur": {"price": (1500, 2200), "trend": "FALLING"}, # Prices in Rs/Quintal
            "Hyderabad": {"price": (1800, 2500), "trend": "STABLE"},
            "Kurnool": {"price": (1600, 2100), "trend": "RISING"},
        },
        "Onion": {
            "Kurnool": {"price": (2500, 3200), "trend": "RISING"},
            "Hyderabad": {"price": (2800, 3500), "trend": "STABLE"},
        },
        "Chillies": {
            "Guntur": {"price": (15000, 18000), "trend": "STABLE"},
            "Warangal": {"price": (14500, 17500), "trend": "RISING"},
        },
        "Paddy": {
            "Nizamabad": {"price": (2100, 2300), "trend": "STABLE"},
            "West Godavari": {"price": (2050, 2250), "trend": "FALLING"},
        },
        "Cotton": {
            "Adoni": {"price": (6800, 7200), "trend": "RISING"},
            "Warangal": {"price": (6900, 7300), "trend": "STABLE"},
        }
    }

    async def get_price_trends(self, crop: str, location: str, harvest_date: Optional[date] = None) -> Dict[str, Any]:
        # Simple fuzzy matching or default
        crop_data = self.MOCK_DATA.get(crop, {})
        if not crop_data:
            # Return generic default if crop not found
            return {
                "current_price_range": (1000, 1500),
                "trend": "UNCERTAIN",
                "nearby_mandis": [],
                "history": [
                    {"date": "3 days ago", "price": 1000},
                    {"date": "2 days ago", "price": 1100},
                    {"date": "Yesterday", "price": 1200}
                ]
            }

        # Simulate finding nearby mandis
        # In a real app, we would use geospatial search
        nearby_mandis = []
        for mandi_name, data in crop_data.items():
            nearby_mandis.append({
                "name": mandi_name,
                "distance_km": random.randint(10, 100), # Mock distance
                "price_min": data["price"][0],
                "price_max": data["price"][1],
                "trend": data["trend"]
            })
        
        # Sort by distance
        nearby_mandis.sort(key=lambda x: x["distance_km"])

        # Determine overall trend based on the closest mandi (or average)
        primary_mandi = nearby_mandis[0] if nearby_mandis else None
        
        # Generate mock history based on trend
        history = []
        base_price = (primary_mandi["price_min"] + primary_mandi["price_max"]) / 2 if primary_mandi else 1250
        trend = primary_mandi["trend"] if primary_mandi else "UNCERTAIN"
        
        if trend == "RISING":
            history = [
                {"date": "3 days ago", "price": int(base_price * 0.90)},
                {"date": "2 days ago", "price": int(base_price * 0.95)},
                {"date": "Yesterday", "price": int(base_price * 0.98)}
            ]
        elif trend == "FALLING":
            history = [
                {"date": "3 days ago", "price": int(base_price * 1.10)},
                {"date": "2 days ago", "price": int(base_price * 1.05)},
                {"date": "Yesterday", "price": int(base_price * 1.02)}
            ]
        else: # STABLE
            history = [
                {"date": "3 days ago", "price": int(base_price * 0.99)},
                {"date": "2 days ago", "price": int(base_price * 1.01)},
                {"date": "Yesterday", "price": int(base_price * 1.00)}
            ]

        return {
            "current_price_range": (primary_mandi["price_min"], primary_mandi["price_max"]) if primary_mandi else (0,0),
            "trend": trend,
            "nearby_mandis": nearby_mandis,
            "history": history
        }
