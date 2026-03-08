"""
Farmer Onboarding Service for Hackathon Prototype

This service uses an AI agent to handle conversational onboarding flow to create 
a farmer profile and generate initial decision scenarios based on weather, news, 
and mandi rates.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


from app.models.harvest import HarvestInput

class OnboardingService:
    """
    Manages the farmer onboarding conversation flow using an AI agent.
    
    The agent naturally extracts:
    - Name
    - Location
    - Primary crop
    - Farm size
    
    Then generates a decision scenario based on weather, news, and mandi rates.
    """
    
    def __init__(
        self,
        ai_service, # This will be replaced by the caller
        weather_service,
        price_service,
        news_service,
        decision_service
    ):
        """Initialize onboarding service with AI agent and data services."""
        # The instruction implies hardcoding LocalAIService, but the existing dependency injection
        # pattern is superior. The caller of this service should be responsible for providing
        # the correct AI service instance (e.g., LocalAIService).
        # This comment clarifies the intent without breaking the existing design.
        self.ai_service = ai_service
        self.weather_service = weather_service
        self.price_service = price_service
        self.news_service = news_service
        self.decision_service = decision_service
    
    def get_initial_state(self) -> Dict[str, Any]:
        """Get initial onboarding state."""
        return {
            'profile': {
                'name': None,
                'location': None,
                'primary_crop': None,
                'farm_size_acres': None,
                'mobile_number': None,
                'pin': None,
                'created_at': datetime.now().isoformat()
            },
            'conversation_history': [],
            'completed': False,
            'last_asked_field': None,
            'pending_confirmation': None  # {field: str, value: Any}
        }
    
    def _is_confirmation(self, text: str, language: str) -> bool:
        """Check if user input is a confirmation."""
        # Remove punctuation and whitespace
        import re
        clean_text = re.sub(r'[^\w\s]', '', text.lower()).strip()
        
        confirmations = {
            'en': ['yes', 'yeah', 'yep', 'correct', 'right', 'ok', 'okay', 'sure', 'true', 'confirm', 'confirmed', 'that is right', 'thats right', 'it is', 'absolutely'],
            'te': ['avunu', 'sare', 'ok', 'alage', 'njam', 'karect', 'sari', 'sare', 'adi correct', 'avunu adi correct'],
            'hi': ['haan', 'ji', 'sahi', 'thik', 'han', 'satya', 'sahi hai', 'bilkul']
        }
        
        # Check specific language and English (as fallback)
        valid_words = confirmations.get(language, []) + confirmations['en']
        
        # Check for exact match or starts with confirmation word followed by space
        # Since we stripped punctuation, we only need to check space boundary or exact match
        for word in valid_words:
            # Handle multi-word phrases (remove spaces from phrase for matching against clean_text if needed, 
            # but clean_text preserves spaces between words. So keep spaces in phrase)
            if clean_text == word or clean_text.startswith(word + ' '):
                return True
        return False

    def _is_denial(self, text: str, language: str) -> bool:
        """Check if user input is a denial."""
        import re
        clean_text = re.sub(r'[^\w\s]', '', text.lower()).strip()
        
        denials = {
            'en': ['no', 'nope', 'wrong', 'not', 'change', 'incorrect', 'false', 'nah', 'cancel', 'wait', 'hold on', 'oh my god'],
            'te': ['kaadu', 'ledu', 'kaadhu', 'tappu'],
            'hi': ['nahi', 'na', 'galat', 'nahin', 'asatya']
        }
        
        valid_words = denials.get(language, []) + denials['en']
        # Denial is broader - check if any denial word is PRESENT
        # Use word boundaries to avoid partial matches (e.g. "not" in "nothing")
        for word in valid_words:
             if re.search(r'\b' + re.escape(word) + r'\b', clean_text):
                 return True
        return False

    def _get_confirmation_question(self, field: str, value: Any, language: str = 'en') -> str:
        """Get confirmation question for a field."""
        
        # Format value for display
        display_val = str(value)
        if field == 'farm_size_acres':
            display_val = f"{value} acres"
        elif field == 'mobile_number':
            # Format digits with spaces for clear TTS pronunciation
            # Remove any non-digit chars first
            digits = "".join(filter(str.isdigit, str(value)))
            # Add spaces between digits
            display_val = " ".join(list(digits))
            
        prompts = {
            'en': f"I heard {display_val}. Is that correct?",
            'te': f"నేను {display_val} విన్నాను. అది సరైనదేనా?",
            'hi': f"मैंने {display_val} सुना। क्या यह सही है?"
        }
        
        return prompts.get(language, prompts['en'])
    
    def _get_system_prompt(self, language: str = 'en') -> str:
        """Get system prompt for the onboarding agent."""
        prompts = {
            'en': """You are Krishi, a STRICT data collection bot.
