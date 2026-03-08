from typing import Dict, Any, Optional
from datetime import date
from app.services.ceda_service import ceda_service
from app.services.weather_service import weather_service
from app.services.decision_service import decision_service

# Mock Location DB (for prototype)
LOCATION_DB = {
    "madanapalle": {"lat": 13.55, "lon": 78.50, "district": "Chittoor"},
    "kurnool": {"lat": 15.82, "lon": 78.03, "district": "Kurnool"},
    "chittoor": {"lat": 13.21, "lon": 79.10, "district": "Chittoor"},
    "adoni": {"lat": 15.63, "lon": 77.28, "district": "Kurnool"},
    "anantapur": {"lat": 14.68, "lon": 77.60, "district": "Anantapur"},
    "tirupati": {"lat": 13.62, "lon": 79.41, "district": "Chittoor"},
    "vijayawada": {"lat": 16.50, "lon": 80.64, "district": "Krishna"},
    "guntur": {"lat": 16.30, "lon": 80.43, "district": "Guntur"},
    "hyderabad": {"lat": 17.3850, "lon": 78.4867, "district": "Hyderabad"},
    "warangal": {"lat": 17.9689, "lon": 79.5941, "district": "Warangal"},
    "visakhapatnam": {"lat": 17.6868, "lon": 83.2185, "district": "Visakhapatnam"},
    "vizag": {"lat": 17.6868, "lon": 83.2185, "district": "Visakhapatnam"},
    "nellore": {"lat": 14.4426, "lon": 79.9865, "district": "Nellore"},
    "kadapa": {"lat": 14.4673, "lon": 78.8242, "district": "YSR Kadapa"},
    "nizamabad": {"lat": 18.6725, "lon": 78.0941, "district": "Nizamabad"},
    "karimnagar": {"lat": 18.4386, "lon": 79.1288, "district": "Karimnagar"},
    "khammam": {"lat": 17.2473, "lon": 80.1514, "district": "Khammam"},
    "mahabubnagar": {"lat": 16.7488, "lon": 78.0035, "district": "Mahabubnagar"},
    "nalgonda": {"lat": 17.0577, "lon": 79.2684, "district": "Nalgonda"},
    "adilabad": {"lat": 19.6760, "lon": 78.5320, "district": "Adilabad"},
    "medak": {"lat": 18.0485, "lon": 78.2631, "district": "Medak"},
    "ranga reddy": {"lat": 17.3200, "lon": 78.5500, "district": "Ranga Reddy"},
}

class WeatherTool:
    name = "get_weather"
    description = "Get current weather and forecast for a location."

    async def run(self, location: str) -> str:
        weather_data = await self.run_raw(location)
        
        # Format for LLM consumption
        forecast = weather_data.get("forecast", {})
        current = weather_data.get("current", {})
        
        temp = current.get("temperature") if current.get("temperature") is not None else forecast.get("temperature_celsius", "N/A")
        
        daily_summary = ""
        if "daily_forecast" in forecast:
            daily_summary = "\n3-Day Forecast:"
            for day in forecast["daily_forecast"]:
                risk = "High Rain Risk" if day["rain_risk"] else "Low Rain Risk"
                daily_summary += f"\n- Day {day['day']}: Max {day['max_temp']}°C, {risk}"
        
        return (
            f"Weather in {location.title()}:\n"
            f"- Current Temp: {temp}°C\n"
            f"- Rain Risk (24h): {'High' if forecast.get('rain_risk_24h') else 'Low'}\n"
            f"- Rain Risk (72h): {'High' if forecast.get('rain_risk_72h') else 'Low'}\n"
            f"{daily_summary}"
        )

    async def run_raw(self, location: str) -> Dict[str, Any]:
        # Try to get coordinates from Geocoding API first
        geo_coords = await weather_service.get_coordinates(location)
        if geo_coords:
            return await weather_service.get_forecast(geo_coords["latitude"], geo_coords["longitude"])

        loc_key = location.lower().replace("telangana", "").replace("andhra pradesh", "").replace("ap", "").strip()
        coords = LOCATION_DB.get(loc_key)
        
        # Try substring match if direct key fails
        if not coords:
            for k, v in LOCATION_DB.items():
                if k in loc_key or loc_key in k:
                    coords = v
                    break
        
        if not coords:
            # Fallback to hardcoded coords if not found (simple prototype fix)
            coords = {"lat": 16.50, "lon": 80.64, "district": location}
            
        return await weather_service.get_forecast(coords["lat"], coords["lon"])

class MarketTool:
    name = "get_market_prices"
    description = "Get current market prices for a crop in a specific location."

    async def run(self, crop: str, location: str) -> str:
        prices = await self.run_raw(crop, location)
        
        try:
            current_price = prices.get("current_price", "N/A")
            trend = prices.get("trend", "stable")
            
            history_str = ""
            if "price_history" in prices and prices["price_history"]:
                history_str = "\nPast Prices (per quintal):"
                # Take last 3 entries
                recent = prices["price_history"][-3:]
                for h in recent:
                    date_str = h.get("date", "N/A")
                    p = h.get("modal_price", "N/A")
                    history_str += f"\n- {date_str}: ₹{p}"

            return (
                f"Market Price for {crop.title()} in {location.title()}:\n"
                f"- Current Price: ₹{current_price}/quintal\n"
                f"- Trend: {trend.upper()}\n"
                f"- Recommendation: {prices.get('recommendation', 'Monitor market')}"
                f"{history_str}"
            )
        except Exception as e:
            return f"Could not fetch prices for {crop} in {location}. Error: {str(e)}"

    async def run_raw(self, crop: str, location: str) -> Dict[str, Any]:
        loc_key = location.lower().replace("telangana", "").replace("andhra pradesh", "").replace("ap", "").strip()
        coords = LOCATION_DB.get(loc_key)
        
        # Try substring match if direct key fails
        if not coords:
            for k, v in LOCATION_DB.items():
                if k in loc_key or loc_key in k:
                    coords = v
                    break
        
        district = coords.get("district", location) if coords else location
        
        # Determine State
        state = "Andhra Pradesh"
        telangana_districts = ["hyderabad", "warangal", "nizamabad", "karimnagar", "khammam", "mahabubnagar", "nalgonda", "adilabad", "medak", "ranga reddy"]
        
        # Check if district is in Telangana list
        if any(d in district.lower() for d in telangana_districts):
            state = "Telangana"
        # Also check if original location string explicitly mentions Telangana
        elif "telangana" in location.lower():
            state = "Telangana"
        
        return await ceda_service.get_market_prices(
            commodity=crop,
            state=state,
            district=district
        )

# Instantiate tools
weather_tool = WeatherTool()
market_tool = MarketTool()
