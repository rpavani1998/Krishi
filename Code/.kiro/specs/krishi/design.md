# Design Document: Krishi – Agricultural Decision Copilot

---

## 1. Executive Summary

Krishi is a channel-neutral agricultural decision copilot that supports farmers from planting to selling. The system provides three core capabilities:

1. **Selling Copilot (MVP)**: Explains selling scenarios, risks, and trade-offs at harvest time
2. **Market Intelligence (Phase 2)**: Provides social proof, transaction intelligence, demand signals, network transparency, and channel reliability scoring
3. **Crop Planning (Phase 3)**: Comprehensive crop exploration hub with investment calculator, ROI projections, cultivation requirements, value addition opportunities, and industry connections

**Core Principles**:
- Explain outcomes, not instructions
- Present risks before prices
- Communicate uncertainty clearly
- Preserve farmer autonomy
- Maintain channel neutrality
- Voice-first, regional language

**MVP Scope**:
- Single district, regional language (Telugu)
- Voice-first (phone IVR + in-app voice) with text fallback
- 100-500 farmers via 1-2 FPOs
- 4-week validation period
- ₹25,000-45,000/month operating cost

**Phase 2 Enhancements**:
- Recent transaction intelligence (5-10 transactions, anonymized)
- Active demand signals from verified buyers
- Network visualization with reliability scoring
- Enhanced scenarios with real examples and contact info
- Alternative pathway calculation with cost breakdowns
- Transaction data collection and sharing (opt-in)
- Buyer demand submission and verification
- Channel reliability scoring and feedback system

**Phase 3 Enhancements**:
- Crop information hub (seasonal demand, regional trends, peer activity)
- Investment calculator with detailed cost breakdown
- ROI projections with risk assessment
- Cultivation requirements and land suitability analysis
- Alternate uses and value addition opportunities
- Industry applications and premium market access
- Voice-enabled crop exploration and planning
- Voice-based outcome feedback and experience sharing

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Users                                       │
│  Farmers │ FPOs │ Aggregators │ Traders │ Mandis │ Processors          │
└──────────────┬──────────────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────────────┐
│              Client Layer (Voice-First + Multi-Channel)                  │
│  • Phone IVR (Amazon Connect) - toll-free number                         │
│  • Android App (Voice + Text + Offline) - primary interface             │
│  • SMS/WhatsApp (Text) - feature phone support                          │
│  • Voice UI Components (mic buttons, waveform, transcription)           │
└──────────────┬──────────────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────────────┐
│         Voice & API Gateway Layer                                        │
│  • Amazon Transcribe (Speech-to-Text, Telugu)                           │
│  • Amazon Polly (Text-to-Speech, Telugu, natural voice)                 │
│  • Amazon Lex (Dialogue Management, intent recognition)                 │
│  • AWS API Gateway (REST APIs for all features)                         │
│  • Amazon Cognito (Phone OTP Authentication)                            │
└──────────────┬──────────────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────────────┐
│           Application Services (AWS Lambda - Python 3.11)                │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ MVP Services:                                                     │   │
│  │  - Scenario Generation Engine                                    │   │
│  │  - Risk Assessment Calculator                                    │   │
│  │  - Channel Information Provider                                  │   │
│  │  - Offline Sync Manager                                          │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │ Phase 2 Services:                                                │   │
│  │  - Transaction Intelligence Aggregator                           │   │
│  │  - Demand Signal Matcher                                         │   │
│  │  - Network Visualization Builder                                 │   │
│  │  - Reliability Scoring Engine                                    │   │
│  │  - Alternative Pathway Calculator                                │   │
│  │  - Buyer Verification Service                                    │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │ Phase 3 Services:                                                │   │
│  │  - Seasonal Demand Analyzer                                      │   │
│  │  - Investment Calculator                                         │   │
│  │  - ROI Projection Engine                                         │   │
│  │  - Land Suitability Checker                                      │   │
│  │  - Value Addition Recommender                                    │   │
│  │  - Industry Buyer Connector                                      │   │
│  │  - Voice Query Processor                                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────┬──────────────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────────────┐
│              Reasoning & Intelligence Layer                              │
│  • Rule-Based Logic (MVP) - price trends, spoilage, weather             │
│  • ML Models (Phase 2+) - demand prediction, price forecasting          │
│  • AWS Bedrock (Claude Haiku) - explanation generation in Telugu        │
│  • Reliability Scoring Algorithm - multi-factor channel scoring         │
│  • Suitability Matching Engine - crop-land compatibility                │
└──────────────┬──────────────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────────────────┐
│              Data Layer                                                  │
│  • DynamoDB (on-demand):                                                 │
│    - Market data, price history                                          │
│    - Transactions (anonymized)                                           │
│    - Demand signals                                                      │
│    - Outcome tracking                                                    │
│    - Feedback and ratings                                                │
│  • RDS PostgreSQL (t3.micro):                                            │
│    - Farmer profiles                                                     │
│    - Crop profiles (detailed)                                            │
│    - Channel profiles                                                    │
│    - Buyer profiles                                                      │
│    - Industry buyer database                                             │
│  • ElastiCache Redis (t3.micro):                                         │
│    - Market data cache (5 min)                                           │
│    - Crop profile cache (24 hr)                                          │
│    - Channel info cache (1 hr)                                           │
│    - Demand signal cache (6 hr)                                          │
│  • S3 (Standard):                                                        │
│    - Call recordings (encrypted)                                         │
│    - Historical data archives                                            │
│    - Voice feedback recordings                                           │
│    - Training data for ML                                                │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

**Frontend**:
- Android (Kotlin) with offline-first architecture
- SQLite for local storage (7-day market data cache)
- Voice input/output capabilities (Transcribe/Polly integration)
- Regional language support (Telugu with local agricultural terms)
- Material Design UI with voice UI components

**Backend**:
- AWS Lambda (Python 3.11) - serverless compute, auto-scaling
- AWS API Gateway - REST APIs with throttling and caching
- Amazon Cognito - phone OTP authentication, session management

**Voice Services**:
- Amazon Connect - IVR system, call routing, concurrent call handling
- Amazon Transcribe - speech-to-text (Telugu, 85%+ accuracy target)
- Amazon Polly - text-to-speech (Telugu, natural voice, appropriate pace)
- Amazon Lex - dialogue management, intent recognition, context preservation

**Data Storage**:
- DynamoDB (on-demand) - market data, transactions, demand signals, feedback
- RDS PostgreSQL (t3.micro) - farmer profiles, crop data, channel profiles
- ElastiCache Redis (t3.micro) - aggressive caching for cost optimization
- S3 (Standard) - call recordings, historical data, voice feedback

**AI/ML**:
- AWS Bedrock (Claude Haiku) - explanation generation in Telugu
- Simple rule-based models (MVP) - price trends, spoilage risk
- ML models for predictions (Phase 2+) - demand forecasting, price prediction

**Monitoring & Operations**:
- CloudWatch - logs, metrics, alarms
- SNS - notifications, SMS delivery
- CloudFront - static asset delivery
- AWS CDK (Python) - infrastructure as code

---

## 3. Feature Design

### 3.1 MVP: Selling Copilot

#### 3.1.1 Voice-First Farmer Input

**Purpose**: Capture harvest details through voice or text

**Voice Flow**:
1. Farmer calls toll-free number or opens app
2. System greets in Telugu: "నమస్కారం, కృషి కి స్వాగతం" (Hello, welcome to Krishi)
3. System asks for crop details through natural dialogue
4. Farmer provides: crop type, quantity, location, harvest date, storage
5. System confirms understanding by repeating key details
6. System generates scenarios

**Input Fields**:
- Crop type (voice/text selection from predefined list)
- Quantity (quintals/kg with voice number recognition)
- Location (village/mandal with voice recognition)
- Harvest date (today/yesterday/specific date)
- Storage conditions (open/covered/cold storage)

**Voice Recognition**:
- Target accuracy: 85%+ for Telugu agricultural terms
- Noise cancellation for field environments
- Fallback to text input when confidence < 70%
- Clarifying questions for ambiguous input

**Text Fallback**:
- Android app text input fields
- SMS/WhatsApp structured format
- Form validation with Telugu error messages

#### 3.1.2 Scenario-Based Reasoning Engine

**Purpose**: Generate "sell now" vs "wait" scenarios with risk-first explanations

**Scenario Types**:
1. **Sell Now**: Immediate sale with current market conditions
2. **Wait 24h**: Short wait with updated projections
3. **Wait 48h**: Medium wait with risk assessment
4. **Wait 72h**: Maximum wait window with high uncertainty

**Scenario Components**:
1. **Key Risks** (presented first):
   - Spoilage risk (LOW/MEDIUM/HIGH with percentage)
   - Weather risk (rain forecast, temperature)
   - Transport availability
   - Price volatility

2. **Possible Outcomes**:
   - Best case (high yield + high price)
   - Likely case (average yield + average price)
   - Worst case (low yield + low price)

3. **Loss-Reduction Actions**:
   - Practical steps (drying, storage, handling)
   - Local cost ranges in rupees
   - Implementation guidance in Telugu

4. **Uncertainty Statements**:
   - What we don't know
   - Data age indicators
   - Confidence levels

**Reasoning Logic (MVP - Rule-Based)**:
```python
# Price Trend Analysis
price_trend = calculate_7day_moving_average(crop_id, mandal_id)
if price_trend > 0.05:  # 5% increase
    trend = "rising"
elif price_trend < -0.05:  # 5% decrease
    trend = "falling"
else:
    trend = "stable"

# Spoilage Risk Calculation
spoilage_risk = get_crop_spoilage_rate(crop_id, storage_condition, days_since_harvest)
if spoilage_risk > 0.15:  # 15% loss
    risk_level = "HIGH"
elif spoilage_risk > 0.08:  # 8% loss
    risk_level = "MEDIUM"
else:
    risk_level = "LOW"

# Weather Risk Assessment
weather_forecast = get_3day_forecast(location)
if weather_forecast.rain_probability > 0.6:
    weather_risk = "HIGH"
elif weather_forecast.rain_probability > 0.3:
    weather_risk = "MEDIUM"
else:
    weather_risk = "LOW"

# Transport Availability
transport_score = check_transport_availability(location, day_of_week)
```

**Example Scenario Output**:
```
విక్రయించండి ఇప్పుడు (Sell Now):

రిస్క్ అంచనా (Risk Assessment):
🔴 చెడిపోవు ప్రమాదం: తక్కువ (5-10%)
🟢 వాతావరణం: మంచిది (వర్షం అవకాశం తక్కువ)
🟢 రవాణా: అందుబాటులో ఉంది
🟡 ధర: స్థిరంగా ఉంది

ధర అంచనా: ₹18-22/kg
మీ 50 క్వింటాల్స్ కు నికర ఆదాయం: ₹90,000-1,10,000

నష్టం తగ్గించే చర్యలు:
1. ఉదయం పంట కోయండి (వేడి తగ్గుతుంది)
2. నీడలో 2-3 గంటలు ఆరబెట్టండి (₹50-100)
3. ప్లాస్టిక్ క్రేట్లు ఉపయోగించండి (₹200-300)

అనిశ్చితం:
- రేపు ధర మారవచ్చు (డేటా 1 రోజు పాతది)
- మండి రద్దీ తెలియదు
```

#### 3.1.3 Channel-Neutral Information Provision

**Purpose**: Provide unbiased information about all selling options

**Channel Types**:
1. **Mandis (APMC Markets)**:
   - Location and distance
   - Typical price ranges (last 7 days)
   - Commission structure (2-5%)
   - Payment terms (same day)
   - Operating days and hours
   - Quality grading process

2. **Aggregators**:
   - Operating regions
   - Crops of interest
   - Price ranges (typically 5-10% below mandi)
   - Commission (5-10%)
   - Payment terms (1-3 days)
   - Pickup service availability

3. **Traders (Commission Agents)**:
   - Specialization (specific crops)
   - Price ranges
   - Commission (3-7%)
   - Payment terms (immediate to 7 days)
   - Relationship-based pricing

4. **Direct Buyers (Processors/Exporters)**:
   - Company name and location
   - Quality requirements
   - Price premiums (10-30% above market)
   - Payment terms (varies)
   - Minimum quantity requirements
   - Contract farming opportunities

**Neutrality Implementation**:
- No ranking or recommendations
- Equal prominence for all channels
- Factual information only
- No financial relationships
- Transparent about data sources
- Clear communication of neutrality to farmers

**Channel Information Display**:
```
అమ్మకపు మార్గాలు (Selling Channels):

1. పులివెందుల మండి (Pulivendula Mandi)
   దూరం: 8 km
   ధర: ₹19-21/kg (గత వారం)
   కమిషన్: 3%
   చెల్లింపు: అదే రోజు
   
2. స్థానిక అగ్రిగేటర్ (Local Aggregator)
   దూరం: 3 km
   ధర: ₹18-20/kg
   కమిషన్: 7%
   చెల్లింపు: 2 రోజులు
   పికప్: అవును
   
3. ఆహార ప్రాసెసర్ (Food Processor)
   దూరం: 15 km
   ధర: ₹22-24/kg (Grade A)
   కమిషన్: లేదు
   చెల్లింపు: 3 రోజులు
   కనీస పరిమాణం: 100 క్వింటాల్స్
```

#### 3.1.4 Offline-First Mobile Architecture

**Purpose**: Work without internet connectivity in rural areas

**Offline Capabilities**:
1. **Data Input**: Capture harvest details offline
2. **Scenario Generation**: Use cached market data (7-day history)
3. **Channel Information**: View cached channel details (30-day cache)
4. **Historical Data**: Access past scenarios and outcomes

**Cache Strategy**:
```
SQLite Local Database:
- market_data (7 days, updated daily when online)
- crop_spoilage_models (permanent, updated monthly)
- weather_patterns (3 days, updated when online)
- channel_information (30 days, updated weekly)
- farmer_profile (permanent, synced when online)
- past_scenarios (permanent, synced when online)
```

**Sync Logic**:
1. **Background Sync**: Automatic when connectivity detected
2. **Priority Order**:
   - Market data (highest priority)
   - Outcome data
   - Profile updates
   - Historical data
3. **Conflict Resolution**: Server data wins
4. **Sync Indicators**: Visual feedback on data freshness

**Data Freshness Indicators**:
```
✓ తాజా డేటా (Fresh data - < 6 hours)
⚠ పాత డేటా (Old data - 6-24 hours)
❌ చాలా పాత డేటా (Very old data - > 24 hours)

Example: "మార్కెట్ డేటా: 2 రోజుల క్రితం" (Market data: 2 days ago)
```

#### 3.1.5 Transparent Uncertainty Communication

**Purpose**: Build trust through honesty about limitations

