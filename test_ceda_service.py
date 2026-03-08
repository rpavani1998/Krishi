import asyncio
import os
from datetime import date
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Load env vars
load_dotenv()

# Import the service
from app.services.ceda_service import CedaPriceService

async def main():
    print("--- Testing CedaPriceService ---")
    
    # Initialize service
    service = CedaPriceService()
    
    # Test parameters
    crop = "Tomato"
    location = "Andhra Pradesh"
    harvest_date = date(2023, 10, 15) # Using a date in 2023 where we know data exists
    
    print(f"Fetching price trends for {crop} in {location} around {harvest_date}...")
    
    try:
        result = await service.get_price_trends(crop, location, harvest_date)
        
        print("\n--- Result ---")
        print(f"Current Price Range: {result.get('current_price_range')}")
        print(f"Trend: {result.get('trend')}")
        print(f"Nearby Mandis: {len(result.get('nearby_mandis', []))}")
        
        if result.get('nearby_mandis'):
            print("Sample Mandi Data:", result['nearby_mandis'][0])
            
        # Check if it's mock data
        if result.get('current_price_range') == (1500, 2200) and result.get('trend') == "STABLE":
            print("\nWARNING: It looks like FALLBACK/MOCK data was returned.")
        else:
            print("\nSUCCESS: Real data seems to be returned (values differ from default mock).")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
