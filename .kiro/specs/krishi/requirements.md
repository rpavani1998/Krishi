# Requirements Document: Krishi – Sell Thoughtfully (MVP)

## 1. Overview

Krishi is a channel-neutral decision copilot that supports farmers at the critical moment of sale. Rather than telling farmers when or where to sell, Krishi explains what happens if they sell now versus waiting, what risks must be managed, and what remains uncertain. The system provides reasoning and risk assessment to help farmers sell thoughtfully while maintaining full control.

**MVP Focus**: Single district, regional language only, voice-first interaction (phone IVR + in-app voice) with text fallback (Android app + SMS/WhatsApp), 100-500 farmers via 1-2 FPOs, 4-week validation period.

## 2. Glossary

- **System**: Krishi - the channel-neutral decision copilot
- **Farmer**: Primary user who grows and harvests crops
- **FPO**: Farmer Producer Organization - collective that sponsors Krishi access
- **Mandi**: Traditional agricultural wholesale market (APMC)
- **Aggregator**: Intermediary who collects produce from multiple farmers
- **Trader**: Commission agent or wholesaler
- **Harvest_Batch**: A specific quantity of crop harvested at a particular time
- **Decision_Window**: Short time period (24-72 hours) when selling decision must be made
- **Scenario**: Explanation of what happens under a specific choice (sell now vs wait)
- **Risk_Factor**: Element that could affect outcome (spoilage, weather, transport)
- **Reasoning_Engine**: Component that generates scenario explanations and risk assessments
- **Uncertainty_Statement**: Explicit acknowledgment of what the system doesn't know
- **Loss_Reduction_Action**: Practical step farmers can take to minimize risk

## 3. Product Principles

All design and implementation decisions follow these core principles:

1. **Explain outcomes, not instructions** - Present scenarios, not commands
2. **Present risks before prices** - Lead with what could go wrong
3. **Communicate uncertainty clearly** - Be honest about limitations
4. **Work effectively with imperfect data** - Function with real-world data gaps
5. **Preserve farmer autonomy** - Farmer always makes final decision
6. **Maintain channel neutrality** - No bias toward any selling option
7. **Keep explanations simple and human** - Use farmer-friendly language

## 4. MVP Scope and Constraints

### 4.1 Geographic Scope
- **Region**: Single district only
- **Sub-regions**: Focus on 2-3 sub-regions with highest FPO engagement
- **Expansion**: Additional districts only after MVP validation

### 4.2 User Scope
- **Target**: 100-500 farmers
- **Access**: Via 1-2 FPO sponsors
- **Duration**: 4 weeks of live usage for validation

### 4.3 Language Scope
- **Primary Language**: Regional language only (e.g., Telugu, Hindi, Tamil)
- **Terminology**: Local agricultural terms
- **Future**: Additional languages in Phase 2

### 4.4 Crop Scope
- **Crops**: Multiple crops commonly grown in target district (e.g., tomatoes, onions, chillies, groundnut)
- **Approach**: Crop-agnostic rules with crop-specific spoilage data
- **Expansion**: Crop-specific models in Phase 2

### 4.5 Interaction Channels (MVP)
- **Primary**: Android mobile app (offline-capable, text + voice)
- **Voice**: Phone calls via IVR (Amazon Connect), in-app voice
- **Secondary**: SMS and WhatsApp (text-based)
- **Out of Scope**: iOS app, web dashboard

### 4.6 Cost Constraints
- **Target**: ₹25,000 - ₹45,000 per month (~$300-550/month)
- **Approach**: Serverless architecture, voice services, minimal AI costs
- **Optimization**: Use simple models, cache aggressively, optimize call duration

## 5. Core Requirements

### Requirement 1: Voice-First Farmer Input (MVP)

**User Story:** As a farmer at harvest time, I want to share my crop details through voice (phone call or app), so that I can get guidance quickly without typing.

#### Acceptance Criteria

1. WHEN a farmer calls the toll-free number, THE System SHALL provide voice input capability in regional language for crop type, quantity, location, harvest date, and storage conditions
2. WHEN a farmer speaks in the regional language, THE System SHALL recognize and process the input using Amazon Transcribe
3. WHEN voice input is unclear or incomplete, THE System SHALL ask clarifying questions through natural dialogue
4. WHEN voice input is successfully captured, THE System SHALL confirm understanding by repeating key details back to the farmer
5. THE System SHALL support both phone calls (IVR via Amazon Connect) and in-app voice input
6. THE System SHALL support fallback to text input when voice is not practical or preferred
7. THE System SHALL handle noisy field environments with noise cancellation
8. THE System SHALL provide voice output using Amazon Polly in regional language

**MVP Implementation**: Phone IVR + in-app voice, regional language support, noise handling

---

### Requirement 2: Text-Based Input (Alternative Channel)

**User Story:** As a farmer who prefers text, I want to share my crop details through text input, so that I have an alternative to voice.

#### Acceptance Criteria

1. WHEN a farmer accesses the Android app, THE System SHALL provide text input fields for crop type, quantity, location, harvest date, and storage conditions
2. WHEN a farmer submits incomplete information, THE System SHALL ask follow-up questions to gather missing details
3. WHEN a farmer enters invalid data, THE System SHALL reject the input with clear error messages in regional language
4. WHEN harvest details are successfully submitted, THE System SHALL confirm receipt and proceed to generate scenarios
5. THE System SHALL support SMS/WhatsApp input for feature phone users
6. THE System SHALL present all content in regional language

**MVP Implementation**: Text input as alternative to voice, SMS/WhatsApp support

---

### Requirement 2: Scenario-Based Reasoning Engine

**User Story:** As a farmer facing a selling decision, I want to understand what happens if I sell now versus waiting, so that I can make an informed choice.

#### Acceptance Criteria

1. WHEN harvest details are received, THE Reasoning_Engine SHALL generate exactly two scenarios: "sell now" and "wait briefly" (24-72 hours)
2. WHEN generating scenarios, THE Reasoning_Engine SHALL analyze directional price signals, spoilage risk, weather risk, and transport availability
3. WHEN presenting scenarios, THE Reasoning_Engine SHALL explain practical loss-reduction actions for each option
4. WHEN data is weak or uncertain, THE Reasoning_Engine SHALL explicitly state what is uncertain and why
5. THE Reasoning_Engine SHALL complete scenario generation within 10 seconds for real-time decision support
6. THE Reasoning_Engine SHALL use simple rule-based logic for risk calculations and Generative AI (AWS Bedrock) for explanation generation

**MVP Simplification**: Rule-based logic for numbers, AWS Bedrock (Claude Haiku) for text explanations

---

### Requirement 3: Risk-First Explanation Output

**User Story:** As a farmer, I want to understand the risks and trade-offs of my selling options, so that I can make decisions that protect my income.

#### Acceptance Criteria

1. WHEN scenarios are generated, THE System SHALL present risk factors for each option including spoilage probability, weather impact, and transport reliability
2. WHEN explaining scenarios, THE System SHALL use plain Telugu language and avoid technical jargon
3. WHEN showing price information, THE System SHALL present directional signals (rising, falling, stable) rather than specific predictions
4. WHEN displaying cost information, THE System SHALL show approximate local cost ranges in rupees
5. THE System SHALL clearly distinguish between what is known, what is estimated, and what is uncertain
6. THE System SHALL structure all explanations as: Key risks → Possible outcomes → Loss-reduction actions → What is uncertain

**MVP Simplification**: Simple risk categories (LOW, MEDIUM, HIGH), directional price signals only

---

### Requirement 4: Channel-Neutral Information Provision

**User Story:** As a farmer, I want unbiased information about all my selling options, so that I can trust the system is working in my interest.

#### Acceptance Criteria

1. WHEN presenting selling channels, THE System SHALL provide information about all available options: mandis, traders, aggregators, direct buyers
2. WHEN explaining channel characteristics, THE System SHALL include typical price ranges, deductions/commissions, payment timelines, and reliability concerns
3. WHEN farmers ask about specific channels, THE System SHALL provide factual information without steering toward any particular choice
4. THE System SHALL NOT execute transactions, take commissions, or have financial relationships with any selling channel
5. THE System SHALL clearly communicate its channel-neutral position to build farmer trust
6. THE System SHALL present channels neutrally without ranking or promotion

**MVP Simplification**: Basic channel information (price ranges, commissions, payment terms), no complex reliability scoring

---

### Requirement 5: Offline-First Mobile Architecture

**User Story:** As a farmer in a rural area with unreliable connectivity, I want to access decision support even when offline, so that I can get guidance when I need it most.

#### Acceptance Criteria

1. WHEN internet connectivity is unavailable, THE System SHALL allow farmers to input harvest data offline and generate basic scenarios using cached market data
2. WHEN operating offline, THE System SHALL clearly indicate which information is cached and how recent it is (e.g., "Market data from 2 days ago")
3. WHEN connectivity is restored, THE System SHALL automatically sync offline data and update scenarios with current market information
4. WHEN bandwidth is limited, THE System SHALL prioritize essential data transfer and compress all communications
5. THE System SHALL cache regional market data (7-day history), crop-specific spoilage models, and weather patterns for offline operation
6. THE System SHALL use SQLite for local storage on Android devices

**MVP Simplification**: Basic offline caching (7 days), simple sync logic, no conflict resolution

---

### Requirement 6: Transparent Uncertainty Communication

**User Story:** As a farmer, I want to know what the system is uncertain about, so that I can factor that into my decision and trust the system's honesty.

#### Acceptance Criteria