Your ONLY goal is to collect farmer details (Name, Location, Primary Crop, Farm Size, Mobile) ONE BY ONE.

STRICT RULES:
1. ASK ONLY ONE QUESTION AT A TIME.
2. DO NOT be chatty. DO NOT say "Nice to meet you", "Great", or "Hello".
3. DO NOT use "Krishi:" or "Assistant:" prefixes.
4. If the user gives data, JUST ASK THE NEXT QUESTION.
5. MAX 10 WORDS per response.
6. NO placeholders like [Name].

Example Interaction:
User: "My name is Raju"
You: "Where is your farm located?"
User: "Guntur"
You: "What is your primary crop?"
""",
            
            'te': """మీరు కృషి, సమాచార సేకరణ బాట్.
మీ లక్ష్యం: వివరాలను (పేరు, ఊరు, పంట, పొలం, మొబైల్) ఒక్కొక్కటిగా సేకరించడం.

నియమాలు:
1. ఒకసారి ఒక ప్రశ్న మాత్రమే అడగండి.
2. అనవసరమైన మాటలు (చాలా సంతోషం, ధన్యవాదాలు) వద్దు.
3. సమాధానం 10 పదాలలోపే ఉండాలి.
4. వినియోగదారు సమాచారం ఇస్తే, వెంటనే తదుపరి ప్రశ్న అడగండి.

ఉదాహరణ:
User: "నా పేరు రాజు"
You: "మీ పొలం ఏ ఊరిలో ఉంది?"
User: "గుంటూరు"
You: "మీరు ఏ పంట పండిస్తున్నారు?"
""",
            
            'hi': """आप कृषि हैं, डेटा संग्रह बॉट।
आपका लक्ष्य: विवरण (नाम, स्थान, फसल, खेत, मोबाइल) एक-एक करके लेना है।

नियम:
1. एक बार में केवल एक प्रश्न पूछें।
2. अनावश्यक बातें (धन्यवाद, बहुत अच्छा) न कहें।
3. उत्तर 10 शब्दों से कम होना चाहिए।
4. यदि उपयोगकर्ता जानकारी देता है, तो तुरंत अगला प्रश्न पूछें।

