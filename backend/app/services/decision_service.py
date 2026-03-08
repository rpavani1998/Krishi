from typing import Dict, List, Any, Optional
from app.models.harvest import HarvestInput, Scenario, HarvestDecision
import logging

logger = logging.getLogger(__name__)

class DecisionService:
    def __init__(self):
        # Simple Spoilage Model (Risk per day)
        # Based on storage condition: "open" is baseline, "covered" reduces by 50%
        self.CROP_SPOILAGE = {
            "Tomato": 0.15,  # 15% per day if open
            "Onion": 0.02,
            "Chillies": 0.05,
            "Paddy": 0.01,
            "Cotton": 0.01
        }

    def evaluate(self, input_data: HarvestInput, price_data: Dict[str, Any], weather_data: Dict[str, Any], language: str = 'en') -> HarvestDecision:
        """
        Generate decision scenarios based on inputs.
        """
        # 2. Analyze Risks
        spoilage_risk_base = self.CROP_SPOILAGE.get(input_data.crop, 0.05)
        if input_data.storage_condition == "covered":
            spoilage_risk_base *= 0.5
        elif input_data.storage_condition == "cold_storage":
            spoilage_risk_base *= 0.1

        forecast = weather_data.get("forecast", {})
        rain_risk_24h = forecast.get("rain_risk_24h", False)
        rain_risk_48h = forecast.get("rain_risk_48h", False)
        
        weather_risk_24h = "HIGH" if rain_risk_24h else "LOW"
        weather_risk_48h = "HIGH" if rain_risk_48h else "LOW"
        
        # Localize weather summary
        weather_summary = f"Rain risk in 24h: {weather_risk_24h}, 48h: {weather_risk_48h}"
        if language == 'te':
             w24 = "ఎక్కువ" if rain_risk_24h else "తక్కువ"
             w48 = "ఎక్కువ" if rain_risk_48h else "తక్కువ"
             weather_summary = f"వర్ష సూచన (24గం): {w24}, (48గం): {w48}"
        elif language == 'hi':
             w24 = "अधिक" if rain_risk_24h else "कम"
             w48 = "अधिक" if rain_risk_48h else "कम"
             weather_summary = f"बारिश का जोखिम (24घं): {w24}, (48घं): {w48}"

        price_trend = price_data.get("trend", "STABLE")
        current_price_range = price_data.get("current_price_range", (0, 0))
        
        # 3. Generate Scenarios
        
        # Scenario A: Sell Now
        sell_now = self._create_sell_now_scenario(
            input_data, current_price_range, weather_risk_24h
        )
        
        # Calculate baseline revenue for comparison
        baseline_revenue = 0
        if sell_now:
            baseline_revenue = (sell_now.expected_revenue_range[0] + sell_now.expected_revenue_range[1]) / 2
        
        # Scenario B: Wait 24h
        wait_24h = self._create_wait_scenario(
            input_data, 
            duration_hours=24,
            current_price_range=current_price_range,
            price_trend=price_trend,
            spoilage_rate=spoilage_risk_base,
            weather_risk=weather_risk_24h,
            baseline_revenue=baseline_revenue
        )

        # Scenario C: Wait 48h
        wait_48h = self._create_wait_scenario(
            input_data,
            duration_hours=48,
            current_price_range=current_price_range,
            price_trend=price_trend,
            spoilage_rate=spoilage_risk_base,
            weather_risk=weather_risk_48h,
            baseline_revenue=baseline_revenue
        )

        # Determine Recommendation
        recommendation = "sell_now"
        # If any wait scenario has significantly higher revenue (>10%) and manageable risk, recommend wait
        wait_24h_rev = (wait_24h.expected_revenue_range[0] + wait_24h.expected_revenue_range[1]) / 2
        wait_48h_rev = (wait_48h.expected_revenue_range[0] + wait_48h.expected_revenue_range[1]) / 2
        
        if wait_24h_rev > baseline_revenue * 1.1 and weather_risk_24h != "HIGH":
            recommendation = "wait"
            wait_24h.tag = "Recommended"
            sell_now.tag = "Low Reward"
        elif wait_48h_rev > baseline_revenue * 1.15 and weather_risk_48h != "HIGH":
            recommendation = "wait"
            wait_48h.tag = "Recommended"
            sell_now.tag = "Low Reward"
        else:
            sell_now.tag = "Recommended"
            wait_24h.tag = "High Risk" if weather_risk_24h == "HIGH" else "Low Reward"

        return HarvestDecision(
            scenarios=[sell_now, wait_24h, wait_48h],
            market_intelligence={
                "nearby_mandis": price_data.get("nearby_mandis", []),
                "trend": price_trend,
                "recommendation": price_data.get("recommendation", "N/A")
            },
            weather_summary=weather_summary,
            recommendation=recommendation
        )

    def _create_sell_now_scenario(self, input: HarvestInput, price_range, weather_risk):
        min_rev = input.quantity * price_range[0]
        max_rev = input.quantity * price_range[1]
        
        description = "Sell at current market price."
        if weather_risk == "HIGH":
            description += " Avoids high rain risk."
        else:
            description += " Safe option to secure cash."

        return Scenario(
            id="sell_now",
            title="Sell Immediately",
            description=description,
            risk_assessment={
                "spoilage": "LOW",
                "weather": weather_risk,
                "price": "LOW" # No price risk as selling now
            },
            price_projection="STABLE",
            expected_revenue_range=(min_rev, max_rev),
            loss_reduction_actions=[
                "Transport during cooler hours (early morning)",
                "Use proper crates to minimize transit damage"
            ],
            uncertainty_factors=[
                "Exact mandi arrival volume unknown"
            ],
            upside="Secure cash flow immediately",
            downside="Miss potential price rise",
            tag="Safe Bet"
        )

    def _create_wait_scenario(self, input: HarvestInput, duration_hours: int, current_price_range, price_trend, spoilage_rate, weather_risk, baseline_revenue: float):
        days = duration_hours / 24
        spoilage_loss = input.quantity * (spoilage_rate * days)
        remaining_qty = input.quantity - spoilage_loss
        
        # Price projection logic
        price_factor = 1.0
        if price_trend == "RISING":
            price_factor = 1.05 + (0.02 * days) # +5% base + 2% per day
        elif price_trend == "FALLING":
            price_factor = 0.90 - (0.02 * days) # -10% base - 2% per day
            
        future_min = current_price_range[0] * price_factor
        future_max = current_price_range[1] * price_factor
        
        min_rev = remaining_qty * future_min
        max_rev = remaining_qty * future_max
        avg_rev = (min_rev + max_rev) / 2
        
        diff = avg_rev - baseline_revenue
        upside = None
        downside = None
        tag = "Neutral"

        if diff > 0:
            upside = f"+₹{int(diff):,} Profit vs Now"
            tag = "High Reward"
        else:
            downside = f"-₹{int(abs(diff)):,} Loss vs Now"
            tag = "High Risk"
            
        if weather_risk == "HIGH":
             downside = "High Rain Risk"
             tag = "High Risk"
        
        title = f"Wait {duration_hours} Hours"
        description = f"Store crop for {days} days. "
        
        # Add Price Context
        if price_trend == "RISING":
            description += "Prices expected to rise (+5%). "
        elif price_trend == "FALLING":
            description += "Prices falling (High Risk). "
        else:
            description += "Market is stable. "
            
        # Add Weather Context
        if weather_risk == "HIGH":
            description += "Warning: High chance of rain."
        else:
            description += "Weather looks clear."

        return Scenario(
            id=f"wait_{duration_hours}h",
            title=title,
            description=description,
            risk_assessment={
                "spoilage": "HIGH" if spoilage_rate > 0.05 else "MEDIUM",
                "weather": weather_risk,
                "price": "HIGH" if price_trend == "FALLING" else "MEDIUM"
            },
            price_projection=price_trend,
            expected_revenue_range=(min_rev, max_rev),
            loss_reduction_actions=[
                "Ensure proper ventilation in storage",
                "Monitor for rot daily"
            ],
            uncertainty_factors=[
                "Unexpected rain could increase spoilage",
                "Market arrivals may fluctuate"
            ],
            upside=upside,
            downside=downside,
            tag=tag
        )

    def generate_recommendation_text(self, decision: HarvestDecision, lang: str = 'en') -> str:
        recommended_scenario = next((s for s in decision.scenarios if s.tag == "Recommended"), None)

        if not recommended_scenario:
            if lang == 'te':
                return "ఒక స్పష్టమైన సిఫార్సును గుర్తించడం సాధ్యం కాలేదు. దయచేసి దృశ్యాలను జాగ్రత్తగా సమీక్షించండి."
            if lang == 'hi':
                return "एक स्पष्ट सिफारिश निर्धारित करने में असमर्थ। कृपया परिदृश्यों की सावधानीपूर्वक समीक्षा करें।"
            return "Unable to determine a clear recommendation. Please review the scenarios carefully."

        if recommended_scenario.id == 'sell_now':
            reason = "to lock in current profits and avoid potential losses from price drops or spoilage."
            if decision.market_intelligence.get('trend') == "FALLING":
                reason = "as market prices are currently falling."
            if recommended_scenario.risk_assessment.get('weather') == "HIGH":
                reason += " Additionally, there is a high risk of rain which could damage your crop."

            if lang == 'te':
                return f"ప్రస్తుత మార్కెట్ పోకడలు మరియు వాతావరణ సూచనల ఆధారంగా, మీ పంటను ఇప్పుడు అమ్ముకోవడం మంచిది, ఎందుకంటే మార్కెట్ ధరలు ప్రస్తుతం తగ్గుతున్నాయి."
            if lang == 'hi':
                return f"मौजूदा बाजार के रुझानों और मौसम के पूर्वानुमान के आधार पर, अपनी फसल को अभी बेचना उचित है क्योंकि बाजार की कीमतें गिर रही हैं।"
            return f"Based on current market trends and weather forecasts, it is advisable to sell your crop now {reason}"
        else:
            wait_hours = recommended_scenario.id.split('_')[1].replace('h','')
            market_trend_info = ""
            if decision.market_intelligence.get('trend') == "RISING":
                market_trend_info = "The market trend is favorable with prices expected to rise."

            if lang == 'te':
                return f"మార్కెట్ అనుకూలంగా ఉంది. {wait_hours} గంటలు వేచి ఉండటం మంచిది, ఇది మీకు మంచి ధరను పొందే అవకాశం ఉంది. అయితే, వాతావరణం మరియు మార్కెట్ మార్పులను గమనిస్తూ ఉండండి."
            if lang == 'hi':
                return f"बाजार का रुझान अनुकूल है। {wait_hours} घंटे इंतजार करने की सलाह दी जाती है ताकि बेहतर कीमत मिल सके। हालांकि, मौसम और बाजार में होने वाले बदलावों पर नजर रखें।"
            
            return f"{market_trend_info} It is recommended to wait for {wait_hours} hours before selling to potentially get a better price. However, keep an eye on the weather and market changes."


decision_service = DecisionService()
