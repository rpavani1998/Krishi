import httpx
from typing import Dict, Any, List, Optional, Tuple
from app.services.price_service import PriceService
from app.core.config import settings
from datetime import datetime, timedelta, date
import logging
import asyncio
import random
from app.infrastructure.retry import retry_with_backoff
from app.infrastructure.circuit_breakers import ceda_circuit_breaker
from app.infrastructure.cache import CacheService
from app.models.validation import CEDAPriceResponse, MandiInfo, CEDAPrice
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class CedaPriceService(PriceService):
    BASE_URL = "https://api.ceda.ashoka.edu.in/v1"
    
    def __init__(self):
        self.api_key = settings.CEDA_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self._commodities_map: Dict[str, int] = {} # Name -> ID
        self._states_map: Dict[str, int] = {}      # Name -> ID
        self._districts_map: Dict[str, int] = {}   # Name -> ID
        self._id_to_district_map: Dict[int, str] = {} # ID -> Name
        self._district_to_state: Dict[int, int] = {} # District ID -> State ID
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Initialize cache with TTLs
        self.cache = CacheService(ttl_seconds={
            "price": 6 * 3600,      # 6 hours for price data
            "mappings": 24 * 3600,  # 24 hours for commodity/geography mappings
        })

    @retry_with_backoff(max_attempts=3, base_delay=1.0, max_delay=10.0)
    async def _initialize_mappings(self):
        """Fetch commodities and geographies to build lookup maps."""
        async with self._lock:
            if self._initialized:
                return

            # Check cache first
            cached_mappings = await self.cache.get("mappings:ceda")
            if cached_mappings:
                logger.info("Loading CEDA mappings from cache")
                self._commodities_map = cached_mappings.get("commodities", {})
                self._states_map = cached_mappings.get("states", {})
                self._districts_map = cached_mappings.get("districts", {})
                self._id_to_district_map = cached_mappings.get("id_to_district", {})
                self._district_to_state = cached_mappings.get("district_to_state", {})
                self._initialized = True
                logger.info(f"CEDA Service Initialized from cache: {len(self._commodities_map)} commodities, {len(self._states_map)} states.")
                return

            async def _fetch_mappings():
                async with httpx.AsyncClient() as client:
                    # 1. Fetch Commodities
                    resp = await client.get(f"{self.BASE_URL}/agmarknet/commodities", headers=self.headers, timeout=10.0)
                    resp.raise_for_status()
                    data = resp.json()
                    
                    if "output" in data and "data" in data["output"]:
                        for item in data["output"]["data"]:
                            self._commodities_map[item["commodity_name"].lower()] = item["commodity_id"]
                    
                    # 2. Fetch Geographies
                    resp = await client.get(f"{self.BASE_URL}/agmarknet/geographies", headers=self.headers, timeout=10.0)
                    resp.raise_for_status()
                    geo_data = resp.json()
                    
                    if "output" in geo_data and "data" in geo_data["output"]:
                        for entry in geo_data["output"]["data"]:
                            state_id = entry["census_state_id"]
                            state_name = entry["census_state_name"].lower()
                            self._states_map[state_name] = state_id
                            
                            dist_id = entry["census_district_id"]
                            dist_name = entry["census_district_name"].lower()
                            self._districts_map[dist_name] = dist_id
                            self._id_to_district_map[dist_id] = entry["census_district_name"]
                            self._district_to_state[dist_id] = state_id
                    
                    self._initialized = True
                    
                    # Cache the mappings
                    await self.cache.set("mappings:ceda", {
                        "commodities": self._commodities_map,
                        "states": self._states_map,
                        "districts": self._districts_map,
                        "id_to_district": self._id_to_district_map,
                        "district_to_state": self._district_to_state,
                    })
                    
                    logger.info(f"CEDA Service Initialized: {len(self._commodities_map)} commodities, {len(self._states_map)} states.")

            try:
                await ceda_circuit_breaker.call(_fetch_mappings)
            except Exception as e:
                logger.error(f"Failed to initialize CEDA mappings: {e}")
                # Allow partial failure or retry? For now, we just log.

    async def get_market_prices(self, commodity: str, state: str, district: str, date_filter: Optional[date] = None) -> Dict[str, Any]:
        """
        Alias for get_price_trends to match the interface expected by endpoints.
        """
        return await self.get_price_trends(commodity, district, date_filter)

    async def get_price_trends(self, crop: str, location: str, harvest_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Fetch price trends for a crop in a specific location.
        Returns format compatible with ScenarioEngine.
        """
        if not self._initialized:
            await self._initialize_mappings()

        crop_lower = crop.lower()
        # Handle crop name variations (simple mapping)
        crop_map_fix = {
            "chilli": "chillies",
            "paddy": "paddy(dhan)(common)",
            "cotton": "cotton",
            "tomato": "tomato",
            "onion": "onion"
        }
        lookup_crop = crop_map_fix.get(crop_lower, crop_lower)
        
        # Try to find partial match if exact match fails
        crop_id = self._commodities_map.get(lookup_crop)
        if not crop_id:
            for name, cid in self._commodities_map.items():
                if lookup_crop in name:
                    crop_id = cid
                    break
        
        if not crop_id:
            logger.warning(f"Crop '{crop}' (lookup: '{lookup_crop}') not found in CEDA database. Available: {list(self._commodities_map.keys())[:5]}...")
            return await self._get_fallback_price(crop, location)

        # Resolve Location
        location_lower = location.lower()
        state_id = self._states_map.get(location_lower)
        district_id = self._districts_map.get(location_lower)
        
        target_state_id = state_id
        if not target_state_id and district_id:
            target_state_id = self._district_to_state.get(district_id)
        
        if not target_state_id:
            # Default to Andhra Pradesh (State ID 28 usually, but map logic handles it)
            target_state_id = self._states_map.get("andhra pradesh")
            
            if not target_state_id:
                 # Fallback entirely
                 return await self._get_fallback_price(crop, location)

        # Prepare Request
        if harvest_date:
            end_date = harvest_date
        else:
            end_date = datetime.now().date()
            
        start_date = end_date - timedelta(days=30) 
        
        # Check cache for price data
        cache_key = f"price:{crop_id}:{target_state_id}:{end_date.strftime('%Y-%m-%d')}"
        cached_price = await self.cache.get(cache_key)
        if cached_price:
            logger.info(f"Returning cached price data for {crop} in state {target_state_id}")
            # Mark as cached data
            cached_price["data_source"] = "cached"
            # Validate cached data
            return await self._validate_and_return(cached_price, crop, location)
        
        payload = {
            "commodity_id": crop_id,
            "state_id": target_state_id,
            "from_date": start_date.strftime("%Y-%m-%d"),
            "to_date": end_date.strftime("%Y-%m-%d")
        }
        
        # Fetch data for the whole state to get nearby markets too
        @retry_with_backoff(max_attempts=3, base_delay=1.0, max_delay=10.0)
        async def _fetch_prices():
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.BASE_URL}/agmarknet/prices", 
                    headers=self.headers, 
                    json=payload,
                    timeout=15.0
                )
                resp.raise_for_status()
                return resp.json()
        
        try:
            data = await ceda_circuit_breaker.call(_fetch_prices)
            
            prices_data = []
            if "output" in data and "data" in data["output"]:
                prices_data = data["output"]["data"]
            
            if not prices_data:
                return await self._get_fallback_price(crop, location)

            result = self._process_price_data(prices_data, district_id, target_state_id)
            
            # Cache the result
            await self.cache.set(cache_key, result)
            
            return result

        except Exception as e:
            logger.error(f"Error fetching CEDA prices: {e}")
            return await self._get_fallback_price(crop, location)

    def _process_price_data(self, data: List[Dict], target_district_id: Optional[int], state_id: int) -> Dict[str, Any]:
        """Process raw API data into application format."""
        
        # 1. Group by District/Market
        district_records: Dict[int, List[Dict]] = {}
        
        for record in data:
            d_id = record.get("census_district_id") or record.get("district_id")
            if not d_id: d_id = 0
            
            if d_id not in district_records:
                district_records[d_id] = []
            district_records[d_id].append(record)

        # 2. Find Target Data
        target_data = []
        target_source_id = None
        
        if target_district_id and target_district_id in district_records:
            target_data = district_records[target_district_id]
            target_source_id = target_district_id
        elif 0 in district_records:
            target_data = district_records[0]
            target_source_id = 0
        else:
            if district_records:
                target_source_id = list(district_records.keys())[0]
                target_data = district_records[target_source_id]

        # 3. Calculate Current Price Range & Trend for Target
        sorted_target = sorted(target_data, key=lambda x: x["date"])
        
        current_price_range = (0, 0)
        current_val = 0
        trend = "STABLE"
        price_history = []
        
        if sorted_target:
            latest = sorted_target[-1]
            min_p = float(latest.get("min_price", 0))
            max_p = float(latest.get("max_price", 0))
            modal_p = float(latest.get("modal_price", 0))
            current_price_range = (min_p, max_p)
            current_val = modal_p
            
            # Populate price history
            for item in sorted_target:
                try:
                    price_history.append({
                        "commodity_id": item.get("commodity_id", 0),
                        "commodity_name": item.get("commodity_name", "Unknown"),
                        "min_price": float(item.get("min_price", 0)),
                        "max_price": float(item.get("max_price", 0)),
                        "modal_price": float(item.get("modal_price", 0)),
                        "date": item.get("date", "")
                    })
                except (ValueError, TypeError):
                    continue
            
            # Trend
            if len(sorted_target) > 5:
                recent = sorted_target[-3:]
                old = sorted_target[:3]
                avg_recent = sum(float(x.get("modal_price", 0)) for x in recent) / 3
                avg_old = sum(float(x.get("modal_price", 0)) for x in old) / 3
                
                if avg_recent > avg_old * 1.05:
                    trend = "RISING"
                elif avg_recent < avg_old * 0.95:
                    trend = "FALLING"

        # 4. Nearby Mandis
        nearby_mandis = []
        for d_id, records in district_records.items():
            if d_id == target_source_id: continue
            if not records: continue
            
            sorted_recs = sorted(records, key=lambda x: x["date"])
            latest = sorted_recs[-1]
            
            dist_name = self._id_to_district_map.get(d_id, f"District {d_id}")
            if d_id == 0: dist_name = "State Average"
            
            nearby_mandis.append({
                "name": dist_name,
                "distance_km": 50, # Placeholder
                "price_min": float(latest.get("min_price", 0)),
                "price_max": float(latest.get("max_price", 0)),
                "trend": "STABLE"
            })
            
        nearby_mandis = nearby_mandis[:5]
        
        recommendation = "Hold"
        if trend == "RISING": recommendation = "Hold (Prices Rising)"
        elif trend == "FALLING": recommendation = "Sell Now (Prices Falling)"
        else: recommendation = "Monitor Market"

        result = {
            "current_price": current_val,
            "current_price_range": current_price_range,
            "trend": trend,
            "nearby_mandis": nearby_mandis,
            "price_history": price_history,
            "recommendation": recommendation,
            "data_source": "live",
            "data_timestamp": datetime.now()
        }
        
        # Validate the response
        try:
            validated = CEDAPriceResponse(**result)
            return validated.model_dump()
        except ValidationError as e:
            logger.error(f"Validation error in CEDA response: {e}")
            # Return the unvalidated result but log the error
            # In production, you might want to return fallback data here
            return result
    
    async def _validate_and_return(self, data: Dict[str, Any], crop: str, location: str) -> Dict[str, Any]:
        """Validate response data and return fallback if validation fails."""
        try:
            validated = CEDAPriceResponse(**data)
            return validated.model_dump()
        except ValidationError as e:
            logger.error(f"Validation error in CEDA response for {crop} in {location}: {e}")
            return await self._get_fallback_price(crop, location)

    async def _get_fallback_price(self, crop: str, location: str) -> Dict[str, Any]:
        """Return cached data if available, otherwise mock data for prototype."""
        # First, try to get any cached price data for this crop
        # Search cache for any price data matching this crop
        cache_stats = self.cache.get_stats()
        
        # Try to find cached data by searching through cache keys
        # This is a simple implementation - in production, use a more sophisticated cache query
        for key in list(self.cache.cache.iterkeys()):
            if key.startswith("price:") and crop.lower() in key.lower():
                cached_data = await self.cache.get(key)
                if cached_data:
                    logger.info(f"Using cached fallback data for {crop}")
                    cached_data["data_source"] = "cached"
                    # Validate before returning
                    try:
                        validated = CEDAPriceResponse(**cached_data)
                        return validated.model_dump()
                    except ValidationError as e:
                        logger.error(f"Validation error in cached fallback data: {e}")
                        # Continue to generate synthetic fallback
        
        # No cached data available, generate synthetic fallback
        logger.warning(f"Generating synthetic fallback data for {crop} in {location}")
        
        base_price = 2000 # per quintal
        if crop.lower() == "tomato": base_price = 1500
        if crop.lower() == "onion": base_price = 2500
        
        variation = random.randint(-200, 200)
        current = base_price + variation
        
        # Generate synthetic history
        history = []
        today = datetime.now()
        for i in range(30):
            d = today - timedelta(days=30-i)
            p_base = base_price + random.randint(-300, 300)
            history.append({
                "commodity_id": 0,
                "commodity_name": crop,
                "min_price": p_base - 100,
                "max_price": p_base + 100,
                "modal_price": p_base,
                "date": d.strftime("%Y-%m-%d")
            })
        
        fallback_data = {
            "current_price": current,
            "current_price_range": (current - 100, current + 100),
            "trend": random.choice(["RISING", "STABLE", "FALLING"]),
            "nearby_mandis": [
                {"name": f"{location} Mandi", "price_min": current-50, "price_max": current+50, "distance_km": 5, "trend": "STABLE"},
                {"name": "District HQ Mandi", "price_min": current, "price_max": current+100, "distance_km": 45, "trend": "STABLE"}
            ],
            "price_history": history,
            "recommendation": "Hold for 2 days" if current < base_price else "Sell Now",
            "data_source": "fallback",
            "data_timestamp": datetime.now()
        }
        
        # Validate fallback data
        try:
            validated = CEDAPriceResponse(**fallback_data)
            return validated.model_dump()
        except ValidationError as e:
            logger.error(f"Validation error in synthetic fallback data: {e}")
            # Return unvalidated data as last resort
            return fallback_data

ceda_service = CedaPriceService()