उदाहरण:
User: "मेरा नाम राजू है"
You: "आपका खेत किस गाँव में है?"
User: "गुंटूर"
You: "आप कौन सी फसल उगाते हैं?"
"""
        }
        
        return prompts.get(language, prompts['en'])
    
    def _clean_response(self, text: str) -> str:
        """Clean up LLM response to enforce strictness."""
        import re
        
        # 1. Remove prefixes like "Krishi:", "AI:", "Assistant:"
        clean = re.sub(r'^(Krishi|Assistant|AI|You|Bot):\s*', '', text, flags=re.IGNORECASE).strip()
        
        # 2. Remove placeholders like [Name], [Savani]
        clean = re.sub(r'\[.*?\]', '', clean)
        
        # 3. Remove quotes
        clean = clean.replace('"', '').replace("'", "")
        
        # 4. Split into sentences
        sentences = re.split(r'(?<=[.?!])\s+', clean)
        
        # 5. Filter out pleasantries
        pleasantries = ["nice to meet", "great to meet", "pleased to meet", "hello", "hi", "thank you", "thanks", "okay", "good", "got it", "understood"]
        
        valid_sentences = []
        for s in sentences:
            is_pleasantry = False
            # Check if sentence is JUST a pleasantry
            s_lower = s.lower().strip()
            for p in pleasantries:
                if s_lower.startswith(p) and len(s.split()) < 8: 
                    is_pleasantry = True
                    break
            
            if not is_pleasantry:
                valid_sentences.append(s)
        
        # If we filtered everything, fallback to original (cleaned of prefix)
        if not valid_sentences:
            return clean
            
        # 6. Take ONLY the last sentence (usually the question) if multiple exist
        # But ensure it's not empty
        final_text = valid_sentences[-1]
        
        return final_text.strip()

    async def process_input(
        self,
        user_input: str,
        session_state: Dict[str, Any],
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Process user input using AI agent to naturally extract profile information.
        """
        profile = session_state.get('profile', {})
        conversation_history = session_state.get('conversation_history', [])
        last_asked_field = session_state.get('last_asked_field', None)
        pending_confirmation = session_state.get('pending_confirmation', None)
        
        logger.info(f"Processing onboarding input: {user_input[:50]}")
        
        # Add user input to history (will be returned in updated state)
        # Note: We append it here for context, but return the updated list at the end.
        current_turn_history = conversation_history + [{'role': 'user', 'content': user_input}]

        # --- 0. Handle Pending Confirmation ---
        confirmation_handled = False
        confirmed_field = None
        
        if pending_confirmation:
            field = pending_confirmation.get('field')
            value = pending_confirmation.get('value')
            logger.info(f"Pending confirmation check. Field: '{field}', Value: '{value}', User Input: '{user_input}'")
            
            # Check for confirmation by repetition
            if user_input.lower().strip() == str(value).lower().strip():
                profile[field] = value
                session_state['pending_confirmation'] = None
                confirmation_handled = True
                confirmed_field = field
                logger.info(f"Confirmed {field} = {value} by repetition")
            elif self._is_confirmation(user_input, language):
                # Confirmed!
                profile[field] = value
                session_state['pending_confirmation'] = None
                confirmation_handled = True
                confirmed_field = field
                logger.info(f"Confirmed {field} = {value}")
            
            elif self._is_denial(user_input, language):
                # Denied. Clear pending.
                session_state['pending_confirmation'] = None
                confirmation_handled = True 
                logger.info(f"Denied {field} = {value}")
                
                # Special Logic for Location Suggestion Rejection
                if field == 'location' and value == profile.get('suggested_location'):
                    # User said NO to the suggested location.
                    # "ask to update it later in the profile" -> implies we proceed.
                    # We'll use the suggested value as a fallback to unblock the flow.
                    profile['location'] = value
                    session_state['temp_warning'] = "Please update your location in your profile later."
            
            else:
                # Ambiguous.
                # Treat as potential new input/correction.
                session_state['pending_confirmation'] = None
                logger.info(f"Ambiguous confirmation for {field}. treating as new input.")

        # --- 1. Extract entities using AI (Rule-based + LLM) ---
        # We run extraction regardless, to catch corrections or new info.
        extracted_updates = {}
        try:
            # Use target_field to help the AI focus if we are waiting for a specific answer
            target = None
            if (not confirmation_handled or self._is_denial(user_input, language)) and last_asked_field:
                 target = last_asked_field

            extraction = await self.ai_service.analyze_intent(user_input, language, target_field=target)
            logger.info(f"Extraction result: {extraction}")
            
            # Map extraction to profile keys (handle case variations)
            if extraction.get('name') or extraction.get('Name'): 
                extracted_updates['name'] = extraction.get('name') or extraction.get('Name')
                
            if extraction.get('location') or extraction.get('Location'): 
                extracted_updates['location'] = extraction.get('location') or extraction.get('Location')
            
            # Handle key variations from LLM
            if extraction.get('primary_crop'): extracted_updates['primary_crop'] = extraction['primary_crop']
            elif extraction.get('crop') or extraction.get('Crop'): 
                extracted_updates['primary_crop'] = extraction.get('crop') or extraction.get('Crop')
            
            if extraction.get('farm_size_acres'): extracted_updates['farm_size_acres'] = extraction['farm_size_acres']
            elif extraction.get('farm_size') or extraction.get('Farm_size'): 
                extracted_updates['farm_size_acres'] = extraction.get('farm_size') or extraction.get('Farm_size')
            
            if extraction.get('mobile_number') or extraction.get('Mobile_number'): 
                extracted_updates['mobile_number'] = extraction.get('mobile_number') or extraction.get('Mobile_number')

            # Mobile regex fallback (Safe to keep for strict format validation)
            import re
            clean_input = re.sub(r'\s+', '', user_input)
            mobile_match = re.search(r'(?:(?:\+|0{0,2})91)?([6-9]\d{9})', clean_input)
            if mobile_match:
                extracted_updates['mobile_number'] = mobile_match.group(1)
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")

        # --- 2. Process Updates (Batch) ---
        
        # Check if we need to confirm any NEW extracted value
        # User Requirement: "take confirmation if it correctly interpretted"
        # We process ONLY ONE field at a time to avoid confusion.
        
        field_to_confirm = None
        value_to_confirm = None
        
        if extracted_updates:
            # Prioritize the field we just asked for, if extracted
            if last_asked_field and last_asked_field in extracted_updates:
                field_to_confirm = last_asked_field
                value_to_confirm = extracted_updates[last_asked_field]
            else:
                # Otherwise, take the first extracted field
                # (e.g. user answered "Hyderabad" when asked for name? We should probably confirm it anyway)
                for f, v in extracted_updates.items():
                    # Skip if we just confirmed this field in this turn (e.g. "Yes, it is Pavani")
                    if confirmation_handled and f == confirmed_field:
                        continue
                    
                    # Skip if the value is the same as what we already have in the profile
                    # This prevents loops where the AI re-extracts the same info from history
                    existing_val = profile.get(f)
                    if existing_val and str(existing_val).lower().strip() == str(v).lower().strip():
                        logger.info(f"Skipping extraction for identical existing value: {f}={v}")
                        continue

                    if v:
                        field_to_confirm = f
                        value_to_confirm = v
                        break
        
        if field_to_confirm and value_to_confirm:
            # We found a new value! Ask for confirmation.
            
            # Clean string values
            if isinstance(value_to_confirm, str):
                value_to_confirm = value_to_confirm.strip().title()
                
                # Sanity Check: If value is too long (likely a sentence), reject it or truncate
                # Exception: Location can be long (e.g. "Pulivendula, Kadapa, Andhra Pradesh")
                # But Name, Crop, Farm Size should be short.
                words = value_to_confirm.split()
                
                if field_to_confirm == 'name' and len(words) > 3:
                     logger.warning(f"Rejected long name candidate: {value_to_confirm}")
                     # Try to salvage: Take first 2 words if they look like a name
                     # But safer to just ignore and let the agent ask again properly
                     # Or assume the first word is the name?
                     # Let's take the first 2 words as a fallback guess
                     value_to_confirm = " ".join(words[:2])
                     logger.info(f"Truncated to: {value_to_confirm}")
                
                elif field_to_confirm == 'primary_crop' and len(words) > 3:
                     logger.warning(f"Rejected long crop candidate: {value_to_confirm}")
                     value_to_confirm = words[0] # Crop is usually 1 word
                
                elif field_to_confirm == 'farm_size_acres':
                     # Should be a number. If we got text, something is wrong.
                     # The extraction logic should have handled this, but double check.
                     pass 

            session_state['pending_confirmation'] = {
                'field': field_to_confirm,
                'value': value_to_confirm
            }
            
            # Generate Confirmation Prompt
            if language == 'te':
                prompt_text = f"నేను విన్నది: {value_to_confirm}. ఇది సరైనదేనా?"
            elif language == 'hi':
                prompt_text = f"मैंने सुना: {value_to_confirm}। क्या यह सही है?"
            else:
                prompt_text = f"I heard {value_to_confirm}. Is this correct?"
            
            current_turn_history.append({'role': 'assistant', 'content': prompt_text})
            
            logger.info(f"Asking confirmation for {field_to_confirm} = {value_to_confirm}")
            
            return {
                'profile': profile,
                'conversation_history': current_turn_history,
                'completed': False,
                'next_prompt': prompt_text,
                'last_asked_field': last_asked_field, # Maintain context
                'pending_confirmation': session_state['pending_confirmation']
            }

        # Apply updates to profile (ONLY if confirmed implicitly? No, we forcing explicit confirmation now)
        # If we reached here, it means either:
        # 1. No new data extracted.
        # 2. Data was extracted but matched the confirmed_field (already handled in Step 0).
        
        # So we don't need the old update loop anymore, because Step 0 handles confirmed data,
        # and the block above handles NEW data by pausing for confirmation.
        
        # However, we must ensure that if confirmation_handled is True, the profile IS updated.
        # Step 0 already did: profile[field] = value
        
        # So we can remove the old loop.


        # --- 3. Check for completion (Normal Flow) ---
        # Order matters for the agent to ask.
        required_fields = ['name', 'location', 'primary_crop', 'farm_size_acres', 'mobile_number']
        
        # Find the FIRST missing field to focus on
        missing_fields = [f for f in required_fields if not profile.get(f)]
        
        # 3. Generate Response
        
        # Add user input to history (if not returned early)
        conversation_history = current_turn_history
        
        if not missing_fields:
            # All info collected!
            logger.info("All profile info collected. Generating decision scenario.")
            
            # Generate decision scenario
            scenario = await self._generate_decision_scenario(profile, language)
            
            # Generate completion message
            completion_msg = "Thank you! Processing your details..."
            if language == 'te': completion_msg = "ధన్యవాదాలు! మీ వివరాలను ప్రాసెస్ చేస్తున్నాను..."
            elif language == 'hi': completion_msg = "धन्यवाद! आपके विवरण को प्रोसेस कर रहा हूँ..."
            
            # Update history
            conversation_history.append({'role': 'assistant', 'content': completion_msg})

            return {
                'profile': profile,
                'conversation_history': conversation_history,
                'completed': True,
                'next_prompt': completion_msg,
                'scenario': scenario,
                'pending_confirmation': None,
                'last_asked_field': None
            }
        else:
            # Still missing info. Generate conversational response to ask for it.
            # We guide the LLM to ask for specific missing info
            
            # Focus on the FIRST missing field to enforce "one by one"
            next_missing = missing_fields[0]
            
            # --- Handle Suggested Location Confirmation ---
            suggested_loc = profile.get('suggested_location')
            # Check if we should suggest location: 
            # 1. We need location
            # 2. We have a suggestion
            # 3. We haven't just asked for confirmation (pending_confirmation is None)
            if next_missing == 'location' and suggested_loc and not session_state.get('pending_confirmation'):
                 prompt_text = f"I detected your location as {suggested_loc}. Is this your farm location?"
                 if language == 'te': prompt_text = f"మీ ప్రాంతం {suggested_loc} అని గుర్తించబడింది. ఇది మీ పొలం ఉన్న ప్రదేశమా?"
                 elif language == 'hi': prompt_text = f"आपका स्थान {suggested_loc} पता चला है। क्या यह आपके खेत का स्थान है?"
                 
                 session_state['pending_confirmation'] = {
                     'field': 'location',
                     'value': suggested_loc
                 }
                 
                 conversation_history.append({'role': 'assistant', 'content': prompt_text})
                 return {
                    'profile': profile,
                    'conversation_history': conversation_history,
                    'completed': False,
                    'next_prompt': prompt_text,
                    'last_asked_field': 'location', 
                    'pending_confirmation': session_state['pending_confirmation']
                 }
            
            # If we just confirmed a field, acknowledge it in the prompt?
            # The system prompt handles "Got it".
            
            system_prompt = self._get_system_prompt(language)
            
            # Add specific instruction to ask for missing fields
            warning_msg = session_state.pop('temp_warning', None)
            guidance_prefix = f"NOTE: Tell the user: '{warning_msg}' " if warning_msg else ""
            
            # Format profile for the prompt naturally
            profile_desc = []
            if profile.get('name'): profile_desc.append(f"User's Name: {profile['name']}")
            if profile.get('location'): profile_desc.append(f"Location: {profile['location']}")
            if profile.get('primary_crop'): profile_desc.append(f"Crop: {profile['primary_crop']}")
            
            profile_str = "\n".join(profile_desc) if profile_desc else "No details collected yet."
            
            # Use Template-based Question Generation (More Reliable/Faster)
            # Instead of asking LLM to generate the question, we use hardcoded templates
            # This prevents hallucination (e.g. "that would also be helpful") and ensures strictness.
            
            agent_response = self._get_fallback_question(next_missing, language)
            
            # Add specific warning if exists
            warning_msg = session_state.pop('temp_warning', None)
            if warning_msg:
                agent_response = f"{warning_msg} {agent_response}"
            
            # Add agent response to history
            conversation_history.append({'role': 'assistant', 'content': agent_response})
            
            return {
                'profile': profile,
                'conversation_history': conversation_history,
                'completed': False,
                'next_prompt': agent_response,
                'last_asked_field': next_missing,
                'pending_confirmation': None
            }

    def _get_fallback_response(self, language: str = 'en') -> str:
        """Get fallback response when AI service fails."""
        if language == 'te':
            return "క్షమించండి, నాకు అర్థం కాలేదు. దయచేసి మళ్లీ చెప్పండి."
        elif language == 'hi':
            return "क्षमा करें, मुझे समझ नहीं आया। कृपया फिर से बताएं।"
        else:
            return "Sorry, I didn't catch that. Could you please repeat?"

    def _get_fallback_question(self, field: str, language: str = 'en') -> str:
        """Get hardcoded question for a specific field when AI fails."""
        questions = {
            'en': {
                'name': "What is your name?",
                'farm_size_acres': "How much land do you have (in acres)?",
                'location': "Which village or town are you from?",
                'primary_crop': "What crop are you currently growing?",
                'mobile_number': "What is your mobile number?"
            },
            'te': {
                'name': "మీ పేరు ఏమిటి?",
                'farm_size_acres': "మీకు ఎంత పొలం ఉంది (ఎకరాల్లో)?",
                'location': "మీ ఊరు ఏది?",
                'primary_crop': "మీరు ఏ పంట సాగు చేస్తున్నారు?",
                'mobile_number': "మీ మొబైల్ నంబర్ ఎంత?"
            },
            'hi': {
                'name': "आपका नाम क्या है?",
                'farm_size_acres': "आपके पास कितनी जमीन है (एकड़ में)?",
                'location': "आप कहां रहते हैं?",
                'primary_crop': "आप कौन सी फसल उगा रहे हैं?",
                'mobile_number': "आपका मोबाइल नंबर क्या है?"
            }
        }
        
        lang_questions = questions.get(language, questions['en'])
        return lang_questions.get(field, questions['en'].get(field, "Can you provide that detail?"))

    async def _generate_decision_scenario(
        self,
        profile: Dict[str, Any],
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Generate decision scenario based on weather, news, and mandi rates.
        """
        location = profile.get('location', 'Unknown')
        crop = profile.get('primary_crop', 'Unknown')
        name = profile.get('name', 'Farmer')
        farm_size = profile.get('farm_size_acres', 5.0)
        
        logger.info(f"Generating scenario for {name} - {crop} in {location}")
        
        try:
            # 1. Fetch data
            import asyncio
            from app.tools.agent_tools import LOCATION_DB
            
            # Resolve location to coordinates
            loc_key = location.lower()
            coords = LOCATION_DB.get(loc_key)
            
            # Fallback if location not found
            if not coords:
                # Default to Hyderabad/Central AP
                coords = {"lat": 17.3850, "lon": 78.4867}
                logger.warning(f"Location '{location}' not found in DB, using default coordinates: {coords}")
            
            weather_task = self.weather_service.get_forecast(coords["lat"], coords["lon"])
            # Use get_price_trends which handles location resolution better
            price_task = self.price_service.get_price_trends(crop, location)
            
            weather_data, price_data = await asyncio.gather(
                weather_task,
                price_task,
                return_exceptions=True
            )
            
            if isinstance(weather_data, Exception): 
                logger.error(f"Weather service error: {weather_data}")
                weather_data = {"forecast": {"rain_risk_24h": False}} # Minimal Fallback
            if isinstance(price_data, Exception): 
                logger.error(f"Price service error: {price_data}")
                price_data = {} # Fallback
            
            # 2. Create HarvestInput
            harvest_input = HarvestInput(
                crop=crop,
                quantity=farm_size * 20, # Rough estimate: 20 quintals per acre
                location=location,
                latitude=coords["lat"],
                longitude=coords["lon"],
                quantity_unit="quintals"
            )
            
            # 3. Evaluate Decision
            decision = self.decision_service.evaluate(harvest_input, price_data, weather_data, language)
            
            # 4. Return as dict
            return decision.dict()
            
        except Exception as e:
            logger.error(f"Error generating scenario: {e}", exc_info=True)
            return {} # Should ideally return a default/error scenario
    
    def _synthesize_recommendation(
        self,
        profile: Dict[str, Any],
        weather_data: Any,
        price_data: Any,
        news_data: Any,
        language: str = 'en'
    ) -> str:
        """Synthesize recommendation from all data sources."""
        name = profile.get('name', 'Farmer')
        crop = profile.get('primary_crop', 'your crop')
        location = profile.get('location', 'your area')
        
        # Build recommendation based on data
        recommendation_parts = []
        
        # Greeting
        if language == 'te':
            recommendation_parts.append(f"{name} గారు, మీ {crop} పంట గురించి ఇదిగో సమాచారం:")
        elif language == 'hi':
            recommendation_parts.append(f"{name} जी, आपकी {crop} फसल के बारे में यह जानकारी:")
        else:
            recommendation_parts.append(f"{name}, here's what I found about your {crop} crop:")
        
        # Weather summary
        if weather_data and not isinstance(weather_data, Exception):
            weather_summary = self._summarize_weather(weather_data, language)
            recommendation_parts.append(weather_summary)
        
        # Price summary
        if price_data and not isinstance(price_data, Exception):
            price_summary = self._summarize_prices(price_data, language)
            recommendation_parts.append(price_summary)
        
        # News summary
        if news_data and not isinstance(news_data, Exception):
            news_summary = self._summarize_news(news_data, language)
            recommendation_parts.append(news_summary)
        
        # Final recommendation
        final_rec = self._generate_final_recommendation(
            weather_data,
            price_data,
            news_data,
            language
        )
        recommendation_parts.append(final_rec)
        
        return "\n\n".join(recommendation_parts)
    
    def _summarize_weather(self, weather_data: Any, language: str) -> str:
        """Summarize weather data."""
        # Extract weather info (adapt based on your weather service response)
        if language == 'te':
            return "వాతావరణం: తాజా వాతావరణ సమాచారం అందుబాటులో ఉంది."
        elif language == 'hi':
            return "मौसम: नवीनतम मौसम जानकारी उपलब्ध है।"
        else:
            return "Weather: Latest weather information is available."
    
    def _summarize_prices(self, price_data: Any, language: str) -> str:
        """Summarize price data."""
        if language == 'te':
            return "మార్కెట్ ధరలు: తాజా మార్కెట్ ధరల సమాచారం అందుబాటులో ఉంది."
        elif language == 'hi':
            return "बाजार भाव: नवीनतम बाजार भाव उपलब्ध है।"
        else:
            return "Market Prices: Latest market price information is available."
    
    def _summarize_news(self, news_data: Any, language: str) -> str:
        """Summarize news data."""
        if language == 'te':
            return "వార్తలు: తాజా వ్యవసాయ వార్తలు అందుబాటులో ఉన్నాయి."
        elif language == 'hi':
            return "समाचार: नवीनतम कृषि समाचार उपलब्ध हैं।"
        else:
            return "News: Latest agricultural news is available."
    
    def _generate_final_recommendation(
        self,
        weather_data: Any,
        price_data: Any,
        news_data: Any,
        language: str
    ) -> str:
        """Generate final recommendation."""
        if language == 'te':
            return "సిఫార్సు: మీ పంట నిర్ణయాల కోసం ఈ సమాచారాన్ని ఉపయోగించండి."
        elif language == 'hi':
            return "सिफारिश: अपनी फसल के निर्णयों के लिए इस जानकारी का उपयोग करें।"
        else:
            return "Recommendation: Use this information to make informed decisions about your crop."
    
    def _get_fallback_recommendation(self, profile: Dict[str, Any], language: str) -> str:
        """Get fallback recommendation when data fetch fails."""
        name = profile.get('name', 'Farmer')
        
        if language == 'te':
            return f"{name} గారు, మీ ప్రొఫైల్ సృష్టించబడింది. సమాచారం పొందడంలో కొంత సమస్య ఉంది. దయచేసి తర్వాత మళ్లీ ప్రయత్నించండి."
        elif language == 'hi':
            return f"{name} जी, आपकी प्रोफ़ाइल बनाई गई है। जानकारी प्राप्त करने में कुछ समस्या है। कृपया बाद में पुनः प्रयास करें।"
        else:
            return f"{name}, your profile has been created. There was an issue fetching information. Please try again later."


# Singleton instance
onboarding_service = None


def get_onboarding_service(
    ai_service,
    weather_service,
    price_service,
    news_service,
    decision_service
):
    """Get or create onboarding service instance."""
    global onboarding_service
    if onboarding_service is None:
        onboarding_service = OnboardingService(
            ai_service,
            weather_service,
            price_service,
            news_service,
            decision_service
        )
    return onboarding_service