1. WHEN data quality is poor or incomplete, THE System SHALL explicitly state what information is missing and how it affects the analysis
2. WHEN making estimates or projections, THE System SHALL clearly label them as estimates and explain the basis
3. WHEN market conditions are volatile or unpredictable, THE System SHALL acknowledge the uncertainty rather than providing false precision
4. WHEN historical patterns are weak or absent, THE System SHALL inform farmers that predictions are less reliable
5. THE System SHALL use phrases like "మాకు తెలియదు" (we don't know), "ఇది అనిశ్చితం" (this is uncertain) in Telugu when appropriate
6. THE System SHALL always indicate data age (e.g., "2 రోజుల క్రితం డేటా" - data from 2 days ago)

**MVP Simplification**: Simple uncertainty flags (HIGH, MEDIUM, LOW), clear data age indicators

---

### Requirement 7: Imperfect Data Handling

**User Story:** As a system operator, I want the system to work with messy rural data, so that it provides value even when perfect information is unavailable.

#### Acceptance Criteria

1. WHEN market data is incomplete or outdated, THE System SHALL use directional trends and historical patterns to provide useful guidance
2. WHEN integrating multiple data sources with conflicts, THE System SHALL apply data quality scoring and explain which sources are more reliable
3. WHEN regional data is sparse, THE System SHALL use neighboring mandal data with appropriate caveats about applicability
4. WHEN real-time data is unavailable, THE System SHALL clearly indicate data age and adjust scenario explanations accordingly
5. THE System SHALL prioritize providing honest, qualified guidance over refusing to help due to imperfect data
6. THE System SHALL function with data gaps of up to 3 days for non-critical information

**MVP Simplification**: Use neighboring mandal data when local data unavailable, simple data quality flags

---

### Requirement 8: Farmer Decision Autonomy

**User Story:** As a farmer, I want to maintain full control over my selling decisions, so that the system supports rather than replaces my judgment.

#### Acceptance Criteria

1. THE System SHALL present scenarios and information without prescribing specific actions or decisions
2. WHEN farmers make choices different from system scenarios, THE System SHALL respect those decisions without warnings or discouragement
3. WHEN farmers request additional information or alternative scenarios, THE System SHALL provide them without judgment
4. WHEN tracking outcomes, THE System SHALL learn from farmer decisions to improve future scenario quality
5. THE System SHALL frame all output as "ఇది మేము చూస్తున్నది" (here's what we see) rather than "మీరు ఇలా చేయాలి" (you should do this)
6. THE System SHALL never use imperative language or commands

**MVP Simplification**: Simple observational framing, basic outcome tracking

---

### Requirement 9: Single District MVP Scope

**User Story:** As a product manager, I want to start with one district, so that we can validate the approach before scaling.

#### Acceptance Criteria

1. WHEN launching MVP, THE System SHALL focus on single district only to ensure deep accuracy
2. WHEN farmers outside target district attempt to use the system, THE System SHALL clearly communicate current geographic limitations in regional language
3. WHEN the district deployment is validated, THE System SHALL support expansion to additional districts
4. WHEN expanding scope, THE System SHALL maintain the same quality standards and trust-building approach
5. THE System SHALL collect feedback and outcome data from MVP to inform expansion strategy
6. THE System SHALL support 2-3 sub-regions within target district for MVP

**MVP Simplification**: Single district only, 2-3 sub-regions, no multi-region support

---

### Requirement 10: FPO-Sponsored Access Model

**User Story:** As an FPO manager, I want to provide Krishi access to our member farmers, so that they make better decisions and reduce losses.

#### Acceptance Criteria

1. WHEN FPOs subscribe to the system, THE System SHALL provide access credentials for their member farmers at no cost to farmers
2. WHEN tracking usage, THE System SHALL provide FPOs with aggregate outcome data (loss reduction, decision quality) without revealing individual farmer details
3. WHEN farmers use the system, THE System SHALL maintain complete neutrality regardless of who sponsors their access
4. WHEN FPOs request reports, THE System SHALL show metrics like distress sales avoided, spoilage reduction, and decision confidence trends
5. THE System SHALL support 1-2 FPO sponsors in MVP
6. THE System SHALL provide simple CSV reports for FPO administrators

**MVP Simplification**: Basic FPO dashboard with aggregate metrics, simple CSV exports

---

### Requirement 11: Decision Outcome Learning

**User Story:** As a system operator, I want to learn from actual farmer decisions and outcomes, so that the system improves over time.

#### Acceptance Criteria

1. WHEN farmers make selling decisions, THE System SHALL track what scenarios were presented, what farmers chose, and what actually happened
2. WHEN outcomes are known, THE System SHALL analyze the accuracy of risk assessments and scenario explanations
3. WHEN patterns emerge from outcomes, THE System SHALL update crop-specific and region-specific parameters to improve future scenarios
4. WHEN learning from outcomes, THE System SHALL preserve farmer privacy by using only anonymized decision and outcome data
5. THE System SHALL create a compounding decision intelligence layer that becomes more accurate with each harvest cycle
6. THE System SHALL collect outcome data through simple follow-up SMS (optional for farmers)

**MVP Simplification**: Basic outcome tracking, manual analysis, simple parameter updates

---

### Requirement 12: Short Decision Window Focus

**User Story:** As a farmer at harvest time, I want guidance focused on immediate decisions (24-72 hours), so that I can act during my actual selling window.

#### Acceptance Criteria

1. WHEN generating scenarios, THE System SHALL focus on decision windows of 24-72 hours from the current moment
2. WHEN presenting "wait" scenarios, THE System SHALL specify the recommended wait duration within the 24-72 hour window
3. WHEN decision windows expire, THE System SHALL prompt farmers to provide updated harvest status for new scenario generation
4. WHEN time-sensitive risks emerge (weather changes, market shifts), THE System SHALL notify farmers via SMS
5. THE System SHALL avoid long-term predictions beyond the immediate decision window to maintain accuracy and trust
6. THE System SHALL send SMS alerts for urgent risks (rain forecast, sudden price drops)

**MVP Simplification**: Fixed 24h, 48h, 72h wait options, simple SMS alerts for urgent risks

---

### Requirement 13: Loss-Reduction Action Guidance

**User Story:** As a farmer, I want practical advice on reducing losses, so that I can protect my income regardless of when I sell.

#### Acceptance Criteria

1. WHEN presenting scenarios, THE System SHALL include 2-3 specific loss-reduction actions relevant to each option (drying, storage, handling techniques)
2. WHEN suggesting actions, THE System SHALL provide approximate local cost ranges in rupees for implementing each action
3. WHEN actions require specific conditions, THE System SHALL explain what's needed (shade, ventilation, containers) in practical Telugu terms
4. WHEN farmers ask about loss-reduction methods, THE System SHALL provide detailed guidance based on crop type and local conditions
5. THE System SHALL prioritize low-cost, high-impact actions that farmers can implement immediately
6. THE System SHALL use local agricultural terminology familiar to Kadapa farmers

**MVP Simplification**: Pre-defined loss-reduction actions per crop, simple cost ranges (₹50-100, ₹100-200, etc.)

---

### Requirement 14: Trust-Building Through Honesty

**User Story:** As a farmer, I want the system to be honest about its limitations, so that I can trust it as a reliable advisor.

#### Acceptance Criteria

1. WHEN data is insufficient for confident analysis, THE System SHALL say "we don't have enough information" in regional language rather than guessing
2. WHEN predictions are uncertain, THE System SHALL use phrases like "this is our estimate" or "this could change" in regional language
3. WHEN the system makes errors in past scenarios, THE System SHALL acknowledge them and explain what was learned
4. WHEN farmers provide feedback that contradicts system scenarios, THE System SHALL thank them and incorporate the learning
5. THE System SHALL never overstate certainty or hide limitations to maintain long-term farmer trust
6. THE System SHALL display data freshness prominently (e.g., "2 days ago" in regional language)

**MVP Simplification**: Simple honesty phrases in regional language, clear data age indicators

---

### Requirement 15: Regional Language Voice Support (MVP)

**User Story:** As a farmer who speaks a regional language, I want to interact with the system in my language through voice, so that I can use it naturally.

#### Acceptance Criteria

1. THE System SHALL support voice input and output in regional language (Telugu for MVP)
2. WHEN processing voice input, THE System SHALL handle regional accents and agricultural terminology specific to the language
3. WHEN generating voice output, THE System SHALL use natural speech patterns and culturally appropriate communication styles using Amazon Polly
4. WHEN farmers call via phone, THE System SHALL provide IVR menu in regional language
5. THE System SHALL support text fallback for any language when voice recognition confidence is low
6. THE System SHALL handle noisy field environments with appropriate noise cancellation
7. THE System SHALL provide voice confirmation of understood inputs

**MVP Implementation**: Regional language voice (Telugu), Amazon Transcribe + Polly, Amazon Connect IVR

---

### Requirement 16: Conversational Voice Interface (MVP)

**User Story:** As a farmer working in the field, I want to interact with the system through natural conversation, so that I can get guidance hands-free.

#### Acceptance Criteria

1. THE System SHALL provide a conversational voice interface optimized for noisy field environments
2. WHEN farmers ask questions, THE System SHALL respond with voice output in the farmer's chosen language
3. WHEN presenting complex information, THE System SHALL break explanations into digestible voice segments with natural pauses
4. WHEN farmers interrupt or ask clarifying questions, THE System SHALL handle conversational flow naturally using Amazon Lex
5. THE System SHALL support both voice-only (phone call) and voice-plus-visual modes (app)
6. THE System SHALL maintain conversation context across multiple turns
7. THE System SHALL provide option to receive SMS summary after voice interaction

**MVP Implementation**: Amazon Lex for dialogue management, context preservation, multi-turn conversations

---

### Requirement 17: Phone IVR System (MVP)

**User Story:** As a farmer without a smartphone, I want to call a toll-free number to get guidance, so that I can access Krishi from any phone.

#### Acceptance Criteria

1. THE System SHALL provide a toll-free phone number for farmers to call
2. WHEN a farmer calls, THE System SHALL greet them in regional language and guide them through the process
3. WHEN collecting information, THE System SHALL use voice prompts and DTMF (keypad) fallback
4. WHEN generating scenarios, THE System SHALL read them out clearly with option to repeat
5. THE System SHALL send SMS summary after call completion
6. THE System SHALL record calls for quality and training purposes (with consent)
7. THE System SHALL handle concurrent calls (up to 10 simultaneous calls for MVP)

**MVP Implementation**: Amazon Connect for IVR, toll-free number, call recording, SMS follow-up

---

### Requirement 16: Data Privacy and Security

**User Story:** As a farmer, I want my personal and harvest data to be protected, so that I can use the system without privacy concerns.

#### Acceptance Criteria

1. WHEN collecting farmer data, THE System SHALL encrypt all personal and harvest information in transit and at rest
2. WHEN storing data, THE System SHALL implement access controls ensuring only authorized personnel can view farmer information
3. WHEN farmers request data deletion, THE System SHALL remove all personal information while preserving anonymized analytics
4. WHEN sharing data with FPO sponsors, THE System SHALL provide only aggregate metrics without individual farmer details
5. THE System SHALL comply with applicable data protection regulations
6. THE System SHALL use AWS encryption services (KMS) for data protection
7. WHEN recording voice calls, THE System SHALL obtain consent and store recordings securely

**MVP Simplification**: Basic encryption (TLS, KMS), simple access controls, manual data deletion process, secure call recording

---

### Requirement 17: Multi-Stakeholder Profiles

**User Story:** As a system administrator, I want to support different user types with appropriate access levels, so that the system serves all stakeholders effectively.

#### Acceptance Criteria

1. THE System SHALL support four user types: Farmers, Aggregators/Traders, Mandis, FPO Administrators
2. WHEN a Farmer profile is created, THE System SHALL store name, village, mandal, primary crops, typical quantities
3. WHEN an Aggregator profile is created, THE System SHALL store operating region, crops of interest, buying quantities, contact info, payment practices
4. WHEN a Mandi profile is created, THE System SHALL store location, operating days, common crops, fee structure
5. WHEN an FPO Administrator profile is created, THE System SHALL provide access to onboard farmers, view aggregate insights, manage permissions
6. THE System SHALL ensure Farmers cannot see other farmers' data
7. THE System SHALL ensure Aggregators cannot see individual farmer decision data or influence recommendations
8. THE System SHALL ensure Mandis are informational only and maintained by administrators

**MVP Simplification**: Basic profile types, simple role-based access control, manual profile creation

---

### Requirement 18: SMS/WhatsApp Integration

---

### Requirement 18: SMS/WhatsApp Integration

**User Story:** As a farmer with a feature phone, I want to receive guidance via SMS/WhatsApp, so that I can use Krishi without a smartphone.

#### Acceptance Criteria

1. THE System SHALL support SMS input for harvest details using structured format
2. THE System SHALL send scenario summaries via SMS in Telugu (max 160 characters per message)
3. THE System SHALL support WhatsApp for richer content delivery (images, formatted text)
4. WHEN farmers send SMS queries, THE System SHALL respond within 30 seconds
5. THE System SHALL use SMS for urgent alerts (weather risks, market changes)
6. THE System SHALL keep SMS costs under ₹2 per farmer per month

**MVP Simplification**: Basic SMS/WhatsApp integration, simple message templates, no complex conversational flow

---

### Requirement 19: Cost-Efficient Infrastructure

**User Story:** As a product manager, I want to keep operating costs low, so that the MVP is financially sustainable.

#### Acceptance Criteria

1. THE System SHALL target monthly operating costs of ₹25,000 - ₹45,000 ($300-550) including voice services
2. THE System SHALL use AWS serverless architecture (Lambda, API Gateway, DynamoDB) to minimize costs
3. THE System SHALL use simple rule-based logic instead of expensive ML models in MVP
4. THE System SHALL cache aggressively to reduce API calls and compute costs
5. THE System SHALL use AWS Free Tier where possible
6. THE System SHALL monitor costs daily and alert if exceeding budget
7. THE System SHALL optimize voice call duration to minimize Amazon Connect costs

**MVP Simplification**: Serverless-only, no SageMaker, no complex ML, aggressive caching, optimized call flows

---

### Requirement 20: Voice Call Quality and Performance

**User Story:** As a farmer calling for guidance, I want clear voice quality and quick responses, so that I can understand the information easily.

#### Acceptance Criteria

1. THE System SHALL maintain voice call quality with minimal latency (< 2 seconds for responses)
2. WHEN processing voice input, THE System SHALL achieve 85%+ accuracy for regional language recognition
3. WHEN generating voice output, THE System SHALL use natural-sounding voices with appropriate pace
4. WHEN handling multiple calls, THE System SHALL support up to 10 concurrent calls without degradation
5. THE System SHALL handle call drops gracefully and allow farmers to resume
6. THE System SHALL provide option to slow down or repeat information
7. THE System SHALL complete scenario generation and delivery within 30 seconds during call

**MVP Implementation**: Amazon Connect for quality, Amazon Transcribe for accuracy, Amazon Polly for natural voice, call resumption logic

---

## 6. MVP Success Criteria

The MVP will be considered successful if:

1. **Farmer Adoption**: 70%+ of onboarded farmers use Krishi at least once during harvest
2. **Clarity Improvement**: 80%+ of farmers report improved clarity during selling decisions
3. **Risk Awareness**: 75%+ of farmers can articulate key risks after using Krishi
4. **Trust**: 85%+ of farmers trust the system's neutrality and honesty
5. **Loss Reduction**: FPOs observe measurable reduction in distress selling
6. **Cost**: Operating costs stay within ₹17,000 - ₹33,000 per month
7. **Performance**: 95%+ of scenarios generated within 10 seconds
8. **Accuracy**: 70%+ directional price accuracy for 24-48 hour windows

## 7. Phase 2 Enhancements (Post-MVP)

After successful MVP validation, Phase 2 will include:

- Multi-language support (additional regional languages)
- Multi-district expansion (3-5 districts)
- ML models for better predictions
- Advanced analytics for FPOs
- Real-time data integration
- Enhanced offline capabilities
- iOS app
- Web dashboard

---


---

## 8. Phase 2 Requirements (Post-MVP)

After successful MVP validation, Phase 2 will introduce enhanced features that provide social proof, market intelligence, and network transparency.

### Requirement 21: Recent Transaction Intelligence

**User Story:** As a farmer, I want to see what nearby farmers recently sold their crops for, so that I can understand realistic price expectations and validate my selling decisions.

#### Acceptance Criteria

1. WHEN viewing scenarios, THE System SHALL display 5-10 recent transactions from the same mandal/district for the same crop within the last 14 days
2. WHEN showing transaction data, THE System SHALL include crop type, quantity (in quintals), sale price (per quintal), channel used (mandi/aggregator/trader/direct), location (village name), transaction date, quality grade (if available), and anonymized farmer reference (e.g., "Farmer from Pulivendula")
3. WHEN transaction data is older than 3 days, THE System SHALL display age indicator (e.g., "5 days ago") in Telugu
4. WHEN transaction data is older than 7 days, THE System SHALL display prominent warning about data freshness
5. WHEN no recent transactions exist for the crop, THE System SHALL display transactions from neighboring mandals with clear geographic indicator
6. THE System SHALL preserve farmer privacy by removing all personally identifiable information (name, phone, exact address)
7. THE System SHALL allow farmers to opt-in to share their transaction data with explicit consent
8. WHEN displaying in voice mode, THE System SHALL summarize key insights: "గత వారంలో 8 మంది రైతులు టమాటాలను క్వింటాల్‌కు ₹800-₹1200 కు అమ్మారు" (In the last week, 8 farmers sold tomatoes for ₹800-₹1200 per quintal)
9. THE System SHALL calculate and display average price, minimum price, maximum price, and most common channel from recent transactions
10. WHEN displaying transaction list, THE System SHALL sort by date (most recent first) with option to sort by price
11. THE System SHALL highlight transactions that match farmer's quantity range (±20%)
12. WHEN farmer taps on a transaction, THE System SHALL show detailed breakdown including all costs and net price received

**Phase 2 Implementation**: Weeks 5-6 after MVP launch

---

### Requirement 22: Demand Intelligence

**User Story:** As a farmer, I want to see where my crop is in demand and what quantities buyers need, so that I can target my selling efforts effectively and connect with buyers directly.

#### Acceptance Criteria

1. WHEN viewing scenarios, THE System SHALL display active demand signals for the farmer's crop within 50km radius, sorted by distance
2. WHEN showing demand data, THE System SHALL include buyer type (aggregator/processor/exporter/trader), buyer name, location (village/town), quantity needed (in quintals), expected price range (per quintal), urgency level (URGENT/THIS_WEEK/THIS_MONTH), quality requirements (Grade A/B/C, moisture %, size), payment terms (immediate/7 days/15 days/30 days), and verified contact info (phone number)
3. WHEN multiple demand signals exist for the same crop, THE System SHALL prioritize by: (1) geographic proximity, (2) price competitiveness, (3) urgency level, (4) buyer reliability score, (5) payment terms
4. WHEN demand is low or absent, THE System SHALL clearly communicate "ప్రస్తుతం మీ పంటకు డిమాండ్ సిగ్నల్స్ లేవు" (Currently no demand signals for your crop) and suggest checking again in 24 hours
5. WHEN demand signals are older than 24 hours, THE System SHALL display age indicator and mark as potentially outdated
6. THE System SHALL update demand data every 6 hours through buyer submissions and aggregator integrations
7. WHEN displaying in voice mode, THE System SHALL summarize top 2-3 opportunities: "పులివెందుల లో ఒక ఎగ్జిపోర్టర్ 50 క్వింటాల్ టమాటాలు కావాలి, క్వింటాల్‌కు ₹1000-₹1200, 3 రోజుల్లో చెల్లింపు" (An exporter in Pulivendula needs 50 quintals of tomatoes, ₹1000-₹1200 per quintal, payment in 3 days)
8. THE System SHALL verify buyer identity through phone verification, business registration check, and FPO validation before displaying demand signals
9. WHEN farmer taps on demand signal, THE System SHALL show full details with "Call Now" button, "Send SMS" button, and "Get Directions" button
10. THE System SHALL track demand fulfillment (farmer contacted buyer, sale completed) to improve buyer reliability scores
11. WHEN demand quantity matches farmer's harvest quantity (±30%), THE System SHALL highlight the demand signal as "Good Match"
12. THE System SHALL allow farmers to mark demand signals as "Contacted", "Interested", or "Not Relevant" to improve future recommendations
13. WHEN buyer has high reliability score (4+ stars), THE System SHALL display "Verified Buyer" badge
14. THE System SHALL show demand trend indicator (increasing/stable/decreasing) based on historical demand patterns

**Phase 2 Implementation**: Weeks 7-8 after MVP launch

---

### Requirement 23: Network Visualization

**User Story:** As a farmer, I want to see all available selling channels and how they connect, so that I can understand my options, compare pathways, and choose the best route to market.

#### Acceptance Criteria

1. WHEN viewing channel options, THE System SHALL display all mandis (with names and locations), aggregators (with operating areas), traders (with specializations), and direct buyers (processors/exporters) within 100km radius
2. WHEN showing network connections, THE System SHALL indicate for each channel: location (village/town with distance), typical price ranges for farmer's crop (per quintal), commission/fees (percentage or fixed amount), payment terms (immediate/days), reliability score (0-5 stars), contact information (phone number), and operating hours/days
3. WHEN a channel has recent activity (transactions in last 7 days), THE System SHALL highlight it with "Active" badge and show transaction count
4. WHEN a channel is new (< 30 days in system) or unverified (< 5 transactions), THE System SHALL clearly mark it with "New" or "Unverified" badge
5. THE System SHALL allow farmers to filter channels by: distance (< 10km, < 25km, < 50km, < 100km), price range (low/medium/high), payment terms (immediate/within 7 days/within 15 days), crop type accepted, and reliability score (3+ stars, 4+ stars)
6. THE System SHALL show alternative pathways with visual flow: "మీరు → అగ్రిగేటర్ A → ప్రాసెసర్ B" (You → Aggregator A → Processor B) with net price calculation at each step
7. WHEN displaying in voice mode, THE System SHALL describe top 3-4 options: "పులివెందుల మండి 15 కిలోమీటర్ దూరంలో ఉంది, క్వింటాల్‌కు ₹900-₹1100, 5% కమిషన్, అదే రోజు చెల్లింపు, 4.2 స్టార్ రేటింగ్" (Pulivendula mandi is 15km away, ₹900-₹1100 per quintal, 5% commission, same-day payment, 4.2 star rating)
8. THE System SHALL calculate reliability scores based on: payment timeliness (40% weight), price accuracy (30% weight), quality assessment fairness (20% weight), and overall farmer satisfaction (10% weight)
9. WHEN farmer taps on a channel, THE System SHALL show detailed profile including: full contact details, operating schedule, crops accepted, quality requirements, payment process, recent farmer reviews (last 5), and transaction history summary
10. THE System SHALL display network map view showing farmer's location and all channels with distance indicators
11. WHEN multiple pathways exist to reach end buyers, THE System SHALL calculate and compare net prices after all deductions for each pathway
12. THE System SHALL show "Popular Choice" badge for channels used by 30%+ of farmers in the mandal
13. WHEN channel has special requirements (minimum quantity, quality certification, advance booking), THE System SHALL display these prominently
14. THE System SHALL allow farmers to save favorite channels for quick access
15. THE System SHALL update channel information daily and mark last update time

**Phase 2 Implementation**: Weeks 9-10 after MVP launch

---

### Requirement 24: Enhanced Scenario Generation with Network Intelligence

**User Story:** As a farmer, I want to see real examples, specific opportunities, and actionable contacts in my scenarios, so that I can take immediate action and connect with buyers directly.

#### Acceptance Criteria

1. WHEN generating "sell now" scenario, THE System SHALL include: (a) 3-5 recent transaction examples from similar farmers, (b) 2-4 active demand signals matching farmer's crop and quantity, (c) specific channel recommendations with contact info and "Call Now" buttons, (d) alternative pathways with net price comparisons, (e) estimated transport costs for each option
2. WHEN generating "wait" scenario, THE System SHALL include: (a) expected demand changes based on historical patterns, (b) upcoming market events (festival demand, export windows, processing season), (c) historical price trends for the wait period, (d) risk factors that could emerge during wait period, (e) recommended actions during wait period (storage, quality preservation)
3. WHEN showing channel options, THE System SHALL provide: (a) direct contact information (phone number with "Call" button), (b) specific pricing for farmer's quantity (not just ranges), (c) estimated transport costs from farmer's village, (d) expected payment timeline with dates, (e) quality requirements and acceptance criteria, (f) recent farmer reviews (last 3)
4. WHEN multiple pathways exist, THE System SHALL rank by: (1) net price after all deductions, (2) payment speed, (3) reliability score, (4) convenience (distance + ease of transport), (5) quality requirements match
5. THE System SHALL clearly distinguish between: (a) confirmed opportunities (buyer verified, demand active), (b) likely opportunities (based on historical patterns), (c) uncertain opportunities (new buyers, volatile conditions)
6. THE System SHALL provide actionable next steps: (a) "Call [Buyer Name]" button with phone number, (b) "Send SMS" button with pre-filled message template, (c) "Get Directions" button for navigation, (d) "Save for Later" option, (e) "Share with FPO" option
7. WHEN displaying in voice mode, THE System SHALL provide complete information including: buyer names, contact numbers, specific prices, payment terms, and directions in Telugu
8. WHEN farmer's quantity is large (> 50 quintals), THE System SHALL suggest splitting across multiple buyers to reduce risk
9. WHEN farmer's crop quality is premium (Grade A), THE System SHALL prioritize buyers who pay premium prices
10. WHEN urgent demand signals exist (URGENT urgency level), THE System SHALL highlight these prominently in "sell now" scenario
11. THE System SHALL calculate total earnings for each pathway: (Quantity × Price) - (Commission + Transport + Handling) = Net Earnings
12. THE System SHALL show comparison table of top 3 pathways with all costs and net earnings side-by-side
13. WHEN farmer has used a channel before, THE System SHALL show farmer's own past experience and outcome
14. THE System SHALL provide SMS summary option: "Send all details to my phone" button

**Phase 2 Implementation**: Weeks 11-12 after MVP launch

---

### Requirement 25: Transaction Data Collection and Sharing

**User Story:** As a farmer, I want to share my transaction data to help other farmers, so that the community benefits from real market information and everyone makes better decisions.

#### Acceptance Criteria

1. WHEN a farmer completes a sale, THE System SHALL prompt them to share transaction details through opt-in dialog: "మీ విక్రయ వివరాలను పంచుకోండి మరియు ఇతర రైతులకు సహాయం చేయండి" (Share your sale details and help other farmers)
2. WHEN collecting transaction data, THE System SHALL request: crop type, quantity sold (quintals), sale price (per quintal), channel used (mandi/aggregator/trader/direct buyer), buyer name (optional), quality grade (A/B/C), transaction date, payment received date, deductions/commissions, transport costs, and overall satisfaction (1-5 stars)
3. WHEN farmer opts in, THE System SHALL clearly explain: (a) data will be anonymized (name and phone removed), (b) only village name will be shown, (c) data helps other farmers get realistic price expectations, (d) farmer can delete data anytime, (e) farmer gets access to community transaction data
4. WHEN storing transaction data, THE System SHALL remove all personally identifiable information: name, phone number, exact address, and replace with anonymized reference like "Farmer from Pulivendula"
5. THE System SHALL allow farmers to view their own complete transaction history with all details including: date, crop, quantity, price, channel, costs, net earnings, and notes
6. THE System SHALL allow farmers to delete their transaction data at any time through "Delete My Data" option in settings
7. THE System SHALL provide incentives for data sharing: (a) access to detailed community transaction analytics, (b) priority access to new features, (c) recognition badge "Community Contributor", (d) monthly summary of how their data helped others
8. WHEN farmer shares 5+ transactions, THE System SHALL award "Trusted Contributor" badge
9. THE System SHALL validate transaction data for reasonableness: price within 3× of recent average, quantity within typical range, date within last 30 days
10. WHEN transaction data seems unusual, THE System SHALL ask farmer to confirm before accepting
11. THE System SHALL allow farmers to add optional notes to transactions: "Good buyer, paid on time" or "Price negotiation was difficult"
12. THE System SHALL send monthly summary to contributing farmers: "Your data helped 47 farmers this month"
13. WHEN displaying transaction history, THE System SHALL show trends: average price over time, most used channels, total earnings
14. THE System SHALL provide voice-based transaction submission: farmer can call and report transaction details through IVR

**Phase 2 Implementation**: Weeks 5-6 after MVP launch
### Requirement 26: Buyer Demand Submission and Verification

**User Story:** As a buyer/aggregator, I want to post my crop requirements, so that farmers can find me and fulfill my demand efficiently.

#### Acceptance Criteria

1. WHEN a buyer wants to post demand, THE System SHALL verify buyer identity through: (a) phone number verification (OTP), (b) business registration document upload, (c) FPO validation or existing farmer references, (d) physical address verification
2. WHEN submitting demand, THE System SHALL collect: crop type, quantity needed (quintals), price range willing to pay (per quintal), location (village/town), pickup/delivery preference, urgency level (URGENT/THIS_WEEK/THIS_MONTH), quality requirements (Grade A/B/C, moisture %, size specifications), payment terms (immediate/7/15/30 days), validity period (how long demand is active), and contact information (phone, WhatsApp)
3. WHEN demand is posted, THE System SHALL make it visible to relevant farmers within 50km radius who grow that crop
4. WHEN demand is fulfilled (farmer contacts buyer and completes sale), THE System SHALL mark it as "Completed" and remove from active listings
5. THE System SHALL expire demand signals automatically after validity period (default 7 days) and notify buyer to renew if still needed
6. THE System SHALL prevent spam or fake demand signals through: (a) rate limiting (max 5 demands per buyer per week), (b) verification requirements, (c) farmer feedback on demand quality, (d) automatic suspension for repeated fake postings
7. THE System SHALL track demand fulfillment rate for buyer reliability scoring: (Completed Demands / Total Demands) × 100
8. WHEN buyer has low fulfillment rate (< 30%), THE System SHALL flag buyer profile and reduce visibility of their demands
9. THE System SHALL allow buyers to edit demand details (price, quantity, urgency) before expiration
10. THE System SHALL send notifications to buyers when: (a) farmers express interest in their demand, (b) demand is about to expire, (c) similar crops become available in their area
11. THE System SHALL provide buyer dashboard showing: active demands, interested farmers count, completed transactions, reliability score, and farmer feedback
12. WHEN buyer posts demand, THE System SHALL suggest optimal price range based on recent market data
13. THE System SHALL allow buyers to mark demands as "Partially Fulfilled" when some quantity is still needed
14. THE System SHALL charge nominal fee (₹50-100) for posting demand to prevent spam and ensure serious buyers only

**Phase 2 Implementation**: Weeks 7-8 after MVP launch

---

### Requirement 27: Channel Reliability Scoring and Feedback System

**User Story:** As a farmer, I want to see reliability scores for channels and read other farmers' experiences, so that I can choose trustworthy buyers and avoid problematic ones.

#### Acceptance Criteria

1. WHEN displaying channels, THE System SHALL show reliability score (0-5 stars with decimal precision, e.g., 4.3 stars) based on aggregated farmer feedback
2. WHEN calculating reliability, THE System SHALL consider: (a) payment timeliness (40% weight) - did buyer pay on promised date, (b) price accuracy (30% weight) - did final price match quoted price, (c) quality assessment fairness (20% weight) - was quality grading reasonable, (d) overall farmer satisfaction (10% weight) - would farmer sell to this buyer again
3. WHEN a farmer completes a transaction, THE System SHALL prompt for feedback within 24 hours through SMS and app notification
4. WHEN collecting feedback, THE System SHALL ask specific questions: (a) "Did buyer pay on time?" (Yes/No/Delayed by X days), (b) "Was final price same as quoted?" (Yes/No/Lower by ₹X), (c) "Was quality assessment fair?" (Yes/No/Too strict), (d) "Overall experience?" (1-5 stars), (e) "Would you sell to this buyer again?" (Yes/No), (f) Optional text comment in Telugu
5. THE System SHALL update reliability scores weekly based on new feedback with recency weighting (recent feedback weighted higher)
6. THE System SHALL require minimum 5 transactions before displaying reliability score; show "New Buyer - Not Yet Rated" for buyers with < 5 transactions
7. THE System SHALL allow farmers to report fraudulent or problematic channels through "Report Issue" button with categories: (a) Payment not received, (b) Significant price reduction, (c) Unfair quality grading, (d) Rude behavior, (e) Other (with text description)
8. WHEN channel receives 3+ fraud reports, THE System SHALL automatically suspend channel and investigate
9. THE System SHALL display reliability breakdown: "4.3 stars (based on 47 farmers) - Payment: 4.5★, Price: 4.2★, Quality: 4.1★, Overall: 4.4★"
10. THE System SHALL show recent farmer reviews (last 5) with anonymized farmer reference, date, rating, and comment
11. WHEN displaying in voice mode, THE System SHALL summarize reliability: "ఈ కొనుగోలుదారుకు 4.3 స్టార్ రేటింగ్ ఉంది, 47 మంది రైతుల అభిప్రాయం ఆధారంగా, చెల్లింపు సమయానికి జరుగుతుంది" (This buyer has 4.3 star rating based on 47 farmers' feedback, payment happens on time)
12. THE System SHALL allow farmers to filter channels by minimum reliability score (e.g., show only 4+ star buyers)
13. THE System SHALL provide channel profile page showing: reliability score, total transactions, farmer reviews, response time, payment history, and quality requirements
14. THE System SHALL send monthly report to channels showing their reliability score, feedback summary, and improvement suggestions
15. WHEN channel improves score by 0.5+ stars, THE System SHALL award "Improved Service" badge
16. THE System SHALL protect against fake reviews by: (a) requiring verified transaction before allowing review, (b) detecting review patterns (same farmer reviewing same channel multiple times), (c) limiting reviews to 1 per transaction

**Phase 2 Implementation**: Weeks 9-10 after MVP launch

---

### Requirement 28: Alternative Pathway Calculation and Comparison

**User Story:** As a farmer, I want to see different ways to reach buyers with complete cost breakdowns, so that I can choose the most profitable path and maximize my earnings.

#### Acceptance Criteria

1. WHEN showing channel options, THE System SHALL calculate alternative pathways: (a) Direct to mandi, (b) Through local aggregator to mandi, (c) Through aggregator to processor, (d) Direct to processor/exporter, (e) Through FPO collective sale
2. WHEN calculating pathways, THE System SHALL include all costs: (a) Commission/fees (percentage or fixed), (b) Transport costs (per quintal per km), (c) Handling/loading charges, (d) Quality testing fees, (e) Storage costs if applicable, (f) FPO membership fees if applicable
3. WHEN comparing pathways, THE System SHALL show net price after all deductions in clear format: "Gross Price: ₹1000/quintal - Commission (5%): ₹50 - Transport: ₹30 - Handling: ₹20 = Net Price: ₹900/quintal"
4. WHEN pathways have different payment terms, THE System SHALL clearly indicate this with visual indicators: "Immediate Payment" (green), "7 Days" (yellow), "15+ Days" (orange)
5. THE System SHALL rank pathways by net profitability (highest net earnings first) with option to re-rank by payment speed or reliability
6. THE System SHALL show downstream buyers for aggregators: "అగ్రిగేటర్ A → ప్రాసెసర్ B (టమాటా సాస్ తయారీదారు)" (Aggregator A → Processor B (tomato sauce manufacturer)) with final destination and use case
7. WHEN displaying in voice mode, THE System SHALL explain top 2 pathways with pros/cons: "మొదటి మార్గం: నేరుగా మండికి, క్వింటాల్‌కు ₹900 నెట్, అదే రోజు చెల్లింపు, కానీ మీరే రవాణా చేయాలి. రెండవ మార్గం: అగ్రిగేటర్ ద్వారా, క్వింటాల్‌కు ₹850 నెట్, 3 రోజుల్లో చెల్లింపు, కానీ వారు రవాణా చేస్తారు" (First path: Direct to mandi, ₹900 net per quintal, same-day payment, but you arrange transport. Second path: Through aggregator, ₹850 net per quintal, payment in 3 days, but they arrange transport)
8. THE System SHALL calculate total earnings for each pathway for farmer's quantity: "మీ 30 క్వింటాల్‌ల కోసం మొత్తం ఆదాయం: ₹27,000" (Total earnings for your 30 quintals: ₹27,000)
9. WHEN pathway involves multiple steps, THE System SHALL show value addition at each step: "మీరు → అగ్రిగేటర్ (₹900) → ప్రాసెసర్ (₹1200) → రిటైల్ (₹2000)" showing how value increases downstream
10. THE System SHALL highlight hidden costs: "Note: Mandi pathway requires you to spend ₹500 on transport and 1 day of time"
11. WHEN farmer has vehicle/transport, THE System SHALL adjust pathway recommendations to favor direct sales
12. WHEN farmer lacks transport, THE System SHALL prioritize pathways where buyer arranges pickup
13. THE System SHALL show risk-adjusted profitability: pathways with higher reliability scores get slight boost in ranking
14. THE System SHALL provide comparison table view showing all pathways side-by-side with: Net Price, Payment Terms, Transport, Reliability, Total Earnings, and Recommended badge for best option
15. WHEN farmer selects a pathway, THE System SHALL provide step-by-step action plan: "1. Call [Buyer Name] at [Phone], 2. Confirm quantity and quality, 3. Arrange transport to [Location], 4. Get payment receipt"
16. THE System SHALL save farmer's pathway preferences and prioritize similar pathways in future recommendations

**Phase 2 Implementation**: Weeks 11-12 after MVP launch

---

## 9. Phase 2 Success Criteria

Phase 2 will be considered successful if:

1. **Feature Adoption**: 65%+ of farmers use at least one Phase 2 feature within first month
2. **Transaction Sharing**: 45%+ of farmers opt-in to share transaction data
3. **Demand Engagement**: 55%+ of farmers check demand signals at least once per harvest
4. **Network Exploration**: 70%+ of farmers explore network visualization to compare channels
5. **Contact Usage**: 35%+ of farmers use contact information to directly reach buyers
6. **Price Improvement**: 12-18% increase in average sale price compared to MVP baseline
7. **Time Reduction**: 25-35% reduction in time from harvest to sale
8. **Channel Diversity**: 45%+ increase in farmers trying new channels beyond their usual buyers
9. **Data Quality**: 85%+ accuracy of transaction and demand data verified through spot checks
10. **Farmer Satisfaction**: 88%+ satisfaction with Phase 2 features
11. **Buyer Participation**: 50+ verified buyers actively posting demand signals
12. **Reliability Scoring**: 80%+ of channels have reliability scores (minimum 5 transactions)
13. **Pathway Usage**: 60%+ of farmers compare alternative pathways before selling
14. **Voice Engagement**: 40%+ of Phase 2 feature interactions via voice interface
15. **Community Growth**: 200+ farmers actively contributing transaction data monthly
---

## 10. Phase 3 Requirements (Post Phase 2)

After successful Phase 2 validation, Phase 3 will introduce the Explore feature - a comprehensive crop planning and knowledge platform that helps farmers make informed planting decisions for the next season.

### Requirement 29: Crop Information Hub and Seasonal Intelligence

**User Story:** As a farmer planning next season, I want to see which crops are in high demand, what my neighbors are growing, and what succeeded or failed recently, so that I can make informed planting decisions and reduce risk.

#### Acceptance Criteria

1. WHEN viewing seasonal demand, THE System SHALL display top 10-15 crops for upcoming season with: (a) demand level indicator (HIGH/MEDIUM/LOW with visual color coding), (b) peak demand months (e.g., "December-February"), (c) expected price ranges (min-max per quintal), (d) demand drivers explanation (e.g., "Festival season demand", "Export window opens", "Processing industry requirement"), (e) year-over-year demand trend (increasing/stable/decreasing)
2. WHEN viewing regional trends, THE System SHALL show crops currently being grown in mandal/district with: (a) number of farmers growing each crop, (b) total acreage under cultivation, (c) average yields (quintals per acre), (d) success rate percentage (farmers who profited), (e) common challenges faced, (f) best performing sub-regions
3. WHEN viewing peer activity, THE System SHALL display recent planting activity (last 30 days) from nearby farmers (anonymized) with: (a) crop type, (b) acreage planted, (c) planting date, (d) irrigation method, (e) optional farmer notes (e.g., "Using drip irrigation this time", "Trying new variety"), (f) anonymized farmer reference (e.g., "Farmer from Pulivendula")
4. WHEN displaying crop information, THE System SHALL use Telugu language with local agricultural terminology (e.g., "టమాటా" for tomato, "ఎకరా" for acre, "క్వింటాల్" for quintal)
5. THE System SHALL update seasonal demand data weekly based on: market trends, buyer demand signals, export opportunities, processing industry requirements, and government procurement plans
6. THE System SHALL preserve farmer privacy by anonymizing all peer activity data (removing names, phone numbers, exact locations)
7. WHEN farmers opt-in, THE System SHALL allow them to share their planting activity with the community through "Share My Planting" button
8. WHEN displaying crop cards, THE System SHALL show quick summary: "టమాటా: HIGH డిమాండ్, 150 మంది రైతులు పండిస్తున్నారు, క్వింటాల్‌కు ₹800-₹1200 ఆశించవచ్చు" (Tomato: HIGH demand, 150 farmers growing, expect ₹800-₹1200 per quintal)
9. THE System SHALL provide crop comparison feature: select 2-3 crops and compare demand, investment, ROI, and risk side-by-side
10. WHEN farmer taps on a crop, THE System SHALL show detailed crop profile with all information: demand, trends, peer activity, investment needs, ROI projections, cultivation requirements, and success stories
11. THE System SHALL highlight "Trending Up" crops with increasing demand and "Caution" crops with declining demand or high risk
12. THE System SHALL show seasonal calendar view: which crops to plant in which months for the region
13. WHEN displaying in voice mode, THE System SHALL provide crop recommendations: "ఈ సీజన్‌లో టమాటా, ఉల్లిపాయ, మిరపకాయలకు డిమాండ్ ఎక్కువగా ఉంది" (This season, tomatoes, onions, and chillies have high demand)
14. THE System SHALL allow farmers to save favorite crops for quick access and receive updates about those crops
15. THE System SHALL provide "What's Working" section showing crops with highest success rates in the region

**Phase 3 Implementation**: Weeks 1-4 after Phase 2 launch

---

### Requirement 30: Investment Calculator with Detailed Cost Breakdown

**User Story:** As a farmer, I want to calculate total investment needed for a specific crop with detailed cost breakdown, so that I can plan my finances, arrange loans if needed, and avoid mid-season cash crunches.

#### Acceptance Criteria

1. WHEN calculating investment, THE System SHALL collect: (a) crop type, (b) land size in acres, (c) irrigation availability (rainfed/borewell/canal/drip), (d) current resources (own seeds/equipment/labor), (e) soil type (if known), (f) farming method (traditional/organic/precision)
2. WHEN generating cost breakdown, THE System SHALL include detailed categories: (a) Seeds/Seedlings (quantity needed, cost per kg/unit, total), (b) Fertilizers (NPK, organic, micronutrients with quantities and costs), (c) Pesticides/Fungicides (types needed, application frequency, costs), (d) Irrigation (electricity/diesel costs, drip system rental if applicable), (e) Labor (land preparation, sowing, weeding, harvesting with person-days and daily wages), (f) Equipment rental (tractor, sprayer, harvester with hours and rates), (g) Miscellaneous (transport, storage materials, quality testing)
3. WHEN displaying costs, THE System SHALL show ranges (min-max) in rupees for each category with explanation: "విత్తనాలు: ₹3,000-₹5,000 (రకం మరియు నాణ్యతపై ఆధారపడి)" (Seeds: ₹3,000-₹5,000 depending on variety and quality)
4. WHEN costs are calculated, THE System SHALL provide: (a) Total investment range (min-max), (b) Per-acre investment, (c) Cost breakdown by phase (land prep, planting, growing, harvesting), (d) Timeline of when costs will be incurred
5. THE System SHALL use local cost data from: input dealers, FPOs, farmer surveys, government agriculture department, and recent market prices
6. THE System SHALL update cost models monthly based on: fertilizer price changes, labor wage changes, fuel price changes, and seasonal variations
7. WHEN displaying in voice mode, THE System SHALL summarize key cost categories and total: "టమాటా 2 ఎకరాలకు మొత్తం పెట్టుబడి ₹40,000-₹60,000, ముఖ్యంగా విత్తనాలు ₹8,000, ఎరువులు ₹15,000, కూలీలు ₹20,000" (For 2 acres of tomatoes, total investment ₹40,000-₹60,000, mainly seeds ₹8,000, fertilizers ₹15,000, labor ₹20,000)
8. WHEN farmer has own resources (seeds, equipment), THE System SHALL adjust calculations and show savings: "మీ స్వంత విత్తనాలు ఉపయోగిస్తే ₹5,000 ఆదా అవుతుంది" (Using your own seeds saves ₹5,000)
9. THE System SHALL provide cost optimization suggestions: "Buying fertilizers in bulk with 3 neighbors can save 15%"
10. THE System SHALL show cost comparison with previous season: "Last season tomato investment was ₹45,000, now ₹50,000 (11% increase due to fertilizer prices)"
11. WHEN investment is high, THE System SHALL suggest: (a) FPO loan options, (b) Government subsidy schemes, (c) Input cost-sharing with neighbors, (d) Phased planting to spread costs
12. THE System SHALL allow farmers to customize inputs: change quantities, select organic vs chemical, adjust labor estimates based on family labor availability
13. THE System SHALL provide downloadable/SMS-able cost summary for loan applications or record-keeping
14. THE System SHALL track actual costs if farmer opts in and compare with estimates to improve future calculations
15. THE System SHALL show "Hidden Costs Alert": costs farmers often forget like transport, storage materials, quality testing fees

**Phase 3 Implementation**: Weeks 1-4 after Phase 2 launch

---

### Requirement 31: ROI Projections and Profitability Analysis

**User Story:** As a farmer, I want to see expected returns, profitability, and risks for different crops, so that I can choose crops that maximize my income while managing risk appropriately.

#### Acceptance Criteria

1. WHEN calculating ROI, THE System SHALL use: (a) expected yield ranges (min-max quintals per acre based on regional data), (b) expected price ranges (min-max per quintal based on seasonal trends), (c) total investment calculated from Requirement 30
2. WHEN displaying projections, THE System SHALL show: (a) Expected revenue range (yield × price), (b) Net profit range (revenue - investment), (c) ROI percentage range ((profit/investment) × 100), (d) Break-even yield (minimum yield needed to recover investment), (e) Break-even price (minimum price needed to recover investment), (f) Profit per acre, (g) Expected timeline to profitability (months from planting to sale)
3. WHEN presenting ROI, THE System SHALL include risk level (HIGH/MEDIUM/LOW) with detailed explanation: "HIGH RISK: Price volatility is high, spoilage risk is significant, weather dependency is critical" or "LOW RISK: Stable demand, low spoilage, multiple selling windows"
4. WHEN projections are uncertain, THE System SHALL clearly communicate uncertainty and factors: "ఈ అంచనాలు గత 3 సంవత్సరాల డేటా ఆధారంగా ఉన్నాయి, కానీ వాతావరణం, మార్కెట్ పరిస్థితులు మారవచ్చు" (These projections are based on last 3 years data, but weather and market conditions can change)
5. THE System SHALL calculate break-even scenarios: "మీరు ఎకరాకు కనీసం 80 క్వింటాల్స్ పండించాలి లేదా క్వింటాల్‌కు కనీసం ₹750 పొందాలి" (You need to produce minimum 80 quintals per acre OR get minimum ₹750 per quintal)
6. THE System SHALL use historical data (3-5 years) and current market trends for projections with data source transparency
7. WHEN displaying in voice mode, THE System SHALL provide key numbers and risk assessment: "టమాటా 2 ఎకరాలకు పెట్టుబడి ₹50,000, ఆశించే ఆదాయం ₹1,20,000-₹2,00,000, నెట్ లాభం ₹70,000-₹1,50,000, ROI 140-300%, కానీ రిస్క్ MEDIUM ఎందుకంటే ధర అస్థిరత ఉంది" (For 2 acres tomatoes, investment ₹50,000, expected revenue ₹1,20,000-₹2,00,000, net profit ₹70,000-₹1,50,000, ROI 140-300%, but risk is MEDIUM due to price volatility)
8. THE System SHALL provide scenario analysis: Best case (high yield + high price), Expected case (average yield + average price), Worst case (low yield + low price)
9. THE System SHALL show profitability comparison across crops: "టమాటా ROI 200%, ఉల్లిపాయ ROI 150%, మిరపకాయ ROI 180%" with risk levels for each
10. WHEN farmer's land/resources are known, THE System SHALL personalize projections based on farmer's historical yields and local conditions
11. THE System SHALL highlight risk factors: "Price Risk: HIGH - prices fluctuate 40-60% seasonally", "Yield Risk: MEDIUM - weather dependent", "Spoilage Risk: HIGH - 15-20% post-harvest loss typical"
12. THE System SHALL provide risk mitigation suggestions: "Reduce price risk by: (a) Staggered planting, (b) Pre-selling 30% to aggregators, (c) Value addition (drying)"
13. THE System SHALL show month-by-month cash flow projection: when costs occur vs when revenue comes
14. THE System SHALL compare ROI with alternative crops and traditional crops farmer usually grows
15. THE System SHALL track actual outcomes if farmer opts in and show accuracy of projections to build trust
16. THE System SHALL provide "Reality Check" section: "80% of farmers achieved ROI between 120-180%, 15% achieved > 200%, 5% had losses"

**Phase 3 Implementation**: Weeks 1-4 after Phase 2 launch

---

### Requirement 32: Cultivation Requirements and Land Suitability Analysis

**User Story:** As a farmer, I want to know detailed soil, water, climate, and cultivation requirements for a crop, so that I can choose crops suitable for my land and avoid costly mistakes.

#### Acceptance Criteria

1. WHEN viewing crop requirements, THE System SHALL display soil information: (a) suitable soil types (red soil, black soil, sandy loam, etc.), (b) pH range (e.g., 6.0-7.5), (c) drainage needs (well-drained/moderate/poor), (d) soil preparation steps in sequence (plowing depth, bed preparation, organic matter addition), (e) soil testing recommendations
2. WHEN showing water requirements, THE System SHALL include: (a) total water needed per crop cycle (in liters or irrigation rounds), (b) irrigation frequency (daily/weekly/bi-weekly), (c) critical watering stages (flowering, fruit development), (d) drought tolerance level (HIGH/MEDIUM/LOW), (e) suitable irrigation methods (flood/drip/sprinkler), (f) water-saving techniques
3. WHEN displaying climate requirements, THE System SHALL show: (a) optimal temperature range (day and night), (b) total rainfall requirements (mm), (c) sunlight needs (full sun/partial shade), (d) season suitability (Kharif/Rabi/Summer), (e) frost tolerance, (f) wind sensitivity, (g) humidity preferences
4. WHEN farmer land profile is available (soil type, irrigation, location), THE System SHALL perform automated suitability check and display: "మీ భూమికి ఈ పంట: HIGHLY SUITABLE / SUITABLE / MARGINALLY SUITABLE / NOT SUITABLE" with detailed explanation
5. THE System SHALL use agricultural university data (ANGRAU, ICAR), government guidelines, and local agricultural officer inputs for requirements
6. THE System SHALL display all requirements in Telugu with local terminology: "ఎర్ర మట్టి" (red soil), "నీటి పారుదల" (drainage), "ఉష్ణోగ్రత" (temperature)
7. WHEN displaying in voice mode, THE System SHALL summarize key requirements and suitability: "టమాటాకు ఎర్ర మట్టి బాగుంటుంది, pH 6-7, వారానికి 2-3 సార్లు నీరు, 20-30 డిగ్రీల ఉష్ణోగ్రత కావాలి. మీ భూమికి HIGHLY SUITABLE" (Tomato prefers red soil, pH 6-7, water 2-3 times per week, 20-30°C temperature needed. HIGHLY SUITABLE for your land)
8. WHEN crop is not suitable for farmer's land, THE System SHALL suggest: (a) modifications to make it suitable (soil amendments, irrigation upgrades), (b) alternative similar crops that are suitable, (c) estimated cost of modifications
9. THE System SHALL provide cultivation calendar: month-by-month activities from land preparation to harvest
10. THE System SHALL show common mistakes to avoid: "Don't plant tomatoes in heavy clay soil without raised beds"
11. WHEN farmer's land has limitations (poor drainage, low pH), THE System SHALL highlight crops that tolerate those conditions
12. THE System SHALL provide variety recommendations: which varieties work best in the region's conditions
13. THE System SHALL show intercropping compatibility: which crops can be grown together
14. THE System SHALL include pest and disease susceptibility information for the region
15. THE System SHALL allow farmers to save their land profile (soil type, irrigation, size) for quick suitability checks across all crops

**Phase 3 Implementation**: Weeks 5-8 after Phase 2 launch

---

### Requirement 33: Alternate Uses, Value Addition, and Income Diversification

**User Story:** As a farmer, I want to discover alternate uses, value-added opportunities, and processing options for crops, so that I can increase my income, reduce waste, and access premium markets.

#### Acceptance Criteria

1. WHEN viewing alternate uses, THE System SHALL display: (a) dried/processed forms (sun-dried, dehydrated, powdered), (b) medicinal uses and ayurvedic applications, (c) industrial applications (dyes, oils, fibers), (d) by-product opportunities (seeds, peels, stems), (e) animal feed potential, (f) organic fertilizer/compost uses
2. WHEN showing value addition options, THE System SHALL include for each option: (a) price multiplier (e.g., "3x price for dried tomatoes vs fresh"), (b) equipment needed (dehydrator, grinder, packaging machine), (c) processing costs (electricity, labor, packaging), (d) skill requirements (training needed, complexity level), (e) market access (who buys processed products), (f) shelf life extension, (g) estimated additional profit per quintal
3. WHEN displaying opportunities, THE System SHALL rank by: (1) profitability (ROI on processing investment), (2) feasibility (equipment availability, skill level), (3) market demand (buyer availability), (4) initial investment required
4. WHEN equipment is required, THE System SHALL provide: (a) approximate costs (purchase vs rental), (b) availability information (local suppliers, FPO shared equipment), (c) capacity (kg per hour), (d) maintenance requirements, (e) government subsidy schemes available
5. THE System SHALL include success stories from local farmers who implemented value addition: "రాజు గారు పులివెందుల నుండి టమాటా ఎండబెట్టడం ప్రారంభించారు, ఇప్పుడు 50% ఎక్కువ ఆదాయం పొందుతున్నారు" (Raju from Pulivendula started drying tomatoes, now earning 50% more income)
6. THE System SHALL provide contact information for: (a) processing equipment suppliers with phone numbers, (b) training centers for processing skills, (c) buyers of processed products, (d) packaging material suppliers
7. WHEN displaying in voice mode, THE System SHALL describe top 2-3 opportunities with key details: "టమాటా ఎండబెట్టడం: 3 రెట్లు ధర, డీహైడ్రేటర్ కావాలి ₹25,000, నెలకు ₹15,000 అదనపు ఆదాయం సాధ్యం" (Tomato drying: 3x price, need dehydrator ₹25,000, possible ₹15,000 extra income per month)
8. THE System SHALL provide step-by-step processing guides: "How to dry tomatoes: 1. Select ripe tomatoes, 2. Wash and slice, 3. Dehydrate at 60°C for 8 hours, 4. Package in airtight bags"
9. WHEN processing requires certification (FSSAI, organic), THE System SHALL explain requirements and process
10. THE System SHALL show seasonal timing: when to process (glut season for better margins)
11. THE System SHALL calculate break-even analysis for processing: "Need to process 50 quintals to recover dehydrator cost"
12. THE System SHALL suggest collective processing: "Share dehydrator with 3 neighbors to reduce individual cost"
13. THE System SHALL provide quality standards for processed products to access premium markets
14. THE System SHALL show export opportunities for processed products with buyer contacts
15. THE System SHALL include video tutorials (if available) or links to processing demonstrations
16. THE System SHALL track farmers who adopted value addition and share their outcomes to inspire others

**Phase 3 Implementation**: Weeks 5-8 after Phase 2 launch

---

### Requirement 34: Industry Applications and Premium Market Access

**User Story:** As a farmer, I want to see which industries buy specific crops, their quality requirements, and premium prices they offer, so that I can target high-value buyers and increase my income.

#### Acceptance Criteria

1. WHEN viewing industry applications, THE System SHALL display industries by category: (a) Food Processing (sauce, paste, juice, canning, frozen foods), (b) Pharmaceuticals (medicinal extracts, active ingredients), (c) Cosmetics (oils, extracts, natural ingredients), (d) Textiles (natural dyes, fibers), (e) Export Industries (fresh export, processed export), (f) Nutraceuticals (health supplements, functional foods)
2. WHEN showing industry details, THE System SHALL include: (a) products made from the crop (e.g., "Tomato → Ketchup, Sauce, Paste, Juice"), (b) major buyers with company names and locations, (c) quality requirements (Grade A, moisture %, size, color, brix level), (d) price premiums over market rate (e.g., "20-40% premium for Grade A"), (e) payment terms (advance/immediate/30 days), (f) contract farming opportunities, (g) minimum quantity requirements, (h) delivery preferences (farm gate/processing unit)
3. WHEN buyers are verified, THE System SHALL provide complete contact information: (a) company name, (b) contact person name, (c) phone number with "Call Now" button, (d) location with "Get Directions" button, (e) email address, (f) procurement schedule (which months they buy)
4. WHEN quality requirements exist, THE System SHALL clearly explain: (a) certification needs (organic, FSSAI, GlobalGAP, APEDA), (b) quality standards in simple terms, (c) testing procedures, (d) how to achieve required quality, (e) cost of certification, (f) certification process timeline, (g) certification support available from FPOs/government
5. THE System SHALL prioritize industries by: (1) price premium offered, (2) accessibility (distance, ease of contact), (3) reliability (payment track record), (4) volume requirements (matching farmer's capacity)
6. THE System SHALL update buyer information quarterly through: industry surveys, FPO partnerships, buyer registrations, and farmer feedback
7. WHEN displaying in voice mode, THE System SHALL describe top 2-3 industries with contact details: "టమాటా సాస్ కంపెనీలు 30% ప్రీమియం ఇస్తాయి, Grade A నాణ్యత కావాలి, పులివెందుల లో XYZ ఫుడ్స్ ఉంది, ఫోన్: 9876543210" (Tomato sauce companies give 30% premium, need Grade A quality, XYZ Foods in Pulivendula, phone: 9876543210)
8. THE System SHALL show industry demand calendar: which industries buy in which months
9. WHEN contract farming is available, THE System SHALL explain: terms, advance payment, price guarantee, input support, and risks
10. THE System SHALL provide quality improvement guidance: how to upgrade from Grade B to Grade A
11. WHEN certification is required, THE System SHALL connect farmers with: certification agencies, training programs, FPO support for group certification
12. THE System SHALL show success stories: "50 farmers in Kadapa got organic certification through FPO, now selling to export companies at 40% premium"
13. THE System SHALL calculate premium earnings: "If you achieve Grade A quality, you can earn ₹15,000 extra on 30 quintals"
14. THE System SHALL provide industry-specific cultivation tips: "For pharmaceutical industry, avoid chemical pesticides in last 30 days"
15. THE System SHALL show downstream value chain: "Your tomatoes → Processor → Retail Brand → Consumer" with value addition at each step
16. THE System SHALL allow farmers to express interest in industry buyers: "I'm interested" button sends farmer details to buyer
17. THE System SHALL track successful industry connections and showcase them to encourage others

**Phase 3 Implementation**: Weeks 5-8 after Phase 2 launch

---

### Requirement 35: Voice-Enabled Crop Exploration and Planning

**User Story:** As a farmer, I want to explore crops, get planning information, and ask questions through voice, so that I can access knowledge hands-free while working in the field or at home.

#### Acceptance Criteria

1. WHEN farmer asks about seasonal demand, THE System SHALL respond with top crops and demand levels in Telugu: "ఈ సీజన్‌లో టమాటా, ఉల్లిపాయ, మిరపకాయలకు HIGH డిమాండ్ ఉంది, టమాటా క్వింటాల్‌కు ₹800-₹1200 వరకు అమ్ముకోవచ్చు" (This season tomatoes, onions, chillies have HIGH demand, tomatoes can sell for ₹800-₹1200 per quintal)
2. WHEN farmer asks about investment, THE System SHALL provide cost breakdown and total investment range: "టమాటా 2 ఎకరాలకు మొత్తం పెట్టుబడి ₹40,000-₹60,000, విత్తనాలు ₹8,000, ఎరువులు ₹15,000, కూలీలు ₹20,000" (For 2 acres tomatoes, total investment ₹40,000-₹60,000, seeds ₹8,000, fertilizers ₹15,000, labor ₹20,000)
3. WHEN farmer asks about profitability, THE System SHALL provide ROI projections with risk assessment: "టమాటా ROI 150-250%, కానీ MEDIUM రిస్క్ ఎందుకంటే ధర అస్థిరత ఉంది, నెట్ లాభం ₹60,000-₹1,20,000 ఆశించవచ్చు" (Tomato ROI 150-250%, but MEDIUM risk due to price volatility, net profit ₹60,000-₹1,20,000 expected)
4. WHEN farmer asks about requirements, THE System SHALL describe soil, water, and climate needs: "టమాటాకు ఎర్ర మట్టి బాగుంటుంది, pH 6-7, వారానికి 2-3 సార్లు నీరు, 20-30 డిగ్రీల ఉష్ణోగ్రత కావాలి" (Tomato prefers red soil, pH 6-7, water 2-3 times per week, 20-30°C temperature needed)
5. WHEN farmer asks about alternate uses, THE System SHALL explain value addition opportunities: "టమాటా ఎండబెట్టడం ద్వారా 3 రెట్లు ధర పొందవచ్చు, డీహైడ్రేటర్ కావాలి ₹25,000" (By drying tomatoes you can get 3x price, need dehydrator ₹25,000)
6. THE System SHALL handle follow-up questions and maintain conversation context across multiple turns: "ఆ పంట గురించి మరింత చెప్పండి" (Tell me more about that crop) should continue previous crop discussion
7. THE System SHALL provide option to send SMS summary after voice interaction: "మీకు ఈ సమాచారం SMS గా పంపించాలా?" (Should I send this information to you via SMS?)
8. WHEN viewing Explore home screen, THE System SHALL provide a prominent microphone button next to the search bar for voice-based crop search
9. WHEN farmer taps the microphone button, THE System SHALL activate voice input and process spoken crop queries: "టమాటా గురించి చెప్పండి" (Tell me about tomatoes)
10. THE System SHALL support natural language queries in Telugu: "ఏ పంట ఎక్కువ లాభం ఇస్తుంది?" (Which crop gives more profit?), "నా భూమికి ఏ పంట బాగుంటుంది?" (Which crop is good for my land?), "తక్కువ నీరు కావాల్సిన పంటలు ఏవి?" (Which crops need less water?)
11. THE System SHALL provide conversational responses with follow-up suggestions: "టమాటా గురించి చెప్పాను. మీరు పెట్టుబడి లేదా లాభం గురించి తెలుసుకోవాలనుకుంటున్నారా?" (I told you about tomatoes. Do you want to know about investment or profit?)
12. WHEN farmer asks comparison questions, THE System SHALL compare crops: "టమాటా vs ఉల్లిపాయ: టమాటా ROI ఎక్కువ కానీ రిస్క్ కూడా ఎక్కువ, ఉల్లిపాయ స్థిరమైన ధర ఉంటుంది" (Tomato vs Onion: Tomato has higher ROI but also higher risk, onion has stable price)
13. THE System SHALL handle voice input errors gracefully: "క్షమించండి, నేను అర్థం చేసుకోలేదు. దయచేసి మళ్ళీ చెప్పండి" (Sorry, I didn't understand. Please say again)
14. THE System SHALL provide voice-based navigation: "పంట సమాచారం కోసం 1 చెప్పండి, పెట్టుబడి కోసం 2 చెప్పండి" (Say 1 for crop information, say 2 for investment)
15. THE System SHALL support voice commands for actions: "ఈ పంటను సేవ్ చేయండి" (Save this crop), "SMS పంపండి" (Send SMS), "మరిన్ని పంటలు చూపించండి" (Show more crops)
16. THE System SHALL provide voice feedback during processing: "ఒక క్షణం, సమాచారం తీసుకుంటున్నాను" (One moment, fetching information)
17. WHEN displaying voice results, THE System SHALL also show visual information on screen for reference
18. THE System SHALL allow switching between voice and text input seamlessly during exploration
19. THE System SHALL track voice usage patterns to improve voice recognition for agricultural Telugu terms
20. THE System SHALL work in noisy field environments with appropriate noise cancellation

**Phase 3 Implementation**: Weeks 9-10 after Phase 2 launch

---

### Requirement 36: Voice-Based Outcome Feedback and Experience Sharing

**User Story:** As a farmer who prefers voice interaction, I want to provide feedback about my selling outcome, crop performance, and overall experience through voice, so that I can share my experience without typing and help other farmers learn from my journey.

#### Acceptance Criteria

1. WHEN viewing the outcome feedback screen after a sale, THE System SHALL provide a prominent voice button above the comments textarea with Telugu label "వాయిస్ ద్వారా చెప్పండి" (Tell via voice)
2. WHEN farmer taps the voice button, THE System SHALL activate voice input for feedback collection with visual indicator (pulsing microphone icon)
3. WHEN farmer speaks feedback in Telugu, THE System SHALL transcribe it to text in real-time and populate the comments field: "కొనుగోలుదారు సమయానికి చెల్లించారు, నాణ్యత అంచనా సరైనది" (Buyer paid on time, quality assessment was fair)
4. WHEN voice transcription is complete, THE System SHALL allow farmer to review and edit the transcribed text before submission
5. THE System SHALL support Telugu voice input for all feedback types: transaction feedback, crop performance feedback, system feedback, and general comments
6. THE System SHALL handle noisy field environments with appropriate noise cancellation and background noise filtering
7. THE System SHALL provide visual feedback during voice recording: (a) waveform animation showing voice levels, (b) recording timer, (c) pause/resume buttons, (d) "Listening..." indicator
8. WHEN voice input fails or is unclear, THE System SHALL: (a) show confidence score, (b) allow farmer to retry recording, (c) provide option to switch to text input, (d) suggest speaking more clearly or moving to quieter location
9. WHEN providing crop performance feedback, THE System SHALL support voice input for: actual yield achieved, quality grade received, challenges faced, what worked well, what would farmer do differently
10. THE System SHALL support structured voice feedback with prompts: "మీ అనుభవం ఎలా ఉంది?" (How was your experience?), "ఏవైనా సమస్యలు ఎదురయ్యాయా?" (Did you face any problems?), "ఇతర రైతులకు ఏమి సలహా ఇస్తారు?" (What advice would you give to other farmers?)
11. THE System SHALL allow voice feedback for multiple aspects: selling experience, buyer reliability, price satisfaction, system helpfulness, feature suggestions
12. WHEN farmer provides voice feedback about a buyer, THE System SHALL extract key information: payment timeliness, price accuracy, quality assessment fairness, and overall rating
13. THE System SHALL support voice-based rating: "5 స్టార్లు ఇవ్వండి" (Give 5 stars) or "చాలా బాగుంది" (Very good) should set 5-star rating
14. THE System SHALL provide voice playback option: farmer can listen to their recorded feedback before submitting
15. WHEN voice feedback contains sensitive information (complaints, fraud reports), THE System SHALL flag for priority review
16. THE System SHALL support voice feedback in multiple contexts: (a) After completing a sale, (b) After harvest completion, (c) After using Explore features, (d) General feedback anytime
17. THE System SHALL provide voice-based success story submission: farmers can share their success stories through voice for inspiring others
18. WHEN farmer provides detailed voice feedback, THE System SHALL offer to create a case study: "మీ అనుభవం ఇతర రైతులకు ఉపయోగపడుతుంది. దీన్ని కేస్ స్టడీగా పంచుకోవచ్చా?" (Your experience will help other farmers. Can we share this as a case study?)
19. THE System SHALL support voice feedback for feature requests: "నాకు ఈ ఫీచర్ కావాలి..." (I need this feature...)
20. THE System SHALL track voice feedback quality and improve transcription accuracy for agricultural Telugu terms over time

**MVP Implementation**: Included in MVP voice features (Requirement 15-17 extension)

---

---

## 11. Phase 3 Success Criteria

Phase 3 will be considered successful if:

1. **Feature Discovery**: 75%+ of farmers discover Explore feature within first 2 weeks
2. **Feature Usage**: 60%+ of farmers use Explore at least once per season for crop planning
3. **Calculator Usage**: 65%+ of farmers use investment calculator before planting decisions
4. **ROI Checks**: 60%+ of farmers check ROI projections for multiple crops before choosing
5. **Crop Diversification**: 25%+ increase in farmers trying new crops based on Explore insights
6. **Planning Confidence**: 85%+ of farmers feel more confident in crop selection after using Explore
7. **Investment Awareness**: 92%+ of farmers understand complete investment requirements before planting
8. **Profitability Impact**: 18-25% increase in average farm profitability through better crop selection
9. **Voice Usage**: 45%+ of explore queries via voice interface
10. **Data Accuracy**: 88%+ accuracy of investment and ROI projections verified through farmer outcomes
11. **Suitability Checks**: 70%+ of farmers use land suitability analysis before crop selection
12. **Value Addition Adoption**: 15%+ of farmers explore or adopt value addition opportunities
13. **Industry Connections**: 20%+ of farmers connect with premium industry buyers
14. **Repeat Usage**: 80%+ of farmers return to Explore for next season planning
15. **Voice Feedback**: 50%+ of outcome feedback provided via voice
16. **Crop Comparison**: 65%+ of farmers compare 2-3 crops before making final decision
17. **Success Stories**: 100+ farmer success stories collected through voice feedback
18. **Planning Timeline**: 40%+ reduction in time spent on crop planning and research
19. **Informed Decisions**: 90%+ of farmers report making more informed planting decisions
20. **Community Learning**: 70%+ of farmers find peer activity and regional trends helpful

---