**Uncertainty Patterns**:
1. **Data Quality Issues**:
   - "మాకు తాజా డేటా లేదు" (We don't have fresh data)
   - "ఈ సమాచారం 3 రోజుల పాతది" (This information is 3 days old)

2. **Incomplete Information**:
   - "మండి రద్దీ గురించి మాకు తెలియదు" (We don't know about mandi crowd)
   - "రవాణా ఖర్చు మారవచ్చు" (Transport cost may vary)

3. **Volatile Conditions**:
   - "ధర అస్థిరంగా ఉంది, మారవచ్చు" (Price is volatile, may change)
   - "వాతావరణం అనిశ్చితం" (Weather is uncertain)

4. **Prediction Limitations**:
   - "ఇది మా అంచనా మాత్రమే" (This is only our estimate)
   - "నిజమైన ధర భిన్నంగా ఉండవచ్చు" (Actual price may differ)

**Uncertainty Levels**:
- **HIGH**: Multiple data gaps, volatile conditions, low confidence
- **MEDIUM**: Some data gaps, moderate volatility, medium confidence
- **LOW**: Good data quality, stable conditions, high confidence

**Implementation**:
```python
def add_uncertainty_statements(scenario, data_quality, market_volatility):
    statements = []
    
    if data_quality.age_hours > 48:
        statements.append(f"మార్కెట్ డేటా {data_quality.age_hours//24} రోజుల పాతది")
    
    if market_volatility > 0.15:  # 15% price variation
        statements.append("ధర అస్థిరంగా ఉంది, జాగ్రత్తగా నిర్ణయించండి")
    
    if not weather_data_available:
        statements.append("వాతావరణ సమాచారం అందుబాటులో లేదు")
    
    scenario.uncertainty_statements = statements
    scenario.confidence_level = calculate_confidence(data_quality, market_volatility)
```

---


### 3.2 Phase 2: Market Intelligence and Network Transparency

Phase 2 enhances the MVP with social proof, transaction intelligence, demand signals, network visualization, and channel reliability scoring.

#### 3.2.1 Recent Transaction Intelligence

**Purpose**: Provide farmers with real transaction data from nearby farmers to set realistic price expectations

**Data Model**:
```python
class Transaction:
    id: UUID
    crop_id: str
    crop_name: str
    quantity_quintals: float
    price_per_quintal: float
    channel_type: str  # mandi/aggregator/trader/direct
    channel_name: str
    location_village: str
    location_mandal: str
    transaction_date: datetime
    quality_grade: str  # A/B/C
    payment_received_date: datetime
    deductions_amount: float
    transport_cost: float
    farmer_reference: str  # anonymized: "Farmer from Pulivendula"
    satisfaction_rating: int  # 1-5
    created_at: datetime
    data_age_days: int  # calculated field
```

**API Endpoints**:
```
GET /api/v1/transactions/recent
Query params:
  - crop_id: required
  - mandal_id: required
  - radius_km: optional (default 50)
  - days: optional (default 14)
  - limit: optional (default 10)

Response:
{
  "transactions": [Transaction],
  "summary": {
    "avg_price": float,
    "min_price": float,
    "max_price": float,
    "most_common_channel": str,
    "total_count": int
  }
}
```

**Aggregation Logic**:
```python
def get_recent_transactions(crop_id, mandal_id, radius_km=50, days=14, limit=10):
    # Query transactions within geographic radius
    transactions = db.query(Transaction).filter(
        Transaction.crop_id == crop_id,
        Transaction.transaction_date >= datetime.now() - timedelta(days=days),
        Transaction.location_mandal.in_(get_nearby_mandals(mandal_id, radius_km))
    ).order_by(Transaction.transaction_date.desc()).limit(limit).all()
    
    # Calculate summary statistics
    prices = [t.price_per_quintal for t in transactions]
    summary = {
        "avg_price": sum(prices) / len(prices) if prices else 0,
        "min_price": min(prices) if prices else 0,
        "max_price": max(prices) if prices else 0,
        "most_common_channel": mode([t.channel_type for t in transactions]),
        "total_count": len(transactions)
    }
    
    # Add data age indicator
    for t in transactions:
        t.data_age_days = (datetime.now() - t.transaction_date).days
    
    return transactions, summary
```

**Privacy Implementation**:
- Remove all PII (name, phone, exact address) before storage
- Replace with anonymized reference: "Farmer from {village_name}"
- Store only village-level location, not exact coordinates
- Farmers can delete their data anytime via API

**Voice Output Format**:
```
"గత వారంలో 8 మంది రైతులు టమాటాలను క్వింటాల్‌కు ₹800-₹1200 కు అమ్మారు. 
సగటు ధర ₹950. చాలా మంది మండి ద్వారా అమ్మారు."

(In the last week, 8 farmers sold tomatoes for ₹800-₹1200 per quintal.
Average price ₹950. Most sold through mandi.)
```

#### 3.2.2 Demand Intelligence System

**Purpose**: Connect farmers with active buyers through verified demand signals

**Data Model**:
```python
class DemandSignal:
    id: UUID
    buyer_id: UUID
    buyer_type: str  # aggregator/processor/exporter/trader
    buyer_name: str
    crop_id: str
    quantity_needed_quintals: float
    price_range_min: float
    price_range_max: float
    location_village: str
    location_mandal: str
    location_lat: float
    location_lon: float
    urgency: str  # URGENT/THIS_WEEK/THIS_MONTH
    quality_requirements: dict  # {grade, moisture_pct, size}
    payment_terms: str  # immediate/7days/15days/30days
    validity_end_date: datetime
    contact_phone: str
    contact_whatsapp: str
    verified: bool
    verification_date: datetime
    fulfillment_status: str  # active/partially_fulfilled/completed/expired
    created_at: datetime
    updated_at: datetime
```

**Buyer Verification Process**:
```python
def verify_buyer(buyer_id):
    # Step 1: Phone verification (OTP)
    send_otp(buyer.phone)
    verify_otp(buyer.phone, otp_code)
    
    # Step 2: Business registration check
    business_doc = upload_business_registration()
    validate_business_doc(business_doc)
    
    # Step 3: FPO validation or farmer references
    fpo_validation = check_fpo_partnership(buyer_id)
    farmer_refs = get_farmer_references(buyer_id, min_count=3)
    
    # Step 4: Physical address verification
    verify_address(buyer.address)
    
    # Mark as verified
    buyer.verified = True
    buyer.verification_date = datetime.now()
    buyer.reliability_score = calculate_initial_score()
```

**Demand Matching Algorithm**:
```python
def match_demand_signals(farmer_crop, farmer_quantity, farmer_location, radius_km=50):
    # Get active demand signals within radius
    demands = db.query(DemandSignal).filter(
        DemandSignal.crop_id == farmer_crop,
        DemandSignal.fulfillment_status == 'active',
        DemandSignal.validity_end_date >= datetime.now(),
        DemandSignal.verified == True,
        distance(DemandSignal.location, farmer_location) <= radius_km
    ).all()
    
    # Score and rank demands
    scored_demands = []
    for demand in demands:
        score = calculate_demand_score(demand, farmer_quantity, farmer_location)
        scored_demands.append((demand, score))
    
    # Sort by score (descending)
    scored_demands.sort(key=lambda x: x[1], reverse=True)
    
    return [d[0] for d in scored_demands]

def calculate_demand_score(demand, farmer_quantity, farmer_location):
    # Scoring factors with weights
    proximity_score = 1 - (distance(demand.location, farmer_location) / 50)  # 30%
    price_score = (demand.price_range_max - market_avg_price) / market_avg_price  # 25%
    urgency_score = {'URGENT': 1.0, 'THIS_WEEK': 0.7, 'THIS_MONTH': 0.4}[demand.urgency]  # 20%
    reliability_score = demand.buyer.reliability_score / 5.0  # 15%
    payment_score = {'immediate': 1.0, '7days': 0.8, '15days': 0.6, '30days': 0.4}[demand.payment_terms]  # 10%
    
    # Quantity match bonus
    quantity_match = 1.0 if abs(demand.quantity_needed - farmer_quantity) / farmer_quantity < 0.3 else 0.8
    
    total_score = (
        proximity_score * 0.30 +
        price_score * 0.25 +
        urgency_score * 0.20 +
        reliability_score * 0.15 +
        payment_score * 0.10
    ) * quantity_match
    
    return total_score
```

**API Endpoints**:
```
GET /api/v1/demand-signals/active
Query params:
  - crop_id: required
  - farmer_location: required (lat,lon)
  - farmer_quantity: required
  - radius_km: optional (default 50)

Response:
{
  "demands": [DemandSignal],
  "matched_count": int,
  "recommendations": [
    {
      "demand": DemandSignal,
      "match_score": float,
      "match_reason": str,
      "estimated_earnings": float
    }
  ]
}

POST /api/v1/demand-signals
Body: DemandSignal (buyer creates demand)

PUT /api/v1/demand-signals/{id}/status
Body: {status: "partially_fulfilled" | "completed"}
```

**Voice Output Format**:
```
"పులివెందుల లో ఒక ఎగ్జిపోర్టర్ 50 క్వింటాల్ టమాటాలు కావాలి. 
క్వింటాల్‌కు ₹1000-₹1200 ఇస్తారు. 
3 రోజుల్లో చెల్లింపు. 
ఫోన్: 9876543210. 
మీ పంటకు బాగా సరిపోతుంది."

(An exporter in Pulivendula needs 50 quintals of tomatoes.
Will pay ₹1000-₹1200 per quintal.
Payment in 3 days.
Phone: 9876543210.
Good match for your crop.)
```

**Spam Prevention**:
- Rate limiting: max 5 demands per buyer per week
- Verification requirements before posting
- Farmer feedback on demand quality
- Automatic suspension for repeated fake postings
- Fulfillment rate tracking (< 30% triggers flag)

#### 3.2.3 Network Visualization and Channel Discovery

**Purpose**: Help farmers discover and compare all available selling channels

**Data Model**:
```python
class Channel:
    id: UUID
    channel_type: str  # mandi/aggregator/trader/direct_buyer
    name: str
    location_village: str
    location_mandal: str
    location_lat: float
    location_lon: float
    distance_km: float  # calculated from farmer location
    
    # Pricing information
    typical_price_ranges: dict  # {crop_id: {min, max}}
    commission_pct: float
    commission_fixed: float
    
    # Operational details
    payment_terms: str
    operating_days: list  # ["Monday", "Tuesday", ...]
    operating_hours: str
    contact_phone: str
    contact_whatsapp: str
    
    # Reliability metrics
    reliability_score: float  # 0-5 stars
    total_transactions: int
    recent_activity_count: int  # last 7 days
    
    # Requirements
    minimum_quantity: float
    quality_requirements: dict
    crops_accepted: list
    
    # Status
    verified: bool
    active: bool
    created_at: datetime
    last_activity_date: datetime
```

**Channel Discovery Algorithm**:
```python
def discover_channels(farmer_location, crop_id, quantity, radius_km=100):
    # Get all channels within radius
    channels = db.query(Channel).filter(
        Channel.active == True,
        distance(Channel.location, farmer_location) <= radius_km,
        Channel.crops_accepted.contains(crop_id)
    ).all()
    
    # Calculate distance for each channel
    for channel in channels:
        channel.distance_km = calculate_distance(channel.location, farmer_location)
    
    # Filter by minimum quantity if specified
    channels = [c for c in channels if c.minimum_quantity <= quantity or c.minimum_quantity is None]
    
    # Add activity badges
    for channel in channels:
        if channel.recent_activity_count >= 5:
            channel.badges.append("Active")
        if (datetime.now() - channel.created_at).days < 30:
            channel.badges.append("New")
        if channel.total_transactions < 5:
            channel.badges.append("Unverified")
        if channel.reliability_score >= 4.0:
            channel.badges.append("Verified Buyer")
    
    return channels

def filter_channels(channels, filters):
    # Apply user-selected filters
    if filters.get('max_distance'):
        channels = [c for c in channels if c.distance_km <= filters['max_distance']]
    
    if filters.get('payment_terms'):
        channels = [c for c in channels if c.payment_terms in filters['payment_terms']]
    
    if filters.get('min_reliability'):
        channels = [c for c in channels if c.reliability_score >= filters['min_reliability']]
    
    if filters.get('price_range'):
        # Filter by price range for specific crop
        pass
    
    return channels
```

**API Endpoints**:
```
GET /api/v1/channels/discover
Query params:
  - farmer_location: required (lat,lon)
  - crop_id: required
  - quantity: required
  - radius_km: optional (default 100)
  - filters: optional (JSON)

Response:
{
  "channels": [Channel],
  "total_count": int,
  "by_type": {
    "mandi": int,
    "aggregator": int,
    "trader": int,
    "direct_buyer": int
  }
}

GET /api/v1/channels/{id}/profile
Response: Channel with full details + recent reviews
```

**Network Map Visualization**:
```javascript
// Frontend map component
function renderNetworkMap(farmer_location, channels) {
  // Center map on farmer location
  map.setCenter(farmer_location);
  
  // Add farmer marker (blue)
  addMarker(farmer_location, 'farmer', 'blue');
  
  // Add channel markers with color coding
  channels.forEach(channel => {
    const color = {
      'mandi': 'green',
      'aggregator': 'orange',
      'trader': 'purple',
      'direct_buyer': 'red'
    }[channel.channel_type];
    
    addMarker(channel.location, channel.name, color);
    
    // Add distance circle
    addCircle(channel.location, channel.distance_km);
  });
  
  // Add distance legend
  addLegend(['< 10km', '< 25km', '< 50km', '< 100km']);
}
```

#### 3.2.4 Channel Reliability Scoring System

**Purpose**: Provide farmers with trustworthy reliability scores based on aggregated feedback

**Data Model**:
```python
class ChannelFeedback:
    id: UUID
    channel_id: UUID
    farmer_id: UUID
    transaction_id: UUID
    
    # Specific ratings (1-5 scale)
    payment_timeliness_rating: int
    price_accuracy_rating: int
    quality_assessment_rating: int
    overall_satisfaction_rating: int
    
    # Detailed feedback
    payment_on_time: bool
    payment_delay_days: int
    price_matched_quote: bool
    price_difference_amount: float
    quality_assessment_fair: bool
    would_sell_again: bool
    
    # Optional text feedback
    comment_telugu: str
    
    # Issue reporting
    issue_reported: bool
    issue_category: str  # payment_not_received/price_reduction/unfair_grading/rude_behavior/other
    issue_description: str
    
    created_at: datetime
    verified_transaction: bool
```

**Reliability Score Calculation**:
```python
def calculate_reliability_score(channel_id):
    # Get all feedback for channel
    feedbacks = db.query(ChannelFeedback).filter(
        ChannelFeedback.channel_id == channel_id,
        ChannelFeedback.verified_transaction == True
    ).all()
    
    if len(feedbacks) < 5:
        return None  # Not enough data
    
    # Calculate component scores (0-5 scale)
    payment_score = calculate_weighted_average(
        [f.payment_timeliness_rating for f in feedbacks],
        recency_weight=True
    )
    
    price_score = calculate_weighted_average(
        [f.price_accuracy_rating for f in feedbacks],
        recency_weight=True
    )
    
    quality_score = calculate_weighted_average(
        [f.quality_assessment_rating for f in feedbacks],
        recency_weight=True
    )
    
    overall_score = calculate_weighted_average(
        [f.overall_satisfaction_rating for f in feedbacks],
        recency_weight=True
    )
    
    # Weighted composite score
    reliability_score = (
        payment_score * 0.40 +
        price_score * 0.30 +
        quality_score * 0.20 +
        overall_score * 0.10
    )
    
    return round(reliability_score, 1)
```

**Recency Weighting**:
```python
def calculate_weighted_average(ratings, recency_weight=True):
    if not recency_weight:
        return sum(ratings) / len(ratings)
    
    # Apply exponential decay to older ratings
    weighted_sum = 0
    weight_sum = 0
    
    for i, rating in enumerate(ratings):
        # More recent ratings get higher weight
        weight = math.exp(-0.1 * i)  # Decay factor
        weighted_sum += rating * weight
        weight_sum += weight
    
    return weighted_sum / weight_sum if weight_sum > 0 else 0
```

**Fraud Detection**:
```python
def detect_fake_reviews(channel_id):
    feedbacks = get_channel_feedbacks(channel_id)
    
    # Pattern 1: Same farmer reviewing same channel multiple times
    farmer_counts = Counter([f.farmer_id for f in feedbacks])
    if any(count > 3 for count in farmer_counts.values()):
        flag_for_review(channel_id, "repeated_reviewer")
    
    # Pattern 2: Suspiciously uniform ratings (all 5 stars or all 1 star)
    ratings = [f.overall_satisfaction_rating for f in feedbacks]
    if len(set(ratings)) == 1 and len(ratings) > 10:
        flag_for_review(channel_id, "uniform_ratings")
    
    # Pattern 3: Burst of reviews in short time
    recent_feedbacks = [f for f in feedbacks if (datetime.now() - f.created_at).days < 7]
    if len(recent_feedbacks) > 20:
        flag_for_review(channel_id, "review_burst")
    
    # Pattern 4: Reviews without verified transactions
    unverified = [f for f in feedbacks if not f.verified_transaction]
    if len(unverified) / len(feedbacks) > 0.3:
        flag_for_review(channel_id, "unverified_reviews")
```

**API Endpoints**:
```
POST /api/v1/feedback/channel
Body: ChannelFeedback

GET /api/v1/channels/{id}/reliability
Response:
{
  "overall_score": float,
  "component_scores": {
    "payment": float,
    "price": float,
    "quality": float,
    "overall": float
  },
  "total_feedbacks": int,
  "recent_reviews": [ChannelFeedback],
  "badges": ["Verified Buyer", "Improved Service"]
}

POST /api/v1/feedback/report-issue
Body: {
  channel_id, issue_category, description
}
```

**Feedback Collection Flow**:
```python
def collect_feedback_after_transaction(transaction_id):
    # Wait 24 hours after transaction
    schedule_task(
        task=send_feedback_request,
        delay=timedelta(hours=24),
        args=[transaction_id]
    )

def send_feedback_request(transaction_id):
    transaction = get_transaction(transaction_id)
    farmer = get_farmer(transaction.farmer_id)
    
    # Send SMS
    send_sms(
        farmer.phone,
        f"మీ విక్రయ అనుభవం ఎలా ఉంది? ఫీడ్‌బ్యాక్ ఇవ్వండి: {feedback_link}"
    )
    
    # Send app notification
    send_push_notification(
        farmer.device_token,
        "మీ విక్రయ అనుభవం పంచుకోండి",
        "ఇతర రైతులకు సహాయం చేయండి"
    )
```

#### 3.2.5 Alternative Pathway Calculation

**Purpose**: Calculate and compare different routes to market with complete cost breakdowns

**Data Model**:
```python
class Pathway:
    id: UUID
    pathway_type: str  # direct/single_intermediary/multi_step
    steps: list  # [PathwayStep]
    
    # Financial calculations
    gross_price_per_quintal: float
    total_deductions: float
    net_price_per_quintal: float
    total_earnings: float  # for farmer's quantity
    
    # Non-financial factors
    payment_terms: str
    payment_days: int
    transport_arrangement: str  # farmer/buyer
    reliability_score: float
    
    # Ranking
    rank: int
    recommended: bool
    
class PathwayStep:
    step_number: int
    entity_type: str  # farmer/aggregator/processor/mandi/retailer
    entity_name: str
    price_per_quintal: float
    deductions: dict  # {commission, transport, handling, testing, storage}
    value_addition: str  # what happens at this step
```

**Pathway Generation Algorithm**:
```python
def generate_pathways(farmer_location, crop_id, quantity, quality_grade):
    pathways = []
    
    # Pathway 1: Direct to Mandi
    mandis = get_nearby_mandis(farmer_location, radius_km=50)
    for mandi in mandis:
        pathway = create_direct_mandi_pathway(mandi, crop_id, quantity)
        pathways.append(pathway)
    
    # Pathway 2: Through Aggregator to Mandi
    aggregators = get_nearby_aggregators(farmer_location, radius_km=25)
    for aggregator in aggregators:
        pathway = create_aggregator_mandi_pathway(aggregator, crop_id, quantity)
        pathways.append(pathway)
    
    # Pathway 3: Through Aggregator to Processor
    processors = get_processors_for_crop(crop_id, radius_km=100)
    for aggregator in aggregators:
        for processor in processors:
            pathway = create_aggregator_processor_pathway(aggregator, processor, crop_id, quantity)
            pathways.append(pathway)
    
    # Pathway 4: Direct to Processor/Exporter
    for processor in processors:
        if processor.accepts_direct_farmers and quantity >= processor.minimum_quantity:
            pathway = create_direct_processor_pathway(processor, crop_id, quantity, quality_grade)
            pathways.append(pathway)
    
    # Pathway 5: Through FPO Collective Sale
    if farmer.fpo_member:
        fpo_pathways = create_fpo_pathways(farmer.fpo_id, crop_id, quantity)
        pathways.extend(fpo_pathways)
    
    return pathways
```

**Cost Calculation**:
```python
def calculate_pathway_costs(pathway, farmer_location, quantity):
    total_deductions = 0
    
    for step in pathway.steps:
        # Commission/fees
        if step.commission_pct:
            commission = step.price_per_quintal * (step.commission_pct / 100)
            step.deductions['commission'] = commission
            total_deductions += commission * quantity
        
        # Transport costs
        if step.transport_responsibility == 'farmer':
            distance = calculate_distance(farmer_location, step.location)
            transport_cost = distance * TRANSPORT_COST_PER_KM_PER_QUINTAL
            step.deductions['transport'] = transport_cost
            total_deductions += transport_cost * quantity
        
        # Handling/loading charges
        if step.handling_charges:
            step.deductions['handling'] = step.handling_charges
            total_deductions += step.handling_charges * quantity
        
        # Quality testing fees
        if step.quality_testing_required:
            step.deductions['testing'] = QUALITY_TESTING_FEE
            total_deductions += QUALITY_TESTING_FEE
        
        # Storage costs (if applicable)
        if step.storage_days > 0:
            storage_cost = step.storage_days * STORAGE_COST_PER_DAY_PER_QUINTAL
            step.deductions['storage'] = storage_cost
            total_deductions += storage_cost * quantity
    
    # Calculate net price
    gross_price = pathway.steps[-1].price_per_quintal
    net_price = gross_price - (total_deductions / quantity)
    total_earnings = net_price * quantity
    
    pathway.gross_price_per_quintal = gross_price
    pathway.total_deductions = total_deductions
    pathway.net_price_per_quintal = net_price
    pathway.total_earnings = total_earnings
    
    return pathway
```

**Pathway Ranking Algorithm**:
```python
def rank_pathways(pathways, farmer_preferences=None):
    # Default ranking by net profitability
    pathways.sort(key=lambda p: p.net_price_per_quintal, reverse=True)
    
    # Apply multi-factor scoring if preferences provided
    if farmer_preferences:
        for pathway in pathways:
            score = 0
            
            # Net price (40% weight)
            price_score = pathway.net_price_per_quintal / max(p.net_price_per_quintal for p in pathways)
            score += price_score * 0.40
            
            # Payment speed (25% weight)
            payment_score = 1.0 / (1 + pathway.payment_days / 7)
            score += payment_score * 0.25
            
            # Reliability (20% weight)
            reliability_score = pathway.reliability_score / 5.0
            score += reliability_score * 0.20
            
            # Convenience (15% weight)
            convenience_score = 1.0 if pathway.transport_arrangement == 'buyer' else 0.7
            score += convenience_score * 0.15
            
            pathway.composite_score = score
        
        pathways.sort(key=lambda p: p.composite_score, reverse=True)
    
    # Assign ranks
    for i, pathway in enumerate(pathways):
        pathway.rank = i + 1
        pathway.recommended = (i == 0)
    
    return pathways
```

**Voice Output Format**:
```
"మొదటి మార్గం: నేరుగా మండికి. 
క్వింటాల్‌కు ₹900 నెట్, అదే రోజు చెల్లింపు, కానీ మీరే రవాణా చేయాలి. 
మీ 30 క్వింటాల్‌లకు మొత్తం ₹27,000.

రెండవ మార్గం: అగ్రిగేటర్ ద్వారా. 
క్వింటాల్‌కు ₹850 నెట్, 3 రోజుల్లో చెల్లింపు, కానీ వారు రవాణా చేస్తారు. 
మొత్తం ₹25,500."

(First path: Direct to mandi.
₹900 net per quintal, same-day payment, but you arrange transport.
Total ₹27,000 for your 30 quintals.

Second path: Through aggregator.
₹850 net per quintal, payment in 3 days, but they arrange transport.
Total ₹25,500.)
```

---

### 3.3 Phase 3: Crop Exploration and Planning Hub

Phase 3 introduces comprehensive crop planning capabilities to help farmers make informed planting decisions.

#### 3.3.1 Crop Information Hub and Seasonal Intelligence

**Purpose**: Provide farmers with comprehensive crop information for planning next season

**Data Model**:
```python
class CropProfile:
    id: UUID
    crop_name_english: str
    crop_name_telugu: str
    crop_category: str  # vegetable/fruit/grain/pulse/cash_crop
    
    # Seasonal demand intelligence
    demand_level: str  # HIGH/MEDIUM/LOW
    demand_trend: str  # increasing/stable/decreasing
    peak_demand_months: list
    demand_drivers: list  # ["Festival season", "Export window", "Processing demand"]
    
    # Regional trends
    farmers_growing_count: int
    total_acreage: float
    average_yield_per_acre: float
    success_rate_pct: float
    common_challenges: list
    best_performing_regions: list
    
    # Market intelligence
    expected_price_range_min: float
    expected_price_range_max: float
    price_volatility: str  # HIGH/MEDIUM/LOW
    historical_prices: list  # [{month, year, avg_price}]
    
    # Quick summary
    summary_telugu: str
    
    updated_at: datetime

class PeerActivity:
    id: UUID
    crop_id: UUID
    farmer_reference: str  # anonymized
    acreage_planted: float
    planting_date: datetime
    irrigation_method: str
    farming_method: str  # traditional/organic/precision
    farmer_notes: str  # optional
    location_village: str
    location_mandal: str
    created_at: datetime
```

**Seasonal Demand Analysis**:
```python
def analyze_seasonal_demand(crop_id, upcoming_season):
    # Gather data sources
    market_trends = get_market_trends(crop_id, lookback_years=3)
    buyer_signals = get_buyer_demand_signals(crop_id, upcoming_season)
    export_calendar = get_export_windows(crop_id)
    processing_demand = get_processing_industry_demand(crop_id)
    govt_procurement = get_government_procurement_plans(crop_id)
    
    # Calculate demand level
    demand_score = (
        market_trends.growth_rate * 0.30 +
        buyer_signals.active_count * 0.25 +
        export_calendar.window_open * 0.20 +
        processing_demand.capacity_utilization * 0.15 +
        govt_procurement.planned_quantity * 0.10
    )
    
    # Classify demand level
    if demand_score > 0.7:
        demand_level = "HIGH"
    elif demand_score > 0.4:
        demand_level = "MEDIUM"
    else:
        demand_level = "LOW"
    
    # Identify demand drivers
    drivers = []
    if export_calendar.window_open:
        drivers.append("Export window opens")
    if processing_demand.capacity_utilization > 0.8:
        drivers.append("Processing industry requirement")
    if is_festival_season(upcoming_season):
        drivers.append("Festival season demand")
    
    return {
        "demand_level": demand_level,
        "demand_score": demand_score,
        "drivers": drivers,
        "peak_months": export_calendar.peak_months
    }
```

**Regional Trend Aggregation**:
```python
def aggregate_regional_trends(crop_id, mandal_id, district_id):
    # Get planting activity from last season
    activities = db.query(PeerActivity).filter(
        PeerActivity.crop_id == crop_id,
        PeerActivity.location_mandal == mandal_id,
        PeerActivity.planting_date >= last_season_start
    ).all()
    
    # Get outcome data
    outcomes = db.query(CropOutcome).filter(
        CropOutcome.crop_id == crop_id,
        CropOutcome.location_mandal == mandal_id,
        CropOutcome.harvest_date >= last_season_start
    ).all()
    
    # Calculate metrics
    farmers_count = len(set(a.farmer_id for a in activities))
    total_acreage = sum(a.acreage_planted for a in activities)
    
    # Calculate success rate (farmers who profited)
    profitable_count = len([o for o in outcomes if o.net_profit > 0])
    success_rate = (profitable_count / len(outcomes) * 100) if outcomes else 0
    
    # Calculate average yield
    yields = [o.yield_per_acre for o in outcomes if o.yield_per_acre]
    avg_yield = sum(yields) / len(yields) if yields else 0
    
    # Identify common challenges
    challenges = Counter([c for o in outcomes for c in o.challenges_faced])
    common_challenges = [c for c, count in challenges.most_common(5)]
    
    return {
        "farmers_count": farmers_count,
        "total_acreage": total_acreage,
        "success_rate": success_rate,
        "avg_yield": avg_yield,
        "common_challenges": common_challenges
    }
```

**API Endpoints**:
```
GET /api/v1/explore/seasonal-demand
Query params:
  - season: required (kharif/rabi/summer)
  - mandal_id: required
  - limit: optional (default 15)

Response:
{
  "top_crops": [
    {
      "crop": CropProfile,
      "demand_analysis": {...},
      "regional_trends": {...}
    }
  ],
  "trending_up": [crop_id],
  "caution_crops": [crop_id]
}

GET /api/v1/explore/peer-activity
Query params:
  - crop_id: optional
  - mandal_id: required
  - days: optional (default 30)

Response:
{
  "activities": [PeerActivity],
  "summary": {
    "total_farmers": int,
    "total_acreage": float,
    "popular_methods": [str]
  }
}

GET /api/v1/explore/crop/{id}/profile
Response: Complete CropProfile with all details
```

**Voice Output Format**:
```
"ఈ సీజన్‌లో టమాటా, ఉల్లిపాయ, మిరపకాయలకు HIGH డిమాండ్ ఉంది. 
టమాటా క్వింటాల్‌కు ₹800-₹1200 వరకు అమ్ముకోవచ్చు. 
150 మంది రైతులు పండిస్తున్నారు. 
డిసెంబర్ నుండి ఫిబ్రవరి వరకు డిమాండ్ ఎక్కువ."

(This season tomatoes, onions, chillies have HIGH demand.
Tomatoes can sell for ₹800-₹1200 per quintal.
150 farmers are growing.
Demand is high from December to February.)
```

#### 3.3.2 Investment Calculator with Detailed Cost Breakdown

**Purpose**: Help farmers understand complete investment requirements before planting

**Data Model**:
```python
class CropInvestmentModel:
    id: UUID
    crop_id: UUID
    region_id: UUID
    
    # Seeds/Seedlings
    seed_quantity_per_acre: float
    seed_cost_per_kg_min: float
    seed_cost_per_kg_max: float
    
    # Fertilizers
    fertilizer_schedule: list  # [{type, quantity_per_acre, cost_min, cost_max, application_stage}]
    
    # Pesticides/Fungicides
    pesticide_schedule: list  # [{type, applications_count, cost_per_application_min, cost_per_application_max}]
    
    # Irrigation
    water_requirement_liters_per_acre: float
    irrigation_frequency_per_week: int
    electricity_cost_per_acre_min: float
    electricity_cost_per_acre_max: float
    drip_system_rental_cost: float
    
    # Labor
    labor_requirements: list  # [{activity, person_days_per_acre, daily_wage_min, daily_wage_max}]
    
    # Equipment
    equipment_needs: list  # [{equipment, hours_per_acre, rental_rate_per_hour}]
    
    # Miscellaneous
    transport_cost_per_acre: float
    storage_materials_cost: float
    quality_testing_cost: float
    
    # Timeline
    cost_timeline: list  # [{phase, days_from_planting, costs}]
    
    updated_at: datetime

class InvestmentCalculation:
    farmer_id: UUID
    crop_id: UUID
    acreage: float
    irrigation_type: str
    farming_method: str
    own_resources: dict  # {seeds: bool, equipment: bool, labor_family: int}
    
    # Calculated costs
    seed_cost: dict  # {min, max}
    fertilizer_cost: dict
    pesticide_cost: dict
    irrigation_cost: dict
    labor_cost: dict
    equipment_cost: dict
    misc_cost: dict
    
    total_investment_min: float
    total_investment_max: float
    per_acre_investment: float
    
    # Savings from own resources
    total_savings: float
    
    # Timeline
    cost_schedule: list  # [{month, amount}]
```

**Investment Calculation Algorithm**:
```python
def calculate_investment(crop_id, acreage, irrigation_type, farming_method, own_resources):
    # Get cost model for crop and region
    model = get_investment_model(crop_id, farmer.region_id)
    
    calc = InvestmentCalculation()
    calc.acreage = acreage
    
    # Seeds cost
    if own_resources.get('seeds'):
        calc.seed_cost = {'min': 0, 'max': 0}
        calc.total_savings += model.seed_cost_per_kg_max * model.seed_quantity_per_acre * acreage
    else:
        calc.seed_cost = {
            'min': model.seed_cost_per_kg_min * model.seed_quantity_per_acre * acreage,
            'max': model.seed_cost_per_kg_max * model.seed_quantity_per_acre * acreage
        }
    
    # Fertilizer cost
    fert_cost_min = sum(f['cost_min'] * f['quantity_per_acre'] for f in model.fertilizer_schedule) * acreage
    fert_cost_max = sum(f['cost_max'] * f['quantity_per_acre'] for f in model.fertilizer_schedule) * acreage
    
    if farming_method == 'organic':
        # Organic fertilizers typically 20-30% more expensive
        fert_cost_min *= 1.2
        fert_cost_max *= 1.3
    
    calc.fertilizer_cost = {'min': fert_cost_min, 'max': fert_cost_max}
    
    # Pesticide cost
    pest_cost_min = sum(p['cost_per_application_min'] * p['applications_count'] for p in model.pesticide_schedule) * acreage
    pest_cost_max = sum(p['cost_per_application_max'] * p['applications_count'] for p in model.pesticide_schedule) * acreage
    
    if farming_method == 'organic':
        # Organic pest control may be cheaper or more expensive depending on method
        pest_cost_min *= 0.8
        pest_cost_max *= 1.2
    
    calc.pesticide_cost = {'min': pest_cost_min, 'max': pest_cost_max}
    
    # Irrigation cost
    if irrigation_type == 'drip':
        irr_cost = model.drip_system_rental_cost * acreage
    else:
        irr_cost_min = model.electricity_cost_per_acre_min * acreage
        irr_cost_max = model.electricity_cost_per_acre_max * acreage
    
    calc.irrigation_cost = {'min': irr_cost_min, 'max': irr_cost_max}
    
    # Labor cost
    total_person_days = sum(l['person_days_per_acre'] for l in model.labor_requirements) * acreage
    
    # Adjust for family labor
    if own_resources.get('labor_family'):
        family_labor_days = min(total_person_days * 0.4, own_resources['labor_family'] * 30)
        total_person_days -= family_labor_days
        calc.total_savings += family_labor_days * model.labor_requirements[0]['daily_wage_max']
    
    labor_cost_min = total_person_days * min(l['daily_wage_min'] for l in model.labor_requirements)
    labor_cost_max = total_person_days * max(l['daily_wage_max'] for l in model.labor_requirements)
    
    calc.labor_cost = {'min': labor_cost_min, 'max': labor_cost_max}
    
    # Equipment cost
    if own_resources.get('equipment'):
        calc.equipment_cost = {'min': 0, 'max': 0}
        calc.total_savings += sum(e['hours_per_acre'] * e['rental_rate_per_hour'] for e in model.equipment_needs) * acreage
    else:
        equip_cost = sum(e['hours_per_acre'] * e['rental_rate_per_hour'] for e in model.equipment_needs) * acreage
        calc.equipment_cost = {'min': equip_cost, 'max': equip_cost}
    
    # Miscellaneous costs
    misc_cost = (model.transport_cost_per_acre + model.storage_materials_cost + model.quality_testing_cost) * acreage
    calc.misc_cost = {'min': misc_cost, 'max': misc_cost}
    
    # Total investment
    calc.total_investment_min = sum(c['min'] for c in [calc.seed_cost, calc.fertilizer_cost, calc.pesticide_cost, calc.irrigation_cost, calc.labor_cost, calc.equipment_cost, calc.misc_cost])
    calc.total_investment_max = sum(c['max'] for c in [calc.seed_cost, calc.fertilizer_cost, calc.pesticide_cost, calc.irrigation_cost, calc.labor_cost, calc.equipment_cost, calc.misc_cost])
    calc.per_acre_investment = (calc.total_investment_min + calc.total_investment_max) / 2 / acreage
    
    # Generate cost timeline
    calc.cost_schedule = generate_cost_timeline(model.cost_timeline, calc, acreage)
    
    return calc
```

**API Endpoints**:
```
POST /api/v1/explore/calculate-investment
Body:
{
  crop_id, acreage, irrigation_type, farming_method, own_resources
}

Response: InvestmentCalculation

GET /api/v1/explore/investment-model/{crop_id}
Response: CropInvestmentModel
```

**Voice Output Format**:
```
"టమాటా 2 ఎకరాలకు మొత్తం పెట్టుబడి ₹40,000-₹60,000. 
ముఖ్యంగా విత్తనాలు ₹8,000, ఎరువులు ₹15,000, కూలీలు ₹20,000. 
మీ స్వంత విత్తనాలు ఉపయోగిస్తే ₹5,000 ఆదా అవుతుంది."

(For 2 acres of tomatoes, total investment ₹40,000-₹60,000.
Mainly seeds ₹8,000, fertilizers ₹15,000, labor ₹20,000.
Using your own seeds saves ₹5,000.)
```

#### 3.3.3 ROI Projections and Profitability Analysis

**Purpose**: Help farmers understand expected returns and risks for different crops

**Data Model**:
```python
class ROIProjection:
    crop_id: UUID
    region_id: UUID
    acreage: float
    
    # Yield projections
    yield_per_acre_min: float
    yield_per_acre_max: float
    yield_per_acre_avg: float
    yield_risk_level: str  # HIGH/MEDIUM/LOW
    
    # Price projections
    price_per_quintal_min: float
    price_per_quintal_max: float
    price_per_quintal_avg: float
    price_risk_level: str  # HIGH/MEDIUM/LOW
    
    # Revenue projections
    revenue_min: float
    revenue_max: float
    revenue_expected: float
    
    # Investment (from calculator)
    total_investment: float
    
    # Profitability
    net_profit_min: float
    net_profit_max: float
    net_profit_expected: float
    roi_pct_min: float
    roi_pct_max: float
    roi_pct_expected: float
    
    # Break-even analysis
    breakeven_yield_quintals: float
    breakeven_price_per_quintal: float
    
    # Risk assessment
    overall_risk_level: str  # HIGH/MEDIUM/LOW
    risk_factors: list  # [{factor, severity, explanation}]
    
    # Scenarios
    best_case: dict
    expected_case: dict
    worst_case: dict
    
    # Timeline
    months_to_profitability: int
    
    # Historical accuracy
    projection_confidence: float  # 0-1
    based_on_years: int
```

**ROI Calculation Algorithm**:
```python
def calculate_roi_projection(crop_id, region_id, acreage, investment):
    # Get historical yield data (3-5 years)
    yield_history = get_historical_yields(crop_id, region_id, years=5)
    
    # Calculate yield projections
    yields = [y.yield_per_acre for y in yield_history]
    yield_min = percentile(yields, 10)  # 10th percentile (pessimistic)
    yield_max = percentile(yields, 90)  # 90th percentile (optimistic)
    yield_avg = mean(yields)
    
    # Assess yield risk based on variance
    yield_variance = variance(yields)
    if yield_variance > 0.3 * yield_avg:
        yield_risk = "HIGH"
    elif yield_variance > 0.15 * yield_avg:
        yield_risk = "MEDIUM"
    else:
        yield_risk = "LOW"
    
    # Get historical price data
    price_history = get_historical_prices(crop_id, region_id, years=5)
    
    # Calculate price projections (seasonal adjustment)
    prices = [p.price_per_quintal for p in price_history if p.month in harvest_months]
    price_min = percentile(prices, 10)
    price_max = percentile(prices, 90)
    price_avg = mean(prices)
    
    # Assess price risk based on volatility
    price_volatility = std_dev(prices) / price_avg
    if price_volatility > 0.4:
        price_risk = "HIGH"
    elif price_volatility > 0.2:
        price_risk = "MEDIUM"
    else:
        price_risk = "LOW"
    
    # Calculate revenue scenarios
    revenue_min = yield_min * price_min * acreage
    revenue_max = yield_max * price_max * acreage
    revenue_expected = yield_avg * price_avg * acreage
    
    # Calculate profitability
    net_profit_min = revenue_min - investment
    net_profit_max = revenue_max - investment
    net_profit_expected = revenue_expected - investment
    
    roi_min = (net_profit_min / investment) * 100
    roi_max = (net_profit_max / investment) * 100
    roi_expected = (net_profit_expected / investment) * 100
    
    # Break-even analysis
    breakeven_yield = investment / (price_avg * acreage)
    breakeven_price = investment / (yield_avg * acreage)
    
    # Risk assessment
    risk_factors = assess_risk_factors(crop_id, region_id, yield_risk, price_risk)
    overall_risk = calculate_overall_risk(risk_factors)
    
    # Scenario analysis
    best_case = {
        "yield": yield_max,
        "price": price_max,
        "revenue": revenue_max,
        "profit": net_profit_max,
        "roi": roi_max
    }
    
    expected_case = {
        "yield": yield_avg,
        "price": price_avg,
        "revenue": revenue_expected,
        "profit": net_profit_expected,
        "roi": roi_expected
    }
    
    worst_case = {
        "yield": yield_min,
        "price": price_min,
        "revenue": revenue_min,
        "profit": net_profit_min,
        "roi": roi_min
    }
    
    return ROIProjection(...)
```

**Risk Assessment**:
```python
def assess_risk_factors(crop_id, region_id, yield_risk, price_risk):
    risk_factors = []
    
    # Price volatility risk
    if price_risk == "HIGH":
        risk_factors.append({
            "factor": "Price Risk",
            "severity": "HIGH",
            "explanation": "Prices fluctuate 40-60% seasonally",
            "mitigation": ["Staggered planting", "Pre-selling 30%", "Value addition"]
        })
    
    # Yield variability risk
    if yield_risk == "HIGH":
        risk_factors.append({
            "factor": "Yield Risk",
            "severity": "HIGH",
            "explanation": "Weather dependent, high variability",
            "mitigation": ["Drip irrigation", "Quality seeds", "Pest management"]
        })
    
    # Spoilage risk
    spoilage_rate = get_crop_spoilage_rate(crop_id)
    if spoilage_rate > 0.15:
        risk_factors.append({
            "factor": "Spoilage Risk",
            "severity": "HIGH",
            "explanation": "15-20% post-harvest loss typical",
            "mitigation": ["Immediate sale", "Cold storage", "Processing"]
        })
    
    # Market access risk
    market_access = assess_market_access(crop_id, region_id)
    if market_access.buyer_count < 3:
        risk_factors.append({
            "factor": "Market Access",
            "severity": "MEDIUM",
            "explanation": "Limited buyers in region",
            "mitigation": ["FPO collective sale", "Explore distant markets"]
        })
    
    # Weather risk
    weather_sensitivity = get_weather_sensitivity(crop_id)
    if weather_sensitivity == "HIGH":
        risk_factors.append({
            "factor": "Weather Risk",
            "severity": "MEDIUM",
            "explanation": "Sensitive to rain, temperature extremes",
            "mitigation": ["Protected cultivation", "Weather insurance"]
        })
    
    return risk_factors

def calculate_overall_risk(risk_factors):
    high_count = len([r for r in risk_factors if r['severity'] == 'HIGH'])
    medium_count = len([r for r in risk_factors if r['severity'] == 'MEDIUM'])
    
    if high_count >= 2:
        return "HIGH"
    elif high_count == 1 or medium_count >= 3:
        return "MEDIUM"
    else:
        return "LOW"
```

**Voice Output Format**:
```
"టమాటా 2 ఎకరాలకు పెట్టుబడి ₹50,000. 
ఆశించే ఆదాయం ₹1,20,000-₹2,00,000. 
నెట్ లాభం ₹70,000-₹1,50,000. 
ROI 140-300%. 
కానీ రిస్క్ MEDIUM ఎందుకంటే ధర అస్థిరత ఉంది. 
మీరు ఎకరాకు కనీసం 80 క్వింటాల్స్ పండించాలి లేదా క్వింటాల్‌కు కనీసం ₹750 పొందాలి."

(For 2 acres tomatoes, investment ₹50,000.
Expected revenue ₹1,20,000-₹2,00,000.
Net profit ₹70,000-₹1,50,000.
ROI 140-300%.
But risk is MEDIUM due to price volatility.
You need minimum 80 quintals per acre OR minimum ₹750 per quintal.)
```

#### 3.3.4 Cultivation Requirements and Land Suitability

**Purpose**: Help farmers choose crops suitable for their land conditions

**Data Model**:
```python
class CropRequirements:
    crop_id: UUID
    
    # Soil requirements
    suitable_soil_types: list  # ["red_soil", "black_soil", "sandy_loam"]
    ph_range_min: float
    ph_range_max: float
    drainage_requirement: str  # well_drained/moderate/poor
    soil_preparation_steps: list  # [{step, description, timing}]
    
    # Water requirements
    total_water_liters_per_acre: float
    irrigation_frequency_per_week: int
    critical_watering_stages: list  # ["flowering", "fruit_development"]
    drought_tolerance: str  # HIGH/MEDIUM/LOW
    suitable_irrigation_methods: list  # ["drip", "sprinkler", "flood"]
    
    # Climate requirements
    optimal_temp_day_min: float
    optimal_temp_day_max: float
    optimal_temp_night_min: float
    optimal_temp_night_max: float
    rainfall_requirement_mm: float
    sunlight_requirement: str  # full_sun/partial_shade
    season_suitability: list  # ["kharif", "rabi", "summer"]
    frost_tolerance: bool
    wind_sensitivity: str  # HIGH/MEDIUM/LOW
    humidity_preference: str  # HIGH/MEDIUM/LOW
    
    # Cultivation calendar
    cultivation_calendar: list  # [{month, activity, description}]
    
    # Varieties
    recommended_varieties: list  # [{name, characteristics, yield_potential}]
    
    # Intercropping
    compatible_intercrops: list
    
    # Pest and disease
    common_pests: list
    common_diseases: list
    susceptibility_level: str  # HIGH/MEDIUM/LOW

class FarmerLandProfile:
    farmer_id: UUID
    land_id: UUID
    
    # Soil characteristics
    soil_type: str
    soil_ph: float
    drainage_quality: str
    organic_matter_content: str  # HIGH/MEDIUM/LOW
    
    # Irrigation
    irrigation_source: str  # borewell/canal/rainfed
    irrigation_capacity: str  # adequate/limited/none
    
    # Location and climate
    location_lat: float
    location_lon: float
    elevation_meters: float
    avg_rainfall_mm: float
    
    # Land size
    total_acreage: float
    cultivable_acreage: float
    
    # History
    previous_crops: list  # [{crop_id, year, yield, success}]
```

**Suitability Matching Algorithm**:
```python
def check_land_suitability(crop_id, farmer_land_profile):
    requirements = get_crop_requirements(crop_id)
    land = farmer_land_profile
    
    suitability_score = 0
    max_score = 0
    issues = []
    recommendations = []
    
    # Soil type match (weight: 25%)
    max_score += 25
    if land.soil_type in requirements.suitable_soil_types:
        suitability_score += 25
    else:
        issues.append({
            "factor": "Soil Type",
            "severity": "HIGH",
            "issue": f"Crop prefers {requirements.suitable_soil_types}, you have {land.soil_type}",
            "solution": "Consider soil amendments or choose different crop"
        })
    
    # pH match (weight: 15%)
    max_score += 15
    if requirements.ph_range_min <= land.soil_ph <= requirements.ph_range_max:
        suitability_score += 15
    else:
        ph_diff = min(abs(land.soil_ph - requirements.ph_range_min), 
                      abs(land.soil_ph - requirements.ph_range_max))
        if ph_diff < 0.5:
            suitability_score += 10
            issues.append({
                "factor": "Soil pH",
                "severity": "MEDIUM",
                "issue": f"pH {land.soil_ph} is slightly outside optimal range {requirements.ph_range_min}-{requirements.ph_range_max}",
                "solution": f"Apply lime to increase pH or sulfur to decrease pH (cost: ₹2000-3000/acre)"
            })
        else:
            issues.append({
                "factor": "Soil pH",
                "severity": "HIGH",
                "issue": f"pH {land.soil_ph} is significantly outside optimal range",
                "solution": "Major soil amendment needed or choose different crop"
            })
    
    # Irrigation match (weight: 30%)
    max_score += 30
    if land.irrigation_source in ['borewell', 'canal'] and land.irrigation_capacity == 'adequate':
        suitability_score += 30
    elif land.irrigation_source == 'rainfed' and requirements.drought_tolerance == 'HIGH':
        suitability_score += 25
    elif land.irrigation_capacity == 'limited':
        suitability_score += 15
        issues.append({
            "factor": "Irrigation",
            "severity": "MEDIUM",
            "issue": "Limited irrigation capacity",
            "solution": "Consider drip irrigation for water efficiency (cost: ₹25,000-35,000/acre)"
        })
    else:
        issues.append({
            "factor": "Irrigation",
            "severity": "HIGH",
            "issue": "Insufficient water availability",
            "solution": "Choose drought-tolerant crops or improve irrigation"
        })
    
    # Drainage match (weight: 15%)
    max_score += 15
    if land.drainage_quality == requirements.drainage_requirement:
        suitability_score += 15
    else:
        suitability_score += 8
        issues.append({
            "factor": "Drainage",
            "severity": "MEDIUM",
            "issue": f"Drainage is {land.drainage_quality}, crop needs {requirements.drainage_requirement}",
            "solution": "Create raised beds or improve drainage channels"
        })
    
    # Climate match (weight: 15%)
    max_score += 15
    climate_score = check_climate_suitability(requirements, land.location_lat, land.location_lon)
    suitability_score += climate_score
    
    # Calculate final suitability
    final_score = (suitability_score / max_score) * 100
    
    if final_score >= 80:
        suitability = "HIGHLY SUITABLE"
    elif final_score >= 60:
        suitability = "SUITABLE"
    elif final_score >= 40:
        suitability = "MARGINALLY SUITABLE"
    else:
        suitability = "NOT SUITABLE"
    
    return {
        "suitability": suitability,
        "score": final_score,
        "issues": issues,
        "recommendations": recommendations
    }
```

**Voice Output Format**:
```
"టమాటాకు ఎర్ర మట్టి బాగుంటుంది, pH 6-7, వారానికి 2-3 సార్లు నీరు, 20-30 డిగ్రీల ఉష్ణోగ్రత కావాలి. 
మీ భూమికి HIGHLY SUITABLE. 
మీ ఎర్ర మట్టి మరియు బోరువెల్ నీరు టమాటాకు బాగా సరిపోతాయి."

(Tomato prefers red soil, pH 6-7, water 2-3 times per week, 20-30°C temperature needed.
HIGHLY SUITABLE for your land.
Your red soil and borewell water are perfect for tomatoes.)
```

#### 3.3.5 Value Addition and Income Diversification

**Purpose**: Help farmers discover processing opportunities to increase income

**Data Model**:
```python
class ValueAdditionOpportunity:
    id: UUID
    crop_id: UUID
    
    # Processing option
    processing_type: str  # drying/dehydration/powder/oil/juice/pickle
    processed_product_name: str
    
    # Economics
    price_multiplier: float  # e.g., 3.0 means 3x price
    processing_cost_per_quintal: float
    net_profit_increase_pct: float
    
    # Requirements
    equipment_needed: list  # [{name, cost_purchase, cost_rental, capacity}]
    skill_requirements: str  # basic/intermediate/advanced
    training_available: bool
    training_providers: list  # [{name, location, contact, cost}]
    
    # Processing details
    processing_steps: list  # [{step, description, duration, equipment}]
    processing_time_hours: float
    yield_ratio: float  # output/input ratio
    
    # Market access
    buyers: list  # [{name, type, location, contact, price_range}]
    market_demand: str  # HIGH/MEDIUM/LOW
    shelf_life_days: int
    
    # Certification
    certification_required: bool
    certification_type: str  # FSSAI/organic/other
    certification_cost: float
    certification_process: str
    
    # Success stories
    success_stories: list  # [{farmer_name, location, income_increase, testimonial}]
    
    # Feasibility
    feasibility_score: float  # 0-100
    initial_investment: float
    breakeven_quantity: float

class ProcessingEquipment:
    id: UUID
    equipment_name: str
    equipment_type: str
    capacity_kg_per_hour: float
    
    # Costs
    purchase_cost: float
    rental_cost_per_day: float
    maintenance_cost_per_month: float
    electricity_cost_per_hour: float
    
    # Availability
    suppliers: list  # [{name, location, contact, price}]
    fpo_shared_equipment: bool
    government_subsidy_available: bool
    subsidy_percentage: float
    
    # Specifications
    power_requirement_kw: float
    space_requirement_sqft: float
    operator_training_required: bool
```

**Value Addition Ranking Algorithm**:
```python
def rank_value_addition_opportunities(crop_id, farmer_resources):
    opportunities = get_value_addition_opportunities(crop_id)
    
    scored_opportunities = []
    for opp in opportunities:
        score = calculate_opportunity_score(opp, farmer_resources)
        scored_opportunities.append((opp, score))
    
    # Sort by score (descending)
    scored_opportunities.sort(key=lambda x: x[1], reverse=True)
    
    return [o[0] for o in scored_opportunities]

def calculate_opportunity_score(opp, farmer_resources):
    # Profitability (40% weight)
    profit_score = min(opp.net_profit_increase_pct / 100, 1.0)
    
    # Feasibility (30% weight)
    feasibility_score = 0
    
    # Equipment availability
    if opp.equipment_needed:
        if farmer_resources.get('has_equipment'):
            feasibility_score += 0.4
        elif any(e.fpo_shared_equipment for e in opp.equipment_needed):
            feasibility_score += 0.3
        elif any(e.rental_cost_per_day < 500 for e in opp.equipment_needed):
            feasibility_score += 0.2
    else:
        feasibility_score += 0.4
    
    # Skill requirements
    if opp.skill_requirements == 'basic':
        feasibility_score += 0.3
    elif opp.skill_requirements == 'intermediate' and opp.training_available:
        feasibility_score += 0.2
    elif opp.skill_requirements == 'advanced':
        feasibility_score += 0.1
    
    # Initial investment
    if opp.initial_investment < 10000:
        feasibility_score += 0.3
    elif opp.initial_investment < 25000:
        feasibility_score += 0.2
    elif opp.initial_investment < 50000:
        feasibility_score += 0.1
    
    # Market demand (20% weight)
    demand_score = {'HIGH': 1.0, 'MEDIUM': 0.6, 'LOW': 0.3}[opp.market_demand]
    
    # Buyer availability (10% weight)
    buyer_score = min(len(opp.buyers) / 5, 1.0)
    
    # Composite score
    total_score = (
        profit_score * 0.40 +
        feasibility_score * 0.30 +
        demand_score * 0.20 +
        buyer_score * 0.10
    )
    
    return total_score * 100
```

**Voice Output Format**:
```
"టమాటా ఎండబెట్టడం: 3 రెట్లు ధర పొందవచ్చు. 
డీహైడ్రేటర్ కావాలి ₹25,000. 
నెలకు ₹15,000 అదనపు ఆదాయం సాధ్యం. 
పులివెందుల FPO లో షేర్డ్ డీహైడ్రేటర్ ఉంది. 
XYZ ఫుడ్స్ ఎండిన టమాటాలు కొనుగోలు చేస్తారు."

(Tomato drying: Can get 3x price.
Need dehydrator ₹25,000.
Possible ₹15,000 extra income per month.
Pulivendula FPO has shared dehydrator.
XYZ Foods buys dried tomatoes.)
```

#### 3.3.6 Industry Applications and Premium Market Access

**Purpose**: Connect farmers with high-value industry buyers

**Data Model**:
```python
class IndustryBuyer:
    id: UUID
    company_name: str
    industry_category: str  # food_processing/pharma/cosmetics/textiles/export/nutraceuticals
    
    # Products and requirements
    products_made: list  # ["Ketchup", "Sauce", "Paste", "Juice"]
    crops_needed: list  # [crop_id]
    quality_requirements: dict  # {grade, moisture_pct, size, color, brix_level}
    
    # Pricing
    price_premium_pct: float  # premium over market rate
    price_range_min: float
    price_range_max: float
    
    # Terms
    payment_terms: str  # advance/immediate/30days
    minimum_quantity_quintals: float
    delivery_preference: str  # farm_gate/processing_unit
    
    # Contract farming
    contract_farming_available: bool
    contract_terms: dict  # {advance_payment, price_guarantee, input_support}
    
    # Certification requirements
    certifications_required: list  # ["organic", "FSSAI", "GlobalGAP", "APEDA"]
    certification_support_provided: bool
    
    # Contact
    contact_person: str
    contact_phone: str
    contact_email: str
    location_address: str
    location_lat: float
    location_lon: float
    
    # Procurement schedule
    procurement_months: list  # months when they buy
    
    # Reliability
    reliability_score: float
    total_farmers_connected: int
    
    # Verification
    verified: bool
    verification_date: datetime

class CertificationInfo:
    certification_type: str
    certification_body: str
    
    # Requirements
    requirements: list  # [{requirement, description}]
    documentation_needed: list
    inspection_process: str
    
    # Costs and timeline
    certification_cost: float
    renewal_cost_annual: float
    processing_time_days: int
    validity_years: int
    
    # Support
    fpo_group_certification: bool
    government_subsidy_available: bool
    subsidy_amount: float
    
    # Agencies
    certification_agencies: list  # [{name, location, contact}]
    training_programs: list  # [{provider, duration, cost}]
```

**Industry Buyer Matching Algorithm**:
```python
def match_industry_buyers(crop_id, farmer_quantity, farmer_quality_grade, farmer_location):
    # Get all industry buyers for crop
    buyers = db.query(IndustryBuyer).filter(
        IndustryBuyer.crops_needed.contains(crop_id),
        IndustryBuyer.verified == True
    ).all()
    
    matched_buyers = []
    for buyer in buyers:
        # Check quantity match
        if farmer_quantity < buyer.minimum_quantity_quintals:
            continue
        
        # Check quality match
        if not meets_quality_requirements(farmer_quality_grade, buyer.quality_requirements):
            continue
        
        # Calculate match score
        score = calculate_buyer_match_score(buyer, farmer_quantity, farmer_location)
        
        # Calculate premium earnings
        market_price = get_current_market_price(crop_id, farmer_location)
        premium_price = market_price * (1 + buyer.price_premium_pct / 100)
        premium_earnings = (premium_price - market_price) * farmer_quantity
        
        matched_buyers.append({
            "buyer": buyer,
            "match_score": score,
            "premium_earnings": premium_earnings,
            "distance_km": calculate_distance(buyer.location, farmer_location)
        })
    
    # Sort by premium earnings (descending)
    matched_buyers.sort(key=lambda x: x['premium_earnings'], reverse=True)
    
    return matched_buyers

def calculate_buyer_match_score(buyer, farmer_quantity, farmer_location):
    # Price premium (40% weight)
    premium_score = min(buyer.price_premium_pct / 50, 1.0)
    
    # Proximity (25% weight)
    distance = calculate_distance(buyer.location, farmer_location)
    proximity_score = max(0, 1 - distance / 100)
    
    # Reliability (20% weight)
    reliability_score = buyer.reliability_score / 5.0
    
    # Payment terms (15% weight)
    payment_score = {'advance': 1.0, 'immediate': 0.9, '30days': 0.6}[buyer.payment_terms]
    
    total_score = (
        premium_score * 0.40 +
        proximity_score * 0.25 +
        reliability_score * 0.20 +
        payment_score * 0.15
    )
    
    return total_score * 100
```

**API Endpoints**:
```
GET /api/v1/explore/industry-buyers
Query params:
  - crop_id: required
  - farmer_quantity: required
  - farmer_quality_grade: required
  - farmer_location: required

Response:
{
  "matched_buyers": [
    {
      "buyer": IndustryBuyer,
      "premium_earnings": float,
      "distance_km": float,
      "certification_needed": [str]
    }
  ],
  "by_category": {
    "food_processing": int,
    "pharma": int,
    "export": int
  }
}

GET /api/v1/explore/certifications/{type}
Response: CertificationInfo
```

**Voice Output Format**:
```
"టమాటా సాస్ కంపెనీలు 30% ప్రీమియం ఇస్తాయి. 
Grade A నాణ్యత కావాలి. 
పులివెందుల లో XYZ ఫుడ్స్ ఉంది, ఫోన్: 9876543210. 
మీ 30 క్వింటాల్‌లకు ₹9,000 అదనపు ఆదాయం. 
FSSAI సర్టిఫికేషన్ కావాలి, FPO ద్వారా గ్రూప్ సర్టిఫికేషన్ పొందవచ్చు."

(Tomato sauce companies give 30% premium.
Need Grade A quality.
XYZ Foods in Pulivendula, phone: 9876543210.
₹9,000 extra income for your 30 quintals.
FSSAI certification needed, can get group certification through FPO.)
```

#### 3.3.7 Voice-Enabled Crop Exploration

**Purpose**: Enable hands-free crop exploration through voice interface

**Voice Query Processing**:
```python
class VoiceQueryProcessor:
    def __init__(self):
        self.lex_client = boto3.client('lex-runtime')
        self.transcribe_client = boto3.client('transcribe')
        self.polly_client = boto3.client('polly')
    
    def process_voice_query(self, audio_stream, farmer_id, session_id):
        # Step 1: Transcribe audio to text
        transcription = self.transcribe_audio(audio_stream, language='te-IN')
        
        # Step 2: Process intent with Lex
        lex_response = self.lex_client.post_text(
            botName='KrishiExploreBot',
            botAlias='prod',
            userId=farmer_id,
            sessionAttributes={'session_id': session_id},
            inputText=transcription
        )
        
        # Step 3: Extract intent and slots
        intent = lex_response['intentName']
        slots = lex_response['slots']
        
        # Step 4: Process query based on intent
        response_data = self.process_intent(intent, slots, farmer_id)
        
        # Step 5: Generate Telugu response text
        response_text = self.generate_response_text(intent, response_data)
        
        # Step 6: Convert to speech
        audio_response = self.text_to_speech(response_text, language='te-IN')
        
        return {
            "transcription": transcription,
            "intent": intent,
            "response_text": response_text,
            "audio_response": audio_response,
            "visual_data": response_data
        }
```

**Intent Definitions**:
```python
EXPLORE_INTENTS = {
    "SeasonalDemandIntent": {
        "utterances": [
            "ఏ పంటలకు డిమాండ్ ఎక్కువ",
            "ఈ సీజన్‌లో ఏ పంట పండించాలి",
            "డిమాండ్ ఉన్న పంటలు చూపించు"
        ],
        "slots": ["season"],
        "handler": "get_seasonal_demand"
    },
    
    "InvestmentQueryIntent": {
        "utterances": [
            "{crop} కు ఎంత పెట్టుబడి కావాలి",
            "{crop} పండించడానికి ఎంత ఖర్చు",
            "పెట్టుబడి లెక్కించు"
        ],
        "slots": ["crop", "acreage"],
        "handler": "calculate_investment"
    },
    
    "ProfitabilityQueryIntent": {
        "utterances": [
            "{crop} లో ఎంత లాభం",
            "{crop} ROI ఎంత",
            "లాభదాయకమైన పంటలు ఏవి"
        ],
        "slots": ["crop"],
        "handler": "calculate_roi"
    },
    
    "SuitabilityQueryIntent": {
        "utterances": [
            "నా భూమికి ఏ పంట బాగుంటుంది",
            "{crop} నా భూమికి సరిపోతుందా",
            "తక్కువ నీరు కావాల్సిన పంటలు"
        ],
        "slots": ["crop", "land_characteristic"],
        "handler": "check_suitability"
    },
    
    "ValueAdditionQueryIntent": {
        "utterances": [
            "{crop} ప్రాసెసింగ్ ఎలా చేయాలి",
            "అదనపు ఆదాయం ఎలా పొందాలి",
            "వాల్యూ అడిషన్ అవకాశాలు"
        ],
        "slots": ["crop"],
        "handler": "get_value_addition"
    },
    
    "ComparisonIntent": {
        "utterances": [
            "{crop1} మరియు {crop2} పోల్చు",
            "ఏది మంచిది {crop1} లేదా {crop2}",
            "రెండు పంటల తేడా చెప్పు"
        ],
        "slots": ["crop1", "crop2"],
        "handler": "compare_crops"
    }
}
```

**Context Management**:
```python
class ConversationContext:
    def __init__(self, session_id):
        self.session_id = session_id
        self.conversation_history = []
        self.current_crop = None
        self.current_intent = None
        self.farmer_preferences = {}
    
    def add_turn(self, user_input, system_response):
        self.conversation_history.append({
            "user": user_input,
            "system": system_response,
            "timestamp": datetime.now()
        })
    
    def get_context_for_query(self, query):
        # Extract context from recent conversation
        if "ఆ పంట" in query or "దాని గురించి" in query:
            # Reference to previous crop
            return {"crop": self.current_crop}
        
        return {}
    
    def update_context(self, intent, slots):
        if "crop" in slots:
            self.current_crop = slots["crop"]
        self.current_intent = intent

def handle_follow_up_question(query, context):
    # Resolve references
    if "మరింత చెప్పండి" in query:
        # Continue with current topic
        return expand_on_topic(context.current_intent, context.current_crop)
    
    if "పెట్టుబడి" in query and context.current_crop:
        # Investment question about current crop
        return calculate_investment(context.current_crop)
    
    if "లాభం" in query and context.current_crop:
        # Profitability question about current crop
        return calculate_roi(context.current_crop)
```

**Voice Feedback Collection**:
```python
def collect_voice_feedback(transaction_id, audio_stream):
    # Transcribe voice feedback
    transcription = transcribe_audio(audio_stream, language='te-IN')
    
    # Extract structured information using NLP
    feedback_data = extract_feedback_components(transcription)
    
    # Sentiment analysis
    sentiment = analyze_sentiment(transcription)
    
    # Store feedback
    feedback = ChannelFeedback(
        transaction_id=transaction_id,
        comment_telugu=transcription,
        sentiment=sentiment,
        **feedback_data
    )
    
    db.add(feedback)
    db.commit()
    
    # Send confirmation
    confirmation = "మీ ఫీడ్‌బ్యాక్ అందుకున్నాము. ధన్యవాదాలు!"
    return text_to_speech(confirmation, language='te-IN')

def extract_feedback_components(transcription):
    # Use NLP to extract structured data
    components = {}
    
    # Payment timeliness
    if "సమయానికి చెల్లించారు" in transcription:
        components['payment_on_time'] = True
    elif "ఆలస్యం" in transcription:
        components['payment_on_time'] = False
    
    # Price accuracy
    if "ధర సరైనది" in transcription or "కోట్ ప్రకారం" in transcription:
        components['price_matched_quote'] = True
    elif "తగ్గించారు" in transcription:
        components['price_matched_quote'] = False
    
    # Overall satisfaction
    if "చాలా బాగుంది" in transcription:
        components['overall_satisfaction_rating'] = 5
    elif "బాగుంది" in transcription:
        components['overall_satisfaction_rating'] = 4
    elif "సరే" in transcription:
        components['overall_satisfaction_rating'] = 3
    
    return components
```

---

## 4. Data Models

### 4.1 Core Entities

**Farmer Profile**:
```sql
CREATE TABLE farmers (
    id UUID PRIMARY KEY,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(100),
    village VARCHAR(100),
    mandal VARCHAR(100),
    district VARCHAR(100),
    primary_crops JSONB,  -- [crop_id]
    typical_quantities JSONB,  -- {crop_id: quantity}
    fpo_id UUID REFERENCES fpos(id),
    land_profile_id UUID REFERENCES land_profiles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_farmers_phone ON farmers(phone_number);
CREATE INDEX idx_farmers_mandal ON farmers(mandal);
CREATE INDEX idx_farmers_fpo ON farmers(fpo_id);
```

**Transaction Data**:
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    farmer_id UUID REFERENCES farmers(id),
    crop_id UUID NOT NULL,
    quantity_quintals DECIMAL(10,2) NOT NULL,
    price_per_quintal DECIMAL(10,2) NOT NULL,
    channel_id UUID REFERENCES channels(id),
    channel_type VARCHAR(50) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    quality_grade VARCHAR(10),
    payment_received_date TIMESTAMP,
    deductions_amount DECIMAL(10,2),
    transport_cost DECIMAL(10,2),
    net_earnings DECIMAL(12,2),
    farmer_reference VARCHAR(100),  -- anonymized
    location_village VARCHAR(100),
    location_mandal VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transactions_crop_mandal ON transactions(crop_id, location_mandal);
CREATE INDEX idx_transactions_date ON transactions(transaction_date DESC);
CREATE INDEX idx_transactions_channel ON transactions(channel_id);
```

**Demand Signals**:
```sql
CREATE TABLE demand_signals (
    id UUID PRIMARY KEY,
    buyer_id UUID REFERENCES buyers(id),
    crop_id UUID NOT NULL,
    quantity_needed_quintals DECIMAL(10,2) NOT NULL,
    price_range_min DECIMAL(10,2),
    price_range_max DECIMAL(10,2),
    location_village VARCHAR(100),
    location_mandal VARCHAR(100),
    location_lat DECIMAL(10,6),
    location_lon DECIMAL(10,6),
    urgency VARCHAR(20) CHECK (urgency IN ('URGENT', 'THIS_WEEK', 'THIS_MONTH')),
    quality_requirements JSONB,
    payment_terms VARCHAR(50),
    validity_end_date TIMESTAMP NOT NULL,
    contact_phone VARCHAR(15),
    verified BOOLEAN DEFAULT FALSE,
    fulfillment_status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_demand_crop_mandal ON demand_signals(crop_id, location_mandal);
CREATE INDEX idx_demand_status ON demand_signals(fulfillment_status, validity_end_date);
CREATE INDEX idx_demand_location ON demand_signals USING GIST(
    ll_to_earth(location_lat, location_lon)
);
```

**Channels**:
```sql
CREATE TABLE channels (
    id UUID PRIMARY KEY,
    channel_type VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    location_village VARCHAR(100),
    location_mandal VARCHAR(100),
    location_lat DECIMAL(10,6),
    location_lon DECIMAL(10,6),
    typical_price_ranges JSONB,  -- {crop_id: {min, max}}
    commission_pct DECIMAL(5,2),
    commission_fixed DECIMAL(10,2),
    payment_terms VARCHAR(100),
    operating_days JSONB,  -- ["Monday", "Tuesday", ...]
    operating_hours VARCHAR(50),
    contact_phone VARCHAR(15),
    reliability_score DECIMAL(3,2),  -- 0-5
    total_transactions INT DEFAULT 0,
    recent_activity_count INT DEFAULT 0,
    minimum_quantity DECIMAL(10,2),
    quality_requirements JSONB,
    crops_accepted JSONB,  -- [crop_id]
    verified BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity_date TIMESTAMP
);

CREATE INDEX idx_channels_type_mandal ON channels(channel_type, location_mandal);
CREATE INDEX idx_channels_location ON channels USING GIST(
    ll_to_earth(location_lat, location_lon)
);
```

**Crop Profiles**:
```sql
CREATE TABLE crop_profiles (
    id UUID PRIMARY KEY,
    crop_name_english VARCHAR(100) NOT NULL,
    crop_name_telugu VARCHAR(100) NOT NULL,
    crop_category VARCHAR(50),
    demand_level VARCHAR(20),
    demand_trend VARCHAR(20),
    peak_demand_months JSONB,  -- [1, 2, 3] for Jan, Feb, Mar
    demand_drivers JSONB,  -- ["Festival season", "Export window"]
    farmers_growing_count INT,
    total_acreage DECIMAL(12,2),
    average_yield_per_acre DECIMAL(10,2),
    success_rate_pct DECIMAL(5,2),
    common_challenges JSONB,
    expected_price_range_min DECIMAL(10,2),
    expected_price_range_max DECIMAL(10,2),
    price_volatility VARCHAR(20),
    summary_telugu TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_crop_profiles_demand ON crop_profiles(demand_level);
CREATE INDEX idx_crop_profiles_category ON crop_profiles(crop_category);
```

**Channel Feedback**:
```sql
CREATE TABLE channel_feedback (
    id UUID PRIMARY KEY,
    channel_id UUID REFERENCES channels(id),
    farmer_id UUID REFERENCES farmers(id),
    transaction_id UUID REFERENCES transactions(id),
    payment_timeliness_rating INT CHECK (payment_timeliness_rating BETWEEN 1 AND 5),
    price_accuracy_rating INT CHECK (price_accuracy_rating BETWEEN 1 AND 5),
    quality_assessment_rating INT CHECK (quality_assessment_rating BETWEEN 1 AND 5),
    overall_satisfaction_rating INT CHECK (overall_satisfaction_rating BETWEEN 1 AND 5),
    payment_on_time BOOLEAN,
    payment_delay_days INT,
    price_matched_quote BOOLEAN,
    price_difference_amount DECIMAL(10,2),
    quality_assessment_fair BOOLEAN,
    would_sell_again BOOLEAN,
    comment_telugu TEXT,
    issue_reported BOOLEAN DEFAULT FALSE,
    issue_category VARCHAR(100),
    issue_description TEXT,
    verified_transaction BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feedback_channel ON channel_feedback(channel_id, created_at DESC);
CREATE INDEX idx_feedback_verified ON channel_feedback(verified_transaction);
```

---

## 5. Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### 5.1 MVP Properties

**Property 1: Scenario Generation Completeness**
*For any* valid harvest input (crop, quantity, location, date, storage), the system SHALL generate exactly 2 scenarios (sell now, wait) within 10 seconds.
**Validates: Requirements 2.1, 2.5**

**Property 2: Risk-First Presentation**
*For any* generated scenario, risk factors SHALL be presented before price information in the output structure.
**Validates: Requirements 3.1, 3.6**

**Property 3: Channel Neutrality**
*For any* set of available channels, the system SHALL present all channels with equal prominence without ranking or recommendation.
**Validates: Requirements 4.1, 4.6**

**Property 4: Offline Data Freshness**
*For any* cached data item, the system SHALL display data age indicator when age exceeds 6 hours.
**Validates: Requirements 5.2, 5.3**

**Property 5: Uncertainty Communication**
*For any* scenario with data quality issues (age > 48 hours OR volatility > 15%), the system SHALL include explicit uncertainty statements.
**Validates: Requirements 6.1, 6.2, 6.3**

**Property 6: Privacy Preservation**
*For any* farmer data stored or transmitted, the system SHALL encrypt data in transit (TLS) and at rest (KMS).
**Validates: Requirements 16.1, 16.2**

**Property 7: Voice Recognition Accuracy**
*For any* voice input in Telugu, the system SHALL achieve >= 85% transcription accuracy for agricultural terms.
**Validates: Requirements 15.2, 20.2**

**Property 8: Voice Output Clarity**
*For any* scenario presented via voice, the system SHALL include all critical information (risks, prices, uncertainty) in the audio output.
**Validates: Requirements 15.3, 16.4**

### 5.2 Phase 2 Properties

**Property 9: Transaction Privacy**
*For any* transaction shared by a farmer, the system SHALL remove all PII (name, phone, exact address) before storage and display only anonymized reference.
**Validates: Requirements 21.6, 25.4**

**Property 10: Transaction Data Accuracy**
*For any* transaction data submitted, the system SHALL validate that price is within 3× of recent average and quantity is within typical range before accepting.
**Validates: Requirements 25.9, 25.10**

**Property 11: Demand Signal Verification**
*For any* demand signal posted, the system SHALL verify buyer identity through phone OTP, business registration, and FPO validation before making it visible to farmers.
**Validates: Requirements 22.8, 26.1**

**Property 12: Demand Matching Relevance**
*For any* farmer's crop and quantity, the system SHALL return only demand signals that match crop type, are within 50km radius, and have quantity within ±30% of farmer's quantity.
**Validates: Requirements 22.1, 22.2, 22.11**

**Property 13: Reliability Score Minimum Data**
*For any* channel, the system SHALL NOT display reliability score until minimum 5 verified transactions are recorded.
**Validates: Requirements 27.6**

**Property 14: Reliability Score Calculation**
*For any* channel with >= 5 feedbacks, the reliability score SHALL be calculated as weighted average: payment_timeliness (40%) + price_accuracy (30%) + quality_assessment (20%) + overall_satisfaction (10%).
**Validates: Requirements 27.2**

**Property 15: Fake Review Detection**
*For any* channel, if same farmer reviews same channel > 3 times OR all ratings are identical with > 10 reviews, the system SHALL flag for review.
**Validates: Requirements 27.16**

**Property 16: Pathway Cost Completeness**
*For any* pathway calculated, the system SHALL include all cost components: commission, transport, handling, testing, storage, and calculate net price after all deductions.
**Validates: Requirements 28.2, 28.3**

**Property 17: Pathway Ranking Accuracy**
*For any* set of pathways, the system SHALL rank by net profitability (highest net earnings first) unless farmer preferences specify alternative ranking.
**Validates: Requirements 28.5**

### 5.3 Phase 3 Properties

**Property 18: Seasonal Demand Accuracy**
*For any* crop and season, the demand level (HIGH/MEDIUM/LOW) SHALL be calculated based on weighted factors: market trends (30%) + buyer signals (25%) + export windows (20%) + processing demand (15%) + govt procurement (10%).
**Validates: Requirements 29.1**

**Property 19: Peer Activity Privacy**
*For any* peer planting activity shared, the system SHALL anonymize farmer identity and display only village-level location.
**Validates: Requirements 29.6**

**Property 20: Investment Calculation Completeness**
*For any* crop and acreage, the investment calculation SHALL include all cost categories: seeds, fertilizers, pesticides, irrigation, labor, equipment, and miscellaneous.
**Validates: Requirements 30.2**

**Property 21: Investment Savings Calculation**
*For any* farmer with own resources (seeds/equipment/labor), the system SHALL adjust investment calculation and show total savings amount.
**Validates: Requirements 30.8**

**Property 22: ROI Projection Data Requirement**
*For any* crop ROI projection, the system SHALL use minimum 3 years of historical yield and price data, and clearly communicate projection confidence level.
**Validates: Requirements 31.1, 31.4, 31.6**

**Property 23: Break-Even Calculation**
*For any* crop investment and expected prices/yields, the system SHALL calculate both break-even yield (minimum yield at expected price) and break-even price (minimum price at expected yield).
**Validates: Requirements 31.5**

**Property 24: Risk Factor Identification**
*For any* crop with price volatility > 40% OR yield variance > 30% OR spoilage rate > 15%, the system SHALL classify overall risk as HIGH and provide specific risk mitigation suggestions.
**Validates: Requirements 31.11, 31.12**

**Property 25: Land Suitability Scoring**
*For any* crop and farmer land profile, the suitability score SHALL be calculated with weights: soil type (25%) + pH (15%) + irrigation (30%) + drainage (15%) + climate (15%).
**Validates: Requirements 32.4**

**Property 26: Suitability Classification**
*For any* suitability score, the system SHALL classify as: HIGHLY SUITABLE (>= 80%), SUITABLE (>= 60%), MARGINALLY SUITABLE (>= 40%), NOT SUITABLE (< 40%).
**Validates: Requirements 32.4**

**Property 27: Value Addition Ranking**
*For any* set of value addition opportunities, the system SHALL rank by composite score: profitability (40%) + feasibility (30%) + market demand (20%) + buyer availability (10%).
**Validates: Requirements 33.3**

**Property 28: Industry Buyer Matching**
*For any* farmer's crop and quantity, the system SHALL return only industry buyers where farmer quantity >= minimum quantity AND farmer quality grade meets requirements.
**Validates: Requirements 34.2**

**Property 29: Premium Earnings Calculation**
*For any* matched industry buyer, the system SHALL calculate premium earnings as: (buyer_premium_price - current_market_price) × farmer_quantity.
**Validates: Requirements 34.2**

**Property 30: Voice Intent Recognition**
*For any* voice query in Telugu, the system SHALL recognize intent and extract slots with >= 85% accuracy for agricultural domain queries.
**Validates: Requirements 35.10**

**Property 31: Voice Context Preservation**
*For any* multi-turn voice conversation, the system SHALL maintain context (current crop, current intent) and resolve references like "ఆ పంట" (that crop).
**Validates: Requirements 35.6**

**Property 32: Voice Feedback Extraction**
*For any* voice feedback transcription, the system SHALL extract structured components (payment timeliness, price accuracy, satisfaction rating) using NLP.
**Validates: Requirements 36.3, 36.12**

---

## 6. Error Handling

### 6.1 Voice Input Errors

**Low Confidence Transcription**:
```python
def handle_low_confidence_transcription(transcription, confidence_score):
    if confidence_score < 0.70:
        # Ask for clarification
        return {
            "action": "clarify",
            "message_telugu": "క్షమించండి, నేను స్పష్టంగా అర్థం చేసుకోలేదు. దయచేసి మళ్ళీ చెప్పండి.",
            "fallback": "text_input"
        }
    elif confidence_score < 0.85:
        # Confirm understanding
        return {
            "action": "confirm",
            "message_telugu": f"మీరు {transcription} అన్నారా?",
            "options": ["అవును", "కాదు"]
        }
    else:
        return {"action": "proceed"}
```

**Noisy Environment**:
```python
def handle_noisy_environment(audio_stream):
    noise_level = detect_noise_level(audio_stream)
    
    if noise_level > 0.7:  # High noise
        return {
            "action": "suggest_retry",
            "message_telugu": "చాలా శబ్దం ఉంది. నిశ్శబ్ద ప్రదేశానికి వెళ్ళండి లేదా టెక్స్ట్ ఉపయోగించండి.",
            "fallback": "text_input"
        }
    elif noise_level > 0.5:  # Medium noise
        # Apply noise cancellation
        cleaned_audio = apply_noise_cancellation(audio_stream)
        return {"action": "retry_with_cleaned_audio", "audio": cleaned_audio}
    else:
        return {"action": "proceed"}
```

### 6.2 Data Quality Errors

**Missing Market Data**:
```python
def handle_missing_market_data(crop_id, mandal_id):
    # Try neighboring mandals
    nearby_mandals = get_nearby_mandals(mandal_id, radius_km=25)
    
    for nearby_mandal in nearby_mandals:
        data = get_market_data(crop_id, nearby_mandal)
        if data:
            return {
                "data": data,
                "warning_telugu": f"{nearby_mandal} నుండి డేటా ఉపయోగిస్తున్నాము. మీ ప్రాంతంలో ధరలు భిన్నంగా ఉండవచ్చు.",
                "confidence": "MEDIUM"
            }
    
    # Fallback to district-level data
    district_data = get_district_market_data(crop_id, mandal_id)
    if district_data:
        return {
            "data": district_data,
            "warning_telugu": "జిల్లా స్థాయి డేటా ఉపయోగిస్తున్నాము. స్థానిక ధరలు భిన్నంగా ఉండవచ్చు.",
            "confidence": "LOW"
        }
    
    # No data available
    return {
        "error": "no_data",
        "message_telugu": "ఈ పంటకు మార్కెట్ డేటా అందుబాటులో లేదు. దయచేసి తర్వాత ప్రయత్నించండి."
    }
```

**Stale Data**:
```python
def handle_stale_data(data, max_age_hours=48):
    age_hours = (datetime.now() - data.updated_at).total_seconds() / 3600
    
    if age_hours > max_age_hours:
        return {
            "use_data": True,
            "warning_telugu": f"ఈ డేటా {int(age_hours/24)} రోజుల పాతది. ప్రస్తుత పరిస్థితులు భిన్నంగా ఉండవచ్చు.",
            "confidence": "LOW",
            "data_age_days": int(age_hours / 24)
        }
    elif age_hours > 24:
        return {
            "use_data": True,
            "warning_telugu": "ఈ డేటా 1 రోజు పాతది.",
            "confidence": "MEDIUM",
            "data_age_days": 1
        }
    else:
        return {"use_data": True, "confidence": "HIGH"}
```

### 6.3 API Errors

**Rate Limiting**:
```python
def handle_rate_limit(user_id, endpoint):
    rate_limit = get_rate_limit(endpoint)
    current_usage = get_current_usage(user_id, endpoint)
    
    if current_usage >= rate_limit:
        return {
            "error": "rate_limit_exceeded",
            "message_telugu": "చాలా అభ్యర్థనలు. దయచేసి కొన్ని నిమిషాల తర్వాత ప్రయత్నించండి.",
            "retry_after_seconds": 60
        }
    
    return {"allowed": True}
```

**Service Unavailable**:
```python
def handle_service_unavailable(service_name):
    # Check if cached data can be used
    if service_name == "market_data":
        cached_data = get_cached_market_data()
        if cached_data:
            return {
                "use_cache": True,
                "data": cached_data,
                "warning_telugu": "తాజా డేటా అందుబాటులో లేదు. కాష్ చేసిన డేటా ఉపయోగిస్తున్నాము."
            }
    
    # Service critical, cannot proceed
    return {
        "error": "service_unavailable",
        "message_telugu": "సేవ తాత్కాలికంగా అందుబాటులో లేదు. దయచేసి కొద్దిసేపు తర్వాత ప్రయత్నించండి.",
        "retry": True
    }
```

### 6.4 Validation Errors

**Invalid Input**:
```python
def validate_harvest_input(crop_id, quantity, location, harvest_date, storage):
    errors = []
    
    if not crop_id or crop_id not in VALID_CROPS:
        errors.append("చెల్లని పంట రకం")
    
    if quantity <= 0 or quantity > 10000:
        errors.append("పరిమాణం 0 కంటే ఎక్కువ మరియు 10000 క్వింటాల్స్ కంటే తక్కువగా ఉండాలి")
    
    if not location or not is_valid_location(location):
        errors.append("చెల్లని స్థానం")
    
    if harvest_date > datetime.now():
        errors.append("పంట తేదీ భవిష్యత్తులో ఉండకూడదు")
    
    if (datetime.now() - harvest_date).days > 30:
        errors.append("పంట తేదీ 30 రోజుల కంటే పాతది")
    
    if storage not in ['open', 'covered', 'cold_storage']:
        errors.append("చెల్లని నిల్వ రకం")
    
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "message_telugu": "దయచేసి సరైన సమాచారం అందించండి: " + ", ".join(errors)
        }
    
    return {"valid": True}
```

---

## 7. Testing Strategy

### 7.1 Unit Testing

**Scope**: Individual functions and components

**Key Areas**:
- Scenario generation logic
- Risk calculation algorithms
- Price trend analysis
- Spoilage risk calculation
- Cost breakdown calculations
- ROI projection formulas
- Suitability scoring
- Reliability score calculation

**Example Unit Tests**:
```python
def test_calculate_spoilage_risk():
    # Test HIGH risk
    risk = calculate_spoilage_risk(
        crop_id="tomato",
        storage="open",
        days_since_harvest=3
    )
    assert risk.level == "HIGH"
    assert risk.percentage > 0.15
    
    # Test LOW risk
    risk = calculate_spoilage_risk(
        crop_id="onion",
        storage="covered",
        days_since_harvest=1
    )
    assert risk.level == "LOW"
    assert risk.percentage < 0.08

def test_investment_calculation():
    calc = calculate_investment(
        crop_id="tomato",
        acreage=2.0,
        irrigation_type="drip",
        farming_method="traditional",
        own_resources={"seeds": True}
    )
    
    assert calc.total_investment_min > 0
    assert calc.total_investment_max > calc.total_investment_min
    assert calc.total_savings > 0  # Because own seeds
    assert calc.seed_cost['min'] == 0  # Own seeds
```

### 7.2 Property-Based Testing

**Configuration**: Minimum 100 iterations per property test

**Property Test Framework**: Use `hypothesis` for Python

**Example Property Tests**:
```python
from hypothesis import given, strategies as st

@given(
    crop_id=st.sampled_from(VALID_CROPS),
    quantity=st.floats(min_value=1, max_value=1000),
    location=st.sampled_from(VALID_LOCATIONS),
    harvest_date=st.datetimes(min_value=datetime.now() - timedelta(days=7)),
    storage=st.sampled_from(['open', 'covered', 'cold_storage'])
)
def test_property_scenario_generation_completeness(crop_id, quantity, location, harvest_date, storage):
    """
    Feature: krishi, Property 1: Scenario Generation Completeness
    For any valid harvest input, system generates exactly 2 scenarios within 10 seconds
    """
    start_time = time.time()
    
    scenarios = generate_scenarios(crop_id, quantity, location, harvest_date, storage)
    
    elapsed_time = time.time() - start_time
    
    assert len(scenarios) == 2
    assert elapsed_time < 10
    assert scenarios[0].type == "sell_now"
    assert scenarios[1].type == "wait"

@given(
    transactions=st.lists(
        st.builds(Transaction,
            price_per_quintal=st.floats(min_value=100, max_value=5000),
            quantity_quintals=st.floats(min_value=1, max_value=500)
        ),
        min_size=1,
        max_size=100
    )
)
def test_property_transaction_privacy(transactions):
    """
    Feature: krishi, Property 9: Transaction Privacy
    For any transaction, system removes all PII before storage
    """
    for transaction in transactions:
        anonymized = anonymize_transaction(transaction)
        
        assert anonymized.farmer_name is None
        assert anonymized.farmer_phone is None
        assert anonymized.farmer_exact_address is None
        assert anonymized.farmer_reference.startswith("Farmer from")
        assert anonymized.location_village is not None  # Village-level OK
```

@given(
    feedbacks=st.lists(
        st.builds(ChannelFeedback,
            payment_timeliness_rating=st.integers(min_value=1, max_value=5),
            price_accuracy_rating=st.integers(min_value=1, max_value=5),
            quality_assessment_rating=st.integers(min_value=1, max_value=5),
            overall_satisfaction_rating=st.integers(min_value=1, max_value=5),
            verified_transaction=st.just(True)
        ),
        min_size=5,
        max_size=100
    )
)
def test_property_reliability_score_calculation(feedbacks):
    """
    Feature: krishi, Property 14: Reliability Score Calculation
    For any channel with >= 5 feedbacks, score is weighted average with specified weights
    """
    score = calculate_reliability_score_from_feedbacks(feedbacks)
    
    # Calculate expected score manually
    payment_avg = sum(f.payment_timeliness_rating for f in feedbacks) / len(feedbacks)
    price_avg = sum(f.price_accuracy_rating for f in feedbacks) / len(feedbacks)
    quality_avg = sum(f.quality_assessment_rating for f in feedbacks) / len(feedbacks)
    overall_avg = sum(f.overall_satisfaction_rating for f in feedbacks) / len(feedbacks)
    
    expected_score = (
        payment_avg * 0.40 +
        price_avg * 0.30 +
        quality_avg * 0.20 +
        overall_avg * 0.10
    )
    
    assert abs(score - expected_score) < 0.1  # Allow small floating point difference
    assert 0 <= score <= 5

@given(
    crop_id=st.sampled_from(VALID_CROPS),
    acreage=st.floats(min_value=0.5, max_value=50),
    own_resources=st.fixed_dictionaries({
        'seeds': st.booleans(),
        'equipment': st.booleans(),
        'labor_family': st.integers(min_value=0, max_value=5)
    })
)
def test_property_investment_savings_calculation(crop_id, acreage, own_resources):
    """
    Feature: krishi, Property 21: Investment Savings Calculation
    For any farmer with own resources, system adjusts investment and shows savings
    """
    calc = calculate_investment(crop_id, acreage, "borewell", "traditional", own_resources)
    
    if own_resources['seeds']:
        assert calc.seed_cost['min'] == 0
        assert calc.seed_cost['max'] == 0
        assert calc.total_savings > 0
    
    if own_resources['equipment']:
        assert calc.equipment_cost['min'] == 0
        assert calc.equipment_cost['max'] == 0
    
    if own_resources['labor_family'] > 0:
        # Labor cost should be reduced
        full_labor_calc = calculate_investment(crop_id, acreage, "borewell", "traditional", {'labor_family': 0})
        assert calc.labor_cost['min'] < full_labor_calc.labor_cost['min']

@given(
    crop_requirements=st.builds(CropRequirements,
        suitable_soil_types=st.lists(st.sampled_from(['red_soil', 'black_soil', 'sandy_loam']), min_size=1),
        ph_range_min=st.floats(min_value=5.0, max_value=6.5),
        ph_range_max=st.floats(min_value=6.5, max_value=8.0)
    ),
    land_profile=st.builds(FarmerLandProfile,
        soil_type=st.sampled_from(['red_soil', 'black_soil', 'sandy_loam', 'clay']),
        soil_ph=st.floats(min_value=4.0, max_value=9.0),
        irrigation_capacity=st.sampled_from(['adequate', 'limited', 'none'])
    )
)
def test_property_land_suitability_scoring(crop_requirements, land_profile):
    """
    Feature: krishi, Property 25: Land Suitability Scoring
    For any crop and land profile, suitability score uses specified weights
    """
    result = check_land_suitability_with_requirements(crop_requirements, land_profile)
    
    assert 0 <= result['score'] <= 100
    assert result['suitability'] in ['HIGHLY SUITABLE', 'SUITABLE', 'MARGINALLY SUITABLE', 'NOT SUITABLE']
    
    # Verify classification thresholds
    if result['score'] >= 80:
        assert result['suitability'] == 'HIGHLY SUITABLE'
    elif result['score'] >= 60:
        assert result['suitability'] == 'SUITABLE'
    elif result['score'] >= 40:
        assert result['suitability'] == 'MARGINALLY SUITABLE'
    else:
        assert result['suitability'] == 'NOT SUITABLE'
```

### 7.3 Integration Testing

**Scope**: End-to-end workflows across multiple components

**Key Workflows**:
1. Complete selling decision flow (voice input → scenario generation → channel display)
2. Transaction data collection and anonymization flow
3. Demand signal posting and matching flow
4. Reliability score calculation and display flow
5. Crop exploration with investment and ROI calculation flow
6. Voice-based crop query and response flow

**Example Integration Tests**:
```python
def test_selling_decision_workflow():
    # Step 1: Farmer provides harvest details via voice
    audio_input = load_test_audio("harvest_details_telugu.wav")
    transcription = transcribe_audio(audio_input)
    
    assert transcription.confidence > 0.85
    
    # Step 2: Extract harvest details
    harvest_details = extract_harvest_details(transcription.text)
    
    assert harvest_details.crop_id is not None
    assert harvest_details.quantity > 0
    
    # Step 3: Generate scenarios
    scenarios = generate_scenarios(**harvest_details)
    
    assert len(scenarios) == 2
    assert all(s.risks for s in scenarios)
    
    # Step 4: Get channel information
    channels = get_channels_for_crop(harvest_details.crop_id, harvest_details.location)
    
    assert len(channels) > 0
    
    # Step 5: Generate voice response
    response_text = format_scenarios_for_voice(scenarios, channels)
    audio_response = text_to_speech(response_text, language='te-IN')
    
    assert audio_response is not None

def test_demand_signal_matching_workflow():
    # Step 1: Buyer posts demand signal
    demand = create_demand_signal(
        buyer_id=test_buyer_id,
        crop_id="tomato",
        quantity_needed=50,
        price_range=(1000, 1200),
        location=test_location
    )
    
    # Step 2: Verify buyer
    verify_buyer(test_buyer_id)
    
    assert demand.verified == True
    
    # Step 3: Farmer searches for opportunities
    farmer_crop = "tomato"
    farmer_quantity = 45
    farmer_location = nearby_location
    
    matches = match_demand_signals(farmer_crop, farmer_quantity, farmer_location)
    
    # Step 4: Verify demand appears in matches
    assert any(m.id == demand.id for m in matches)
    
    # Step 5: Farmer contacts buyer
    contact_buyer(farmer_id=test_farmer_id, demand_id=demand.id)
    
    # Step 6: Track fulfillment
    mark_demand_fulfilled(demand.id)
    
    assert get_demand_signal(demand.id).fulfillment_status == 'completed'
```

### 7.4 Voice Testing

**Scope**: Voice recognition, dialogue management, and speech synthesis

**Test Data**: 
- 100+ Telugu audio samples covering agricultural terms
- Various accents and speaking speeds
- Noisy field environment recordings

**Key Metrics**:
- Transcription accuracy >= 85%
- Intent recognition accuracy >= 85%
- Response latency < 2 seconds
- Voice output clarity (subjective evaluation)

**Example Voice Tests**:
```python
def test_voice_recognition_accuracy():
    test_samples = load_telugu_audio_samples()
    
    correct_transcriptions = 0
    total_samples = len(test_samples)
    
    for sample in test_samples:
        transcription = transcribe_audio(sample.audio, language='te-IN')
        
        # Calculate word error rate
        wer = calculate_word_error_rate(transcription.text, sample.expected_text)
        
        if wer < 0.15:  # 85% accuracy threshold
            correct_transcriptions += 1
    
    accuracy = correct_transcriptions / total_samples
    assert accuracy >= 0.85

def test_voice_intent_recognition():
    test_queries = [
        ("ఏ పంటలకు డిమాండ్ ఎక్కువ", "SeasonalDemandIntent"),
        ("టమాటా కు ఎంత పెట్టుబడి కావాలి", "InvestmentQueryIntent"),
        ("టమాటా లో ఎంత లాభం", "ProfitabilityQueryIntent"),
        ("నా భూమికి ఏ పంట బాగుంటుంది", "SuitabilityQueryIntent")
    ]
    
    correct_intents = 0
    
    for query, expected_intent in test_queries:
        result = process_voice_query_text(query)
        
        if result.intent == expected_intent:
            correct_intents += 1
    
    accuracy = correct_intents / len(test_queries)
    assert accuracy >= 0.85
```

### 7.5 Performance Testing

**Load Testing**:
- Concurrent users: 100-500 farmers
- Scenario generation: < 10 seconds per request
- API response time: < 2 seconds for 95th percentile
- Voice call handling: 10+ concurrent calls

**Stress Testing**:
- Database query performance under load
- Cache hit rates and effectiveness
- AWS Lambda cold start times
- Amazon Connect call quality under load

---

## 8. Deployment and Operations

### 8.1 Infrastructure as Code

**AWS CDK Stack** (Python):
```python
class KrishiStack(Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # Lambda functions
        self.scenario_generator = lambda_.Function(
            self, "ScenarioGenerator",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="scenario.handler",
            code=lambda_.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            memory_size=512
        )
        
        # DynamoDB tables
        self.market_data_table = dynamodb.Table(
            self, "MarketData",
            partition_key={"name": "crop_id", "type": dynamodb.AttributeType.STRING},
            sort_key={"name": "timestamp", "type": dynamodb.AttributeType.NUMBER},
            billing_mode=dynamodb.BillingMode.ON_DEMAND
        )
        
        # RDS PostgreSQL
        self.database = rds.DatabaseInstance(
            self, "KrishiDB",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_15),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            vpc=self.vpc,
            multi_az=False  # MVP single AZ
        )
        
        # ElastiCache Redis
        self.cache = elasticache.CfnCacheCluster(
            self, "KrishiCache",
            cache_node_type="cache.t3.micro",
            engine="redis",
            num_cache_nodes=1
        )
```

### 8.2 Monitoring and Alerts

**CloudWatch Metrics**:
- API latency (p50, p95, p99)
- Error rates by endpoint
- Lambda invocation counts and durations
- Database connection pool usage
- Cache hit/miss rates
- Voice call quality metrics

**Alerts**:
- Error rate > 5% for 5 minutes
- API latency p95 > 3 seconds
- Database CPU > 80%
- Lambda concurrent executions > 80% of limit
- Cost exceeds daily budget

### 8.3 Cost Optimization

**Strategies**:
- Aggressive caching (Redis) to reduce database queries
- Lambda reserved concurrency to control costs
- DynamoDB on-demand billing for variable load
- S3 lifecycle policies for old call recordings
- CloudFront caching for static assets
- Optimize voice call duration (< 2 minutes average)

**Monthly Cost Breakdown** (MVP):
- Lambda: ₹5,000-8,000
- RDS t3.micro: ₹2,500-3,500
- DynamoDB: ₹3,000-5,000
- ElastiCache: ₹2,000-3,000
- Amazon Connect: ₹8,000-15,000 (voice calls)
- Amazon Transcribe/Polly: ₹3,000-6,000
- S3 + CloudFront: ₹1,000-2,000
- **Total: ₹25,000-45,000/month**

---

## 9. Security and Compliance

### 9.1 Data Encryption

- **In Transit**: TLS 1.2+ for all API communications
- **At Rest**: AWS KMS encryption for RDS, DynamoDB, S3
- **Voice Recordings**: Encrypted in S3 with customer-managed keys

### 9.2 Authentication and Authorization

- **Farmers**: Phone OTP via Amazon Cognito
- **Buyers**: Phone OTP + business verification
- **Admins**: IAM roles with MFA

### 9.3 Privacy

- **PII Handling**: Minimal collection, encrypted storage
- **Anonymization**: Remove PII before sharing transaction data
- **Data Deletion**: Farmers can request data deletion
- **Consent**: Explicit opt-in for data sharing

### 9.4 Compliance

- **Data Protection**: Follow applicable data protection regulations
- **Voice Recording**: Obtain consent before recording
- **Financial Data**: Secure handling of payment information
- **Audit Logs**: Track all data access and modifications

---

## 10. Future Enhancements

### 10.1 Machine Learning Models

**Phase 2+**:
- Price prediction models (LSTM/Prophet)
- Demand forecasting (time series analysis)
- Yield prediction (regression models)
- Quality grading (computer vision)

### 10.2 Advanced Features

**Phase 3+**:
- Weather-based risk alerts
- Pest and disease prediction
- Soil health monitoring integration
- Satellite imagery for crop monitoring
- Blockchain for supply chain transparency

### 10.3 Platform Expansion

**Future Phases**:
- iOS app
- Web dashboard for FPOs
- Multi-language support (Hindi, Tamil, Kannada)
- Multi-district and multi-state expansion
- Integration with government schemes
- Partnership with financial institutions for credit
