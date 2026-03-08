import os
import uuid
import logging
import tempfile
import asyncio
from typing import Dict, Any, Optional, List, Union
import json
import re
import requests
from .ai_service_interface import AIService
from app.tools.agent_tools import weather_tool, market_tool, LOCATION_DB
from app.services.news_service import news_service
from app.services.decision_service import DecisionService
from app.models.harvest import HarvestInput

logger = logging.getLogger(__name__)

class LocalAIService(AIService):
    """
    Open Source Implementation using:
    - OpenAI Whisper (Local) for Speech-to-Text
    - RAG Pipeline (SentenceTransformers + ChromaDB) for Knowledge
    - Deterministic Agent (Router) for Tool Execution
    """
    def __init__(self):
        super().__init__()
        # Use existing Ollama instance
        from app.core.config import settings
        self.ollama_url = settings.OLLAMA_BASE_URL
        self.llm_model = settings.OLLAMA_MODEL
        self._ollama_available = True
        self._ollama_down_until_ts = 0
        
        # Check connection
        try:
            requests.post(self.ollama_url, json={"model": self.llm_model, "prompt": "hi", "stream": False}, timeout=5)
            logger.info(f"Connected to Ollama ({self.llm_model})")
            self._ollama_available = True
        except Exception as e:
            import time
            self._ollama_available = False
            self._ollama_down_until_ts = time.time() + 300
            logger.warning(f"Ollama unavailable (startup): {e}. Falling back for 5 minutes.")

        # Initialize Whisper (lazy load to speed up startup)
        self.whisper_model = None
        
        # Initialize RAG Service (lazy load)
        self.rag_service = None
        
        # Initialize Decision Service
        self.decision_service = DecisionService()

    async def generate_audio(self, text: str, language_code: str = 'en-IN', voice_settings: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate TTS audio file using gTTS.
        Supports accents via 'tld' in voice_settings.
        """
        try:
            from gtts import gTTS
            
            # Map language code to gTTS language
            lang = 'en'
            if 'te' in language_code.lower(): lang = 'te'
            elif 'hi' in language_code.lower(): lang = 'hi'
            
            # Extract accent (TLD) - Default to Indian English (co.in)
            tld = 'co.in'
            if voice_settings and 'accent' in voice_settings:
                tld = voice_settings['accent']
                
            # Clean text for TTS (remove markdown)
            clean_text = text.replace('*', '').replace('#', '').replace('_', '').replace('`', '')
            # Remove links [text](url) -> text
            clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_text)
            
            tts = gTTS(text=clean_text, lang=lang, tld=tld, slow=False)
            
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
                tts.save(temp_audio_path)
                
            return temp_audio_path
        except Exception as e:
            logger.error(f"TTS Generation Error: {e}")
            return None

    async def transcribe_audio(self, audio_bytes: bytes, language_code: str = 'en-IN') -> str:
        """
        Convert audio bytes to text using local Whisper model.
        """
        # Lazy load Whisper model with retries
        if not self.whisper_model:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Loading Whisper model (base)... Attempt {attempt + 1}/{max_retries}")
                    import whisper
                    # Run in executor to avoid blocking the event loop
                    loop = asyncio.get_event_loop()
                    self.whisper_model = await loop.run_in_executor(None, lambda: whisper.load_model("base"))
                    logger.info("Whisper model loaded successfully.")
                    break
                except Exception as e:
                    logger.error(f"Failed to load Whisper model (Attempt {attempt + 1}): {e}")
                    if attempt == max_retries - 1:
                        return "Error: Speech-to-text service unavailable."
                    await asyncio.sleep(1) # Wait a bit before retry

        try:
            # Write bytes to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio_path = temp_audio.name
            
            # Extract language code (e.g., 'te' from 'te-IN')
            lang = 'en'
            if language_code:
                if 'te' in language_code.lower(): lang = 'te'
                elif 'hi' in language_code.lower(): lang = 'hi'
            
            logger.info(f"Transcribing audio with language hint: {lang} (Original: {language_code})")

            # Transcribe with language hint and initial prompt to guide style
            initial_prompt = ""
            if lang == 'te': initial_prompt = "నమస్కారం, వ్యవసాయం, పంటలు, ధరలు, వాతావరణం, టమాటా, వరి. నాకు సహాయం కావాలి."
            elif lang == 'hi': initial_prompt = "नमस्ते, खेती, फसल, बाज़ार भाव, मौसम, टमाटर, धान. मुझे मदद चाहिए."
            
            # Use specific options for better accuracy
            options = {
                "language": lang,
                "initial_prompt": initial_prompt,
                "fp16": False, # Force FP32 for better compatibility on CPU
                "beam_size": 5, # Improve accuracy
                "best_of": 5,
                "temperature": 0.0 # Deterministic
            }
            
            # Run transcription in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.whisper_model.transcribe(temp_audio_path, **options)
            )
            text = result["text"].strip()
            
            # Filter common Whisper hallucinations
            if self._is_hallucination(text):
                logger.warning(f"Filtered hallucination in transcription: {text[:100]}...")
                return ""
            
            logger.info(f"Transcription Result ({lang}): {text}")
            
            # Cleanup
            os.remove(temp_audio_path)
            
            return text
        except Exception as e:
            logger.error(f"Transcription Error: {e}")
            return ""

    def _is_hallucination(self, text: str) -> bool:
        """
        Check for common Whisper hallucinations (repetition loops).
        """
        # 1. Check for specific phrases
        hallucinations = [
            "Subtitles by", "Amara.org", "Thank you", "MBC", "Al Jazeera", 
            "Subscribe", "Copyright", "All rights reserved", "Community", 
            "Likely", "The following"
        ]
        for h in hallucinations:
            if h.lower() in text.lower():
                return True
                
        # 2. Check for Repetition Loops (e.g. "Naaku, Naaku, Naaku...")
        import re
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        words = clean_text.split()
        
        if len(words) > 8:
            unique_words = set(words)
            ratio = len(unique_words) / len(words)
            # If less than 40% words are unique (heavy repetition), it's likely a loop
            # e.g. "a b a b a b a b" -> 2/8 = 0.25 -> True
            if ratio < 0.4: 
                return True
                
            # Check for single word repeating dominantly
            # e.g. "pam pam pam pam pam"
            from collections import Counter
            counts = Counter(words)
            most_common = counts.most_common(1)
            if most_common and most_common[0][1] > len(words) * 0.6:
                 return True
                 
        return False

    def _get_lang_name(self, code: str) -> str:
        if "te" in code.lower(): return "Telugu"
        if "hi" in code.lower(): return "Hindi"
        return "English"

    def _extract_entities_from_text_rules(self, text: str) -> Dict[str, Any]:
        """
        Extract entities using regex and heuristic rules.
        Useful for backfilling from history or quick extraction.
        """
        data = {}
        text_lower = text.lower()
        
        # Crop Detection
        if "tomato" in text_lower: data["crop"] = "Tomato"
        if "paddy" in text_lower: data["crop"] = "Paddy"
        if "cotton" in text_lower: data["crop"] = "Cotton"
        if "micro crops" in text_lower or "micro greens" in text_lower: data["crop"] = "Micro Crops"
        
        # Location Detection (Specific Cities)
        if "madanapalle" in text_lower: data["location"] = "Madanapalle"
        if "warangal" in text_lower: data["location"] = "Warangal"
        if "khammam" in text_lower: data["location"] = "Khammam"
        if "hyderabad" in text_lower: data["location"] = "Hyderabad" # Added Hyderabad
        
        # Regex for name
        import re
        name_match = re.search(r"(?:my name is|i am|name is|called)\s+([a-zA-Z\s]+)", text_lower)
        if name_match:
            captured_name = name_match.group(1).strip()
            captured_name = re.split(r'[.,?!]', captured_name)[0].strip()
            stop_words = ["what", "how", "can", "please", "and", "but", "so", "details", "info", "is", "are", "do", "does", "will", "would", "could", "should"]
            words = captured_name.split()
            clean_words = []
            for w in words:
                if w.lower() in stop_words: break
                clean_words.append(w)
            if len(clean_words) > 3: clean_words = clean_words[:2]
            captured_name = " ".join(clean_words)
            invalid_starts = ["from ", "growing ", "farming ", "a farmer", "here"]
            is_invalid = False
            for inv in invalid_starts:
                if captured_name.lower().startswith(inv):
                    is_invalid = True
                    break
            if not is_invalid and len(captured_name) > 1:
                data["name"] = captured_name.title()
                
        # Regex for location (contextual)
        location_match = re.search(r"\b(?:from|in|at|near)\s+([a-zA-Z\s]+)", text_lower)
        if location_match:
             captured_loc = location_match.group(1).strip()
             blacklist = ["my farm", "the village", "town", "city", "here", "there", "now"]
             if len(captured_loc) > 2 and captured_loc not in blacklist:
                 data["location"] = captured_loc.title()
                 
        # Standalone Location Detection (from DB)
        if not data.get("location"):
            sorted_locs = sorted(LOCATION_DB.keys(), key=len, reverse=True)
            for city in sorted_locs:
                if city in text_lower:
                    data["location"] = city.title()
                    break
                    
        # Farm Size
        size_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:acres|acre|hectares|cents|guntas|gunta)", text_lower)
        if size_match:
            data["farm_size"] = float(size_match.group(1))
            
        return data

    async def analyze_intent(self, text: str, language_code: str = 'en-IN', target_field: Optional[str] = None, profile: Optional[Dict[str, Any]] = None, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Extract intent and entities from text.
        If target_field is provided, optimizes extraction for that specific field.
        """
        logger.info(f"Analyzing intent for: {text} in {language_code} (Target: {target_field})")
        lang_name = self._get_lang_name(language_code)
        
        # 1. Rule-based Extraction (Context)
        rule_based_data = {
            "crop": None,
            "location": None,
            "quantity": None,
            "name": None,
            "farm_size": None
        }
        
        # 0. Preprocessing: Handle common typos
        text_lower = text.lower()
        if "weight" in text_lower:
            # Only replace if "sell" is also present to avoid over-correction
            # OR if "or" is present (e.g. "sell or weight", "harvest or weight")
            if "sell" in text_lower or "harvest" in text_lower or " or " in text_lower:
                text_lower = text_lower.replace("weight", "wait")
                text = text.replace("weight", "wait") # Keep original case for extraction
                logger.info(f"Corrected 'weight' to 'wait' in input: {text}")

        # Use profile data as fallback/context
        if profile:
            if profile.get("location"): rule_based_data["location"] = profile["location"]
            if profile.get("primary_crop"): rule_based_data["crop"] = profile["primary_crop"]
            elif profile.get("crop"): rule_based_data["crop"] = profile["crop"]
            
            if profile.get("name"): rule_based_data["name"] = profile["name"]
            if profile.get("farm_size_acres"): rule_based_data["farm_size"] = profile["farm_size_acres"]

        # Use helper method for rules
        extracted_rules = self._extract_entities_from_text_rules(text)
        rule_based_data.update(extracted_rules)

        # 1.1 Explicit Profile Augmentation (Heuristic Override)
        # If user implies ownership ("my crop", "harvest my crop", "sell my crop") 
        # or asks a direct question ("should I sell"), force Profile Context if extraction failed.
        if profile:
             # Crop
             if not rule_based_data.get("crop"):
                 if "my crop" in text_lower or "the crop" in text_lower or "harvest" in text_lower or "sell" in text_lower or "wait" in text_lower:
                     if profile.get("primary_crop"):
                         rule_based_data["crop"] = profile.get("primary_crop")
                     elif profile.get("crop"):
                         rule_based_data["crop"] = profile.get("crop")
                     
                     if rule_based_data.get("crop"):
                         logger.info(f"Using Profile Crop (Augmented): {rule_based_data['crop']}")
             
             # Location
             if not rule_based_data.get("location"):
                 if "my farm" in text_lower or "here" in text_lower or "local" in text_lower or "market" in text_lower or "sell" in text_lower:
                     if profile.get("location"):
                         rule_based_data["location"] = profile.get("location")
                         logger.info(f"Using Profile Location (Augmented): {rule_based_data['location']}")

        # Heuristic: If target is 'name' and input is short, treat it as the name directly
        # This prevents LLM hallucination for simple Indian names (e.g. Pavani -> Pavini)
        if target_field == 'name' and not rule_based_data.get('name'):
            clean_text = text.strip().strip('.').strip()
            
            # Robust Prefix Stripping: Handle "My name is X" where regex might fail
            prefixes = ["my name is", "i am", "name is", "this is", "myself", "it is", "called"]
            lower_text = clean_text.lower()
            for prefix in prefixes:
                if lower_text.startswith(prefix + " ") or lower_text == prefix:
                    clean_text = clean_text[len(prefix):].strip(" .!,")
                    break
            
            words = clean_text.split()
            # Blacklist for common non-name words
            blacklist = ["hello", "hi", "hey", "ok", "okay", "yes", "no", "what", "why", "who", "confirm", "cancel", "start", "stop", "details", "info"]
            if len(words) <= 3 and len(words) > 0 and clean_text.lower() not in blacklist:
                logger.info(f"Heuristic: Treating short input '{clean_text}' as Name")
                rule_based_data["name"] = clean_text.title()

        # 2. LLM Extraction (Ollama)
        llm_data = {}
        # Skip LLM extraction if Ollama is down (circuit breaker)
        import time
        if not self._ollama_available and time.time() < self._ollama_down_until_ts:
            logger.info("Skipping LLM extraction (Ollama in cooldown). Using rule-based only.")
        else:
            try:
                # Dynamic Prompt Construction based on target_field
                if target_field:
                    prompt = f"""
                    Context: The user was asked to provide their {target_field}.
                    User Input: "{text}"
                    
                    Task: Extract the {target_field} from the input.
                    - If the input contains the {target_field}, extract it cleanly (remove "my name is", "i am from", etc.).
                    - **Single-word answers are valid.** If the user just says "Kadapa", extract "Kadapa".
                    - If the input is garbage, irrelevant, or does not contain a valid {target_field} (e.g. "oh my god", "what", "hello"), return null.
                    
                    Detailed Instructions for {target_field}:
                    """
                    
                    if target_field == 'location':
                        prompt += """
                        - Look for Village, Mandal, District, or City names.
                        - If multiple parts are given (e.g., "Pulivendula Mandal, Kadapa District"), extract the full location string.
                        - Examples:
                          - "I am from Kadapa" -> "Kadapa"
                          - "Kadapa" -> "Kadapa"
                          - "Pulivendula Mandal" -> "Pulivendula Mandal"
                          - "My village is Vempalli" -> "Vempalli"
                        """
                    elif target_field == 'name':
                         prompt += """
                        - Look for a person's name.
                        - EXTRACT THE NAME EXACTLY AS SPELLED IN THE INPUT. DO NOT AUTOCORRECT OR CHANGE SPELLING.
                        - Examples:
                          - "My name is Pavani" -> "Pavani"
                          - "Pavani" -> "Pavani"
                          - "I am Suresh" -> "Suresh"
                        """
                    elif target_field == 'primary_crop':
                         prompt += """
                        - Look for crop names (e.g., Tomato, Paddy, Cotton, Chilli).
                        - Examples:
                          - "I grow Tomato" -> "Tomato"
                          - "Tomato" -> "Tomato"
                        """
                    elif target_field == 'farm_size_acres':
                         prompt += """
                        - Look for a number representing the farm size (in acres).
                        - Examples:
                          - "5 acres" -> "5"
                          - "I have 10 acres" -> "10"
                          - "2.5" -> "2.5"
                        """
                    elif target_field == 'mobile_number':
                         prompt += """
                        - Look for a 10-digit mobile number.
                        - Examples:
                          - "9876543210" -> "9876543210"
                          - "My number is 9988776655" -> "9988776655"
                        """
                    
                    prompt += f"""
                    Return ONLY a JSON object with keys: {target_field}.
                    Example: {{"{target_field}": "ExtractedValue"}} or {{"{target_field}": null}}
                    """
                else:
                    context_str = ""
                    if profile:
                        context_str = f"""
                        User Profile Context:
                        - Name: {profile.get('name', 'Unknown')}
                        - Location: {profile.get('location', 'Unknown')}
                        - Crop: {profile.get('primary_crop', 'Unknown')}
                        - Farm Size: {profile.get('farm_size_acres', 'Unknown')} acres
                        """
                    
                    history_str = ""
                    if history:
                        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
                    
                    # Simplified and more forceful prompt
                    prompt = f"""
                    {context_str}
                    User Input (in {lang_name}): "{text}"

                    Task: Analyze the user's primary goal. Choose ONE of the following intents.

                    Intents:
                    - `harvest_advice`: The user wants to know if they should SELL or WAIT to sell their crop. This is the intent if the query contains words like "sell", "wait", "market value", "price", "beneficial to sell", etc., in the context of a decision.
                    - `general_knowledge`: The user is asking a "how to", "what is", or "when is" question that requires a factual answer from a knowledge base. This is the default for informational questions.
                    - `market_price`: A specific request for the price of a crop.
                    - `weather_forecast`: A specific request for the weather.
                    - `onboarding`: Providing personal details.
                    - `small_talk`: Greetings or chit-chat.

                    CRITICAL RULE: If the user mentions "sell" or "wait" in the context of making a decision about their crop, the intent MUST be `harvest_advice`. Do not classify it as `general_knowledge`.

                    History of conversation:
                    {history_str}

                    Return ONLY a JSON object with keys: "intent" and "data".

                    Example 1 (Correct - Harvest Advice):
                    Input: "I think the crop is ready for harvest me to sell it right away or wait"
                    Output: {{"intent": "harvest_advice", "data": {{"action": "sell"}}}}

                    Example 2 (Correct - Harvest Advice):
                    Input: "I want to know the market value and if it is beneficial for me to sell it now or wait"
                    Output: {{"intent": "harvest_advice", "data": {{"action": "sell"}}}}

                    Example 3 (Correct - General Knowledge):
                    Input: "how would the Cotton crop look before the harvest"
                    Output: {{"intent": "general_knowledge", "data": {{"query": "how would the Cotton crop look before the harvest"}}}}

                    Example 4 (Incorrect):
                    Input: "should I sell my crop?"
                    Output: {{"intent": "general_knowledge", "data": {{"query": "should I sell my crop?"}}}}
                    """
                    
                    if history:
                        context_str += "\nConversation History:\n"
                        # Only take last 3 messages to avoid context window issues
                        for msg in history[-3:]:
                             role = "Assistant" if msg.get('role') == 'assistant' else "User"
                             content = msg.get('content', '')[:100] # Truncate long messages
                             context_str += f"- {role}: {content}\n"
                    
                    prompt = f"""
                    Extract the following entities from the user input:
                    {context_str}
                    
                    - intent: The user's intention (e.g., market_price, weather, decision_support, greeting, onboarding_info). If the user is answering a previous question (see History), infer the intent from context (e.g. answering 'Tomato' to 'Which crop?' -> decision_support).
                    - crop: The crop mentioned (e.g., Tomato, Paddy). If user says "my crop", use profile crop. CHECK HISTORY if not in current input.
                    - location: The location mentioned. If user says "here" or "my farm", use profile location. CHECK HISTORY if not in current input.
                    - quantity: The quantity mentioned
                    - name: The user's name
                    - farm_size: The farm size mentioned (in acres). EXTRACT ONLY THE NUMBER.
                    -
                    User Input: "{text}"
                    -
                    CRITICAL: If the user is completing a multi-turn task (like decision support), YOU MUST EXTRACT previously mentioned entities (like crop/location) from the 'Conversation History' to provide a complete set of entities.
                    
                    Return ONLY a JSON object with keys: intent, crop, location, quantity, name, farm_size.
                    Do not include any other text.
                    """
                
                response = requests.post(
                    self.ollama_url, 
                    json={
                        "model": self.llm_model, 
                        "prompt": prompt, 
                        "stream": False,
                        "format": "json" # Force JSON output
                    }, 
                    timeout=5
                )
                
                if response.status_code == 200:
                    try:
                        llm_data = response.json().get("response", "{}")
                        import json
                        llm_data = json.loads(llm_data)
                        
                        # Sanitize farm_size to float
                        if 'farm_size' in llm_data and llm_data['farm_size']:
                            try:
                                # Handle strings like "5 acres" or "10-24" (take first number)
                                val = str(llm_data['farm_size'])
                                import re
                                num = re.search(r"(\d+(?:\.\d+)?)", val)
                                if num:
                                    llm_data['farm_size'] = float(num.group(1))
                                else:
                                    llm_data['farm_size'] = None
                            except:
                                llm_data['farm_size'] = None

                        # Normalize keys if target_field was used
                        if target_field:
                             # Map specific target field back to standard keys if needed
                             # But our standard keys match target_field usually (name, location)
                             # Except 'primary_crop' -> 'crop', 'farm_size_acres' -> 'farm_size'
                             if target_field == 'primary_crop' and 'primary_crop' in llm_data:
                                 llm_data['crop'] = llm_data.pop('primary_crop')
                             if target_field == 'farm_size_acres' and 'farm_size_acres' in llm_data:
                                 llm_data['farm_size'] = llm_data.pop('farm_size_acres')
                                 
                    except:
                        logger.warning("Failed to parse LLM JSON response")
            except Exception as e:
                # Trip circuit breaker
                self._ollama_available = False
                self._ollama_down_until_ts = time.time() + 300
                logger.warning(f"LLM Extraction failed: {e}. Entering cooldown for 5 minutes.")

        # 3. Merge Logic (Prioritize LLM, fallback to Rule-based)
        final_data = rule_based_data.copy()
        
        # Merge LLM data if available and valid
        if llm_data:
            for key, value in llm_data.items():
                if value:
                     # Anti-Hallucination: Discard NAME if it overlaps with LOCATION when target is NOT Name
                     if key == 'name' and target_field and target_field != 'name':
                         # Check against extracted location (from LLM or Rules)
                         loc = llm_data.get('location') or rule_based_data.get('location')
                         if loc and (value in loc or loc in value):
                             logger.warning(f"Discarding Name '{value}' as it overlaps with Location '{loc}' (Target: {target_field})")
                             continue
                         
                         # Check against Crop
                         crop = llm_data.get('crop') or rule_based_data.get('crop')
                         if crop and (value in crop or crop in value):
                             logger.warning(f"Discarding Name '{value}' as it overlaps with Crop '{crop}'")
                             continue

                     # Global Blacklist for Location (Anti-Hallucination)
                     if key == 'location':
                         blacklist_locs = ["do you suggest", "what do you", "suggest", "please suggest", "tell me", "know", "harvest", "sell", "wait"]
                         # Normalize value for check (strip punctuation and whitespace)
                         norm_val = value.strip().lower().strip('?.!,')
                         # Use substring matching for robustness
                         if any(bad in norm_val for bad in blacklist_locs):
                             logger.warning(f"Rejected Blacklisted Location '{value}' (normalized: '{norm_val}')")
                             continue

                     # If target_field is set, we trust LLM extraction for that field more than regex
                     # This helps when regex captures partial/incorrect data (e.g. "Pani Pa" vs "Pavani")
                     # But we still prefer regex for numbers/sizes if they are precise.
                     
                     if target_field and key == target_field:
                         if key == 'farm_size':
                             # For numbers, trust regex if available (usually more precise)
                             if not final_data.get(key):
                                 final_data[key] = value
                         elif key == 'name':
                            # SPECIAL CASE: Name Extraction Conflict
                            # Regex "My name is Pavani" -> "Pavani" (Correct)
                            # LLM sometimes hallucinates "Paviniyar" or similar.
                            
                            # 1. Prefer Regex if available
                            if final_data.get('name'):
                                logger.info(f"Preferring Regex Name '{final_data.get('name')}' over LLM '{value}'")
                                pass # Keep regex value
                            
                            # 2. Prefer Raw Input if it's short (Direct Answer)
                            # e.g. User says "Pavani", LLM says "Pavini" -> Trust "Pavani"
                            elif len(text.split()) <= 3:
                                raw_name = text.strip().strip('.').title()
                                logger.info(f"Preferring Short Input '{raw_name}' over LLM '{value}'")
                                final_data[key] = raw_name
                                
                            else:
                                final_data[key] = value
                                
                         elif key == 'location':
                             # Anti-Hallucination: Check if extracted location is actually in the text
                             # (Fuzzy check: at least 3 chars must match sequentially or words match)
                             # LLM often hallucinates "Kadapa" or "Madanapalle" for random inputs.
                             
                             loc_val = value.lower()
                             input_text = text.lower()
                             
                             # Simple check: Is the value (or a significant part of it) in the input?
                             # Exception: Translated names (e.g. input in Telugu, output in English).
                             # But for now, let's be strict to avoid "Kadapa" hallucination from "nuvvu..."
                             
                             # If input is very different from extracted value, reject it.
                             # But "Hyderabad" vs "Haidarabad" is fine.
                             # "nuvvu what did you understand" vs "Kadapa" -> REJECT.
                             
                             # Heuristic: Check if at least one word of location appears in input (len > 3)
                             loc_words = loc_val.split()
                             found_match = False
                             
                             # Blacklist for bad location extractions (common hallucinations from complex sentences)
                             blacklist_locs = ["do you suggest", "what do you", "suggest", "please suggest", "tell me", "know", "harvest", "sell", "wait"]
                             if loc_val.lower() in blacklist_locs:
                                 logger.warning(f"Rejected Blacklisted Location '{loc_val}'")
                                 continue
                                 
                             for w in loc_words:
                                 if len(w) > 3 and w in input_text:
                                     found_match = True
                                     break
                                 # Allow short matches if input is short? No.
                             
                             # Also allow if input *is* the location (approx)
                             import difflib
                             similarity = difflib.SequenceMatcher(None, input_text, loc_val).ratio()
                             
                             if found_match or similarity > 0.6:
                                 final_data[key] = value
                             else:
                                 logger.warning(f"Rejected Hallucinated Location '{value}' from input '{text}'")
                                 pass # Do not add
                                 
                         else:
                             # For other text fields, trust LLM if it found something
                             final_data[key] = value
                     
                     # Default behavior for non-target fields: Only fill gaps
                     elif key in final_data and not final_data.get(key):
                         final_data[key] = value
                     elif key not in final_data:
                        final_data[key] = value

        # 1.2 Explicit Profile Fallback after LLM
        if profile and not final_data.get("crop"):
            if "my crop" in text_lower or "the crop" in text_lower or "harvest" in text_lower or "sell" in text_lower or "wait" in text_lower:
                if profile.get("primary_crop"):
                    final_data["crop"] = profile.get("primary_crop")
                elif profile.get("crop"):
                    final_data["crop"] = profile.get("crop")
                
                if final_data.get("crop"):
                    logger.info(f"Fallback: Using Profile Crop after LLM: {final_data['crop']}")

        # 4. Single-Word / Direct Answer Fallback (CRITICAL for Onboarding)
        if target_field:
            # Map target_field to internal keys if necessary
            internal_key = target_field
            if target_field == 'primary_crop': internal_key = 'crop'
            elif target_field == 'farm_size_acres': internal_key = 'farm_size'
            
            # Check if we successfully extracted the target field
            extracted_val = final_data.get(internal_key)
            
            if not extracted_val:
                # If we didn't extract it, check if the input itself is a valid candidate
                # Heuristic: Input is short (< 5 words) and doesn't contain negation/confusion
                words = text.split()
                if len(words) <= 5:
                    clean_text = text.strip().strip('.').strip()
                    # Exclude common conversational fillers if they are the ONLY thing said
                    blacklist = [
                        "hello", "hi", "hey", "ok", "okay", "yes", "no", "what", "why", "confirm", "cancel",
                        # Telugu
                        "avunu", "kaadu", "namaskaram", "enti", "enduku", "sare", "bagundi", "naaku",
                        # Hindi
                        "haan", "nahi", "namaste", "kya", "kyon", "thik", "ji", "achha"
                    ]
                    if clean_text.lower() not in blacklist:
                         logger.info(f"Fallback: Treating entire input '{clean_text}' as {internal_key}")
                         final_data[internal_key] = clean_text.title()
                         
                         # Special handling for numbers/farm_size
                         if internal_key == 'farm_size':
                             import re
                             num_match = re.search(r"(\d+(?:\.\d+)?)", clean_text)
                             if num_match:
                                 final_data[internal_key] = float(num_match.group(1))

        # 5. History Backfill (Contextual Entity Recovery)
        if history:
            # Check if we are missing key entities
            missing_crop = not final_data.get("crop")
            missing_location = not final_data.get("location")
            
            if missing_crop or missing_location:
                logger.info("Attempting to backfill missing entities from history...")
                # Iterate backwards through history
                for msg in reversed(history):
                    if msg.get("role") == "user":
                        content = msg.get("content", "")
                        # Run extraction on history message
                        hist_extracted = self._extract_entities_from_text_rules(content)
                        
                        if missing_crop and hist_extracted.get("crop"):
                            final_data["crop"] = hist_extracted["crop"]
                            logger.info(f"Backfilled Crop '{final_data['crop']}' from history: '{content}'")
                            missing_crop = False
                            
                        if missing_location and hist_extracted.get("location"):
                             final_data["location"] = hist_extracted["location"]
                             logger.info(f"Backfilled Location '{final_data['location']}' from history: '{content}'")
                             missing_location = False
                        
                        if not missing_crop and not missing_location:
                            break

        # Default intent logic with Overrides
        # Force decision_support if specific advice keywords are present
        has_advice = "harvest" in text_lower or "decision" in text_lower or "good time" in text_lower or "should i" in text_lower or "suggest" in text_lower or "sell" in text_lower or "wait" in text_lower
        
        # Explicit override for "sell or wait" queries
        # Typo correction: "weight" -> "wait" (very common in voice input)
        text_lower = text_lower.replace("weight", "wait")

        # Heuristic: "sell ... wait" pattern strongly implies Decision Support
        # Broadened to catch "should I sell now", "harvest time", etc.
        triggers_action = ["sell", "harvest", "cut", "market"]
        triggers_timing = ["wait", "now", "time", "later", "hold", "keep", "store"]
        
        has_action = any(t in text_lower for t in triggers_action)
        has_timing = any(t in text_lower for t in triggers_timing)

        if has_action and has_timing:
            has_advice = True
            final_data["intent"] = "decision_support"
            logger.info("Heuristic: Found 'Action + Timing' pattern -> Forcing Decision Support")
            
        logger.info(f"DEBUG: text_lower='{text_lower}', has_advice={has_advice}, current_intent={final_data.get('intent')}")

        has_price = "price" in text_lower or "rate" in text_lower or "mandi" in text_lower or "market" in text_lower

        has_weather = "weather" in text_lower or "rain" in text_lower or "climate" in text_lower
        
        # Override LLM if it missed decision support context
        if has_advice:
             final_data["intent"] = "decision_support"
        elif has_price and has_weather:
             final_data["intent"] = "decision_support"

        # Fallback Intent Logic (Moved Up)
        # Check heuristics if intent is missing, unknown, OR general_chat (to catch missed specific intents)
        if not final_data.get("intent") or final_data.get("intent") in ["unknown", "general_chat"]:
            if has_price:
                final_data["intent"] = "market_price"
            elif has_weather:
                final_data["intent"] = "weather"
            elif "hello" in text_lower or "hi" in text_lower or "namaste" in text_lower:
                final_data["intent"] = "greeting"
            else:
                # Fallback: If we have a location but no intent
                # This handles "Hyderabad Telangana" as a standalone answer
                if final_data.get("location"):
                    # If we ALSO have a crop (e.g. from history), assume Decision Support
                    if final_data.get("crop"):
                         logger.info(f"Heuristic: Location + Crop ('{final_data['crop']}') -> defaulting to Decision Support")
                         final_data["intent"] = "decision_support"
                    # Else if standalone location -> Weather
                    elif len(text.split()) <= 6:
                         logger.info(f"Heuristic: Standalone location '{final_data['location']}' -> defaulting to Weather intent")
                         final_data["intent"] = "weather"
                    else:
                         final_data["intent"] = "general_chat"
                else:
                    final_data["intent"] = "general_chat"
             
        # Use profile to fill missing entities for relevant intents
        if profile and final_data.get("intent") in ["decision_support", "weather", "market_price", "news"]:
             if not final_data.get("crop") and profile.get("primary_crop"):
                 final_data["crop"] = profile.get("primary_crop")
                 logger.info(f"Backfilled Crop from Profile: {final_data['crop']}")
                 
             if not final_data.get("location") and profile.get("location"):
                 final_data["location"] = profile.get("location")
                 logger.info(f"Backfilled Location from Profile: {final_data['location']}")

        # Strong Heuristic: If we have both Crop and Location, it's likely a specific query
        if final_data.get("crop") and final_data.get("location"):
             current_intent = final_data.get("intent")
             # Only override if it's generic or greeting (which might be a hallucination for location names)
             if not current_intent or current_intent in ["unknown", "general_chat", "greeting"]:
                 logger.info(f"Heuristic: Found Crop + Location -> Forcing Decision Support (Overriding '{current_intent}')")
                 final_data["intent"] = "decision_support"

        logger.info(f"Analyzed Intent: {final_data}")
        
        # Optimization: If target_field is set, we are in a controlled flow (Onboarding).
        # Return the extracted data immediately, skipping tool execution.
        if target_field:
            return final_data
        
        # Extract variables for tool execution
        intent = final_data.get("intent")
        crop = final_data.get("crop")
        location = final_data.get("location")
        quantity = final_data.get("quantity")
        
        # 3. Execute Tool or Return Intent
        if intent == "decision_support":
            # Check for missing slots
            missing = []
            if not crop: missing.append("crop")
            if not location: missing.append("location")
            # Quantity is optional, default to generic
            if not quantity: quantity = "10"
            
            if missing:
                # Generate a question to ask for missing info
                missing_str = ", ".join(missing)
                prompt = f"""
                The user needs farming decision support but is missing critical information: {missing_str}.
                
                Your Task:
                1. Acknowledge the user's question about selling/harvesting.
                2. Politely ask for the missing details ({missing_str}) to run the simulation.
                3. DO NOT give generic advice. DO NOT answer "It depends".
                4. Ask specifically: "Which crop?" or "Where is your farm located?"
                
                User Query: "{text}"
                Language: {lang_name}
                """
                # Use profile name if available
                user_name = (profile.get('name') if profile else None) or 'Farmer'
                if user_name != 'Farmer':
                    prompt += f"\nAddress the user as {user_name}."

                response_text = await self._generate_llm_response(prompt, "", lang_name)
                
                return {
                    **final_data,
                    "error": "Missing slots",
                    "missing": missing,
                    "response": response_text
                }
            
            # All info present - Execute decision logic
            # 1. Get Weather (Structured)
            weather_data = await weather_tool.run_raw(location)
            
            # Synthetic Fallback for Weather
            if not weather_data or "error" in str(weather_data).lower() or not isinstance(weather_data, dict):
                logger.warning(f"Weather tool failed for {location}. Using synthetic data.")
                weather_data = {
                    "location": location,
                    "forecast": [
                        {"day": "Today", "condition": "Sunny", "temp_max": 32, "temp_min": 24, "rain_chance": 0},
                        {"day": "Tomorrow", "condition": "Partly Cloudy", "temp_max": 31, "temp_min": 23, "rain_chance": 10},
                        {"day": "Day 3", "condition": "Cloudy", "temp_max": 30, "temp_min": 22, "rain_chance": 20}
                    ],
                    "current": {"temp": 30, "condition": "Sunny", "humidity": 45}
                }
            
            # 2. Get Market Price (Structured)
            market_data = await market_tool.run_raw(crop, location)
            
            # Synthetic Fallback for Market
            if not market_data or "error" in str(market_data).lower() or not isinstance(market_data, dict) or not market_data.get("current_price"):
                logger.warning(f"Market tool failed for {crop} in {location}. Using synthetic data.")
                market_data = {
                    "market": f"{location} Mandi",
                    "commodity": crop,
                    "current_price": 2500,
                    "min_price": 2200,
                    "max_price": 2800,
                    "trend": "stable",
                    "unit": "Quintal",
                    "history": [
                        {"date": "3 days ago", "price": 2400},
                        {"date": "2 days ago", "price": 2450},
                        {"date": "Yesterday", "price": 2500}
                    ]
                }
            
            # 3. Generate Harvest Decision Scenarios
            raw_quantity = final_data.get("quantity", 10)
            try:
                quantity = float(raw_quantity)
            except (ValueError, TypeError):
                quantity = 10.0
                
            harvest_input = HarvestInput(
                crop=crop,
                location=location,
                quantity=quantity, 
                latitude=0, # Will be handled by service
                longitude=0,
                storage_condition="open"
            )
            
            # Extract lang code (e.g. 'te' from 'Telugu')
            lang_code_short = 'en'
            if 'te' in language_code: lang_code_short = 'te'
            elif 'hi' in language_code: lang_code_short = 'hi'
            
            decision = self.decision_service.evaluate(harvest_input, market_data, weather_data, language=lang_code_short)
            
            # 4. Get News (Contextual)
            news_response = await news_service.get_news(crop=crop, limit=3)
            news_items = news_response.get("articles", [])
            news_summary = "Relevant News:\n" + "\n".join([f"- {item['title']} ({item['source']})" for item in news_items]) if news_items else "No specific news found for this crop."
            
            # 5. Synthesize Advice
            user_name = (profile.get('name') if profile else None) or 'Farmer'
            farm_size = f"{profile.get('farm_size_acres')} acres" if profile and profile.get('farm_size_acres') else "N/A"
            
            logger.info(f"DEBUG: Synthesizing advice for User: {user_name}, Farm Size: {farm_size}")

            context = f"""
            User Profile:
            - Name: {user_name}
            - Farm Size: {farm_size}
            
            User Request: "Help me decide about my {quantity} of {crop} in {location}."
            
            DECISION SCENARIOS GENERATED:
            1. Sell Now: {decision.scenarios[0].expected_revenue_range}
            2. Wait 24h: {decision.scenarios[1].expected_revenue_range} ({decision.scenarios[1].risk_assessment})
            
            MARKET DATA:
            Price: {market_data.get('current_price', 'N/A')}
            Trend: {market_data.get('trend', 'N/A')}
            
            WEATHER SUMMARY:
            {decision.weather_summary}
            
            NEWS HEADLINES (Context):
            {news_summary}
            """
            
            synthesis_prompt = f"""
            You are an expert agricultural advisor helping a farmer named {user_name}.
            
            Analyze the provided DATA SOURCES (Weather, Market, News) to help the farmer make their own decision.
            
            CRITICAL INSTRUCTIONS:
            - START your response by saying "Hello {user_name},".
            - DO NOT give a direct command like "You should sell" or "You must wait".
            - Instead, PRESENT THE POSSIBILITIES and factors (Prices, Weather, Risks).
            - Use ONLY the provided data. Do NOT hallucinate prices or weather.
            - All prices are in Rupees (₹) per Quintal. NEVER use Dollars ($) or Pounds.
            
            STRICTLY follow this output format:
            
            Hello {user_name}, here is the analysis for your {crop} in {location}:

            **Current Status**:
            *   **Market Price**: [Current Price] (Trend: [Up/Down/Stable])
            *   **Weather**: [3-day forecast summary]

            **Possibilities**:
            1.  **If you Sell Now**: You get [Current Price]. This is a safe option to secure immediate income.
            2.  **If you Wait**: Prices are trending [Up/Down]. However, consider the weather risk: [Mention rain/storm risk if any].

            **Key Factors to Consider**:
            *   [Mention News or External Factors if any]
            *   [Mention specific weather risk]
            
            **Conclusion**: The choice depends on your risk appetite.
            
            Example Output:
            Hello {user_name}, here is the analysis for your Tomato in Madanapalle:
            
            **Current Status**:
            *   **Market Price**: ₹2500/Quintal (Trend: Rising)
            *   **Weather**: Clear skies for next 3 days.

            **Possibilities**:
            1.  **If you Sell Now**: You secure ₹2500 immediately. Safe and guaranteed.
            2.  **If you Wait**: Prices might reach ₹2700 in 2 days. Since weather is clear, the risk is low.

            **Key Factors to Consider**:
            *   News reports high demand in neighboring districts.
            *   No rain predicted, so storage is less risky.
            
            **Conclusion**: Waiting could be profitable, but selling now guarantees returns.
            """
            
            try:
                # Pass synthesis_prompt as system_instruction to override default persona
                final_advice = await self._generate_llm_response(
                    query=f"Help me decide about my {quantity} of {crop} in {location}.",
                    context=context, 
                    language=lang_name,
                    system_instruction=synthesis_prompt
                )
            except Exception as e:
                logger.error(f"Failed to generate advice: {e}")
                final_advice = "I have gathered the weather and market data for you, but I am unable to generate a detailed recommendation right now. Please check the data above."
                if lang_name == "Telugu":
                    final_advice = "నేను మీ కోసం వాతావరణం మరియు మార్కెట్ వివరాలను సేకరించాను, కానీ సలహాను రూపొందించలేకపోయాను. దయచేసి పైన ఉన్న వివరాలను చూడండి."
                elif lang_name == "Hindi":
                    final_advice = "मैंने आपके लिए मौसम और बाजार का डेटा इकट्ठा किया है, लेकिन मैं अभी सलाह नहीं दे पा रहा हूँ। कृपया ऊपर दिए गए डेटा की जांच करें।"

            # Merge Decision Data with News
            response_data = decision.dict()
            response_data["news"] = news_items
            response_data["weather_raw"] = weather_data # For debugging
            response_data["crop"] = crop
            response_data["location"] = location

            return {
                "intent": "decision_support",
                "data": response_data,
                "response": final_advice
            }

        elif intent == "market_price":
            if crop and location:
                # Call the tool directly
                tool_result = await market_tool.run(crop, location)
                # Generate natural language response
                nl_response = await self._generate_llm_response(
                    f"""
                    The current market price data for {crop} in {location} is:
                    {tool_result}
                    
                    Task: Tell this to the user in {lang_name}.
                    Constraints:
                    1. Use ONLY the prices mentioned in the data. Do NOT invent new prices.
                    2. Prices are in Rupees (₹) per Quintal. Do NOT use Dollars ($) or Pounds.
                    3. If data shows 'N/A' or is missing, say you don't have the data.
                    4. Keep it brief (2 sentences).
                    """, 
                    "", 
                    lang_name
                )
                
                # Fallback if LLM failed
                if "technical issue" in nl_response or "సాంకేతిక సమస్య" in nl_response or "तकनीकी समस्या" in nl_response or "offline" in nl_response or "అందుబాటులో లేదు" in nl_response or "उपलब्ध नहीं" in nl_response:
                    nl_response = tool_result
                
                return {
                    "intent": "market_price",
                    "data": tool_result,
                    "response": nl_response
                }
            else:
                 error_msg = "Please specify the crop and location."
                 if lang_name == "Telugu": error_msg = "దయచేసి పంట మరియు ప్రాంతం పేరు చెప్పండి."
                 elif lang_name == "Hindi": error_msg = "कृपया फसल और स्थान का नाम बताएं।"
                 
                 return {
                    "intent": "market_price",
                    "error": "Missing crop or location",
                    "response": error_msg
                }
        
        elif intent == "weather":
            if location:
                 tool_result = await weather_tool.run(location)
                 nl_response = await self._generate_llm_response(
                    f"""
                    The current weather data for {location} is:
                    {tool_result}
                    
                    Task: Tell this to the user in {lang_name}.
                    Constraints:
                    1. Use ONLY the provided weather data.
                    2. Keep units as Celsius (°C).
                    3. Mention rain risk if present.
                    """, 
                    "", 
                    lang_name
                )
                 
                 # Fallback if LLM failed
                 if "technical issue" in nl_response or "సాంకేతిక సమస్య" in nl_response or "तकनीकी समस्या" in nl_response or "offline" in nl_response or "అందుబాటులో లేదు" in nl_response or "उपलब्ध नहीं" in nl_response:
                    nl_response = tool_result
                 
                 return {
                    "intent": "weather",
                    "data": tool_result,
                    "response": nl_response
                 }
            else:
                 error_msg = "Please specify the location for weather."
                 if lang_name == "Telugu": error_msg = "దయచేసి వాతావరణం కోసం ప్రాంతం పేరు చెప్పండి."
                 elif lang_name == "Hindi": error_msg = "कृपया मौसम के लिए स्थान का नाम बताएं।"
                 
                 return {
                    "intent": "weather",
                    "error": "Missing location",
                    "response": error_msg
                 }

        elif intent == "news":
            # Use extracted entities for better relevance
            news_response = await news_service.get_news(
                crop=crop, 
                region=location, 
                language=language_code,
                limit=3
            )
            news_items = news_response.get("articles", [])
            
            if news_items:
                # Format news for the user
                news_text = "Here are the latest agriculture news updates:\n"
                for i, item in enumerate(news_items, 1):
                    news_text += f"{i}. {item['title']} ({item['source']})\n"
                
                # Generate a summary in the requested language
                prompt = f"""
                Task:
                1. Translate the provided agricultural news headlines to {lang_name}.
                2. Provide a brief summary of the most important agricultural news in {lang_name}.
                3. Focus on news about farming, government schemes, crop prices, and weather alerts.
                4. Ensure the response is natural, grammatically correct, and helpful for a farmer.
                5. Format as a numbered list.
                6. Ignore non-agricultural news content if present.
                """
                
                news_system_prompt = f"""
                You are a helpful agricultural news translator and summarizer.
                Your task is to translate and summarize agricultural news headlines into {lang_name}.
                Prioritize news about:
                - Government schemes and announcements
                - Market prices and crop rates
                - Weather warnings
                - Farming advice
                Ensure the translations are accurate and easy to understand for a farmer.
                Do NOT provide advice, just report the news.
                """
                
                nl_response = await self._generate_llm_response(
                    prompt,
                    news_text,
                    lang_name,
                    system_instruction=news_system_prompt
                )
                
                # Fallback if LLM failed - just show the list
                if "technical issue" in nl_response or "సాంకేతిక సమస్య" in nl_response or "तकनीकी समस्या" in nl_response or "offline" in nl_response or "అందుబాటులో లేదు" in nl_response or "उपलब्ध नहीं" in nl_response:
                     if lang_name == "Telugu":
                          nl_response = "వ్యవసాయ వార్తలు:\n" + "\n".join([f"{i+1}. {item['title']}" for i, item in enumerate(news_items[:3])])
                     elif lang_name == "Hindi":
                          nl_response = "कृषि समाचार:\n" + "\n".join([f"{i+1}. {item['title']}" for i, item in enumerate(news_items[:3])])
                     else:
                          nl_response = news_text
                
                return {
                    "intent": "news",
                    "data": news_items,
                    "response": nl_response
                }
            else:
                error_msg = "Sorry, I couldn't fetch the latest news right now."
                if lang_name == "Telugu": error_msg = "క్షమించండి, ప్రస్తుతం వార్తలు అందుబాటులో లేవు."
                elif lang_name == "Hindi": error_msg = "क्षमा करें, अभी समाचार उपलब्ध नहीं हैं।"
                
                return {
                    "intent": "news",
                    "error": "No news found",
                    "response": error_msg
                }

        elif intent == "greeting":
            greeting = "Namaste! How can I help you with your farming today?"
            if lang_name == "Telugu": greeting = "నమస్కారం! మీ వ్యవసాయ పనుల్లో నేను ఎలా సహాయపడగలను?"
            elif lang_name == "Hindi": greeting = "नमस्ते! मैं आपकी खेती में कैसे मदद कर सकता हूँ?"
            
            return {
                "intent": "greeting",
                "response": greeting
            }
        
        elif intent == "unknown":
            unknown_msg = "I am not sure I understand. Could you please ask about crops, prices, or weather?"
            if lang_name == "Telugu": unknown_msg = "క్షమించండి, నాకు అర్థం కాలేదు. దయచేసి పంటలు, ధరలు లేదా వాతావరణం గురించి అడగండి."
            elif lang_name == "Hindi": unknown_msg = "क्षमा करें, मुझे समझ नहीं आया। कृपया फसलों, कीमतों या मौसम के बारे में पूछें।"
            
            return {
                "intent": "unknown",
                "response": unknown_msg
            }

        elif intent == "general_chat":
             # Use LLM directly for general chat
             nl_response = await self.generate_response(text, context=None, language=language_code)
             return {
                 "intent": "general_chat",
                 "response": nl_response
             }

        else: # harvest_advice or fallback
            return {
                "intent": "harvest_advice",
                "query": text
            }

    async def generate_response(self, prompt: str, context: Optional[Union[str, List[Dict[str, str]]]] = None, language: str = "en-IN", system_instruction: str = None, profile: Optional[Dict] = None) -> str:
        """
        Generate a natural language response using RAG + LLM.
        """
        # Retrieve RAG Context (Lazy Init)
        rag_context = ""
        try:
            if not self.rag_service:
                from app.services.rag_service import RAGService
                self.rag_service = RAGService()
                
                # Check if we need to ingest the provided knowledge base
                kb_path = os.path.join(os.getcwd(), "knowledge_base")
                # If persist dir is empty or doesn't exist, ingest
                if not os.path.exists(self.rag_service.persist_directory) or not os.listdir(self.rag_service.persist_directory):
                     logger.info("RAG: Knowledge Base not indexed. Triggering initial ingestion...")
                     if os.path.exists(kb_path):
                         self.rag_service.ingest_documents(kb_path)
                     else:
                         logger.warning(f"RAG: Knowledge Base path not found: {kb_path}")

            # Query RAG
            rag_context = self.rag_service.query(prompt)
            if rag_context:
                logger.info(f"RAG: Retrieved context for query '{prompt}'")
        except Exception as e:
            logger.warning(f"RAG Error: {e}")

        context_str = ""
        
        if rag_context:
            context_str += f"Relevant Knowledge Base Information:\n{rag_context}\n\n"
        
        if context:
            if isinstance(context, list):
                # Format chat history
                context_str += "Recent Conversation History:\n"
                for msg in context[-10:]: # Keep last 10 messages for better context
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if role == 'user':
                        context_str += f"Farmer: {content}\n"
                    elif role == 'assistant':
                        context_str += f"Krishi: {content}\n"
            elif isinstance(context, str):
                context_str += context
        
        # Add Profile Context
        if profile:
            name = profile.get('name', 'Farmer')
            crop = profile.get('primary_crop', 'crops')
            location = profile.get('location', 'your area')
            context_str += f"\nUser Profile:\nName: {name}\nLocation: {location}\nPrimary Crop: {crop}\n"
            
            # Update system instruction to be personalized if not already set
            if not system_instruction:
                system_instruction = f"You are Krishi, a helpful agricultural assistant for {name} in {location}. Always address the user by name. Provide specific advice for {crop}. CRITICAL: Do NOT mention other crops (like Cotton) unless the user explicitly asks about them. Stick to {crop}."


        return await self._generate_llm_response(prompt, context_str, language, system_instruction=system_instruction)

    async def translate_news_items(self, items: list, language: str) -> list:
        """
        Translate a list of news items (title + summary) to the target language using the LLM.
        """
        if not items or language.startswith("en"):
            return items

        try:
            logger.info(f"Translating {len(items)} news items to {language}...")
            
            # Prepare context for translation
            items_text = ""
            for i, item in enumerate(items[:5]):  # Limit to top 5 for performance
                items_text += f"Item {i+1}:\nTitle: {item.get('title', '')}\nSummary: {item.get('description', '') or item.get('summary', '')}\n\n"

            lang_name = "Telugu" if "te" in language else "Hindi" if "hi" in language else "English"
            
            prompt = f"""
            You are a professional translator. Translate the following agricultural news to {lang_name}.
            Keep the meaning accurate but use simple, clear language suitable for farmers.
            
            Format your response exactly like this for each item:
            Item 1:
            Title: [The translated title in {lang_name}]
            Summary: [The translated summary in {lang_name}]
            
            Item 2:
            ...
            
            News to translate:
            {items_text}
            """

            response = await self._generate_llm_response(
                prompt, 
                "", 
                language, 
                system_instruction=f"You are a helpful translator. Translate strictly to {lang_name}.",
                timeout=90  # Increased timeout for batch translation
            )
            
            # Parse the response
            translated_items = [item.copy() for item in items] # Deep copy to avoid modifying original if parsing fails
            current_item_index = 0 # Assume starting with first item
            state = "expect_title" # expect_title, expect_summary
            
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Check for Item header (Item 1, Item 2, etc.)
                # Also handle if it translated "Item" to something else but kept the number
                # Regex looking for a number at the start or after "Item"
                item_match = re.search(r'^(?:Item|అంశం|News)?\s*(\d+)[:.]?', line, re.IGNORECASE)
                if item_match:
                    try:
                        idx = int(item_match.group(1)) - 1
                        if 0 <= idx < len(translated_items):
                            current_item_index = idx
                            state = "expect_title"
                            continue
                    except:
                        pass
                
                # Heuristic: If line contains "Title:" or similar keywords, force state
                if re.match(r'^(Title|శీర్షిక|నివేదిక)[:\s-]', line, re.IGNORECASE):
                    state = "expect_title"
                elif re.match(r'^(Summary|వివరణ|సారాంశం|సూచ్యం)[:\s-]', line, re.IGNORECASE):
                    state = "expect_summary"

                if state == "expect_title" and 0 <= current_item_index < len(translated_items):
                    # Clean up prefix
                    cleaned = re.sub(r'^(Title|శీర్షిక|నివేదిక|Item \d+|.*?News \d+)[:\s-]*', '', line, flags=re.IGNORECASE).strip()
                    if cleaned:
                        translated_items[current_item_index]["title"] = cleaned
                        state = "expect_summary"
                
                elif state == "expect_summary" and 0 <= current_item_index < len(translated_items):
                    # Clean up prefix
                    cleaned = re.sub(r'^(Summary|వివరణ|సారాంశం|సూచ్యం)[:\s-]*', '', line, flags=re.IGNORECASE).strip()
                    if cleaned:
                        translated_items[current_item_index]["description"] = cleaned
                        translated_items[current_item_index]["summary"] = cleaned
                        # After summary, we might expect next item or done
                        # Don't change state immediately to allow multi-line summary (simple concat)
                        # But here we just overwrite, so we assume single line summary for now.
                        state = "waiting_next"

            logger.info(f"Successfully translated items to {lang_name}")
            return translated_items

        except Exception as e:
            logger.error(f"Translation Error: {e}")
            return items

    async def _determine_intent_and_params(self, text: str, rule_based_data: Dict[str, str]) -> Dict[str, str]:
        """
        Uses LLM to determine intent and extract parameters.
        This acts as a 'Router' or 'MCP Host' that selects the right tool.
        """
        import time
        try:
            if not self._ollama_available and time.time() < self._ollama_down_until_ts:
                raise RuntimeError("Ollama in cooldown")
            # We construct a prompt that forces the LLM to choose a tool
            prompt = f"""
            You are an AI assistant for farmers. Your job is to classify the user's intent and extract entities.
            
            Available Tools/Intents:
            1. decision_support: User asks for help making a decision about harvesting, selling, or planting. Requires 'crop', 'location', and 'quantity'. (Keywords: should I sell, when to harvest, profit).
            2. market_price: User asks for crop prices (keywords: price, cost, rate, daralu). Needs 'crop' and 'location'.
            3. weather: User asks about rain, temperature, or forecast (keywords: rain, weather, varsham). Needs 'location'.
            4. news: User asks for agriculture news, updates, or headlines.
            5. harvest_advice: User asks about growing, planting, diseases, fertilizers, or specific farming techniques.
            6. general_chat: User greets, asks "how are you", "who are you", or general questions not specific to farming techniques.
            7. unknown: ONLY if the input is completely gibberish or malicious. If unsure, default to "general_chat".

            User Input: "{text}"
            
            Context (Rule-based extraction):
            - Crop: {rule_based_data.get('crop')}
            - Location: {rule_based_data.get('location')}
            
            Return ONLY a JSON object with the following format (no other text):
            {{
                "intent": "decision_support" | "market_price" | "weather" | "news" | "harvest_advice" | "general_chat" | "unknown",
                "crop": "extracted crop name or null",
                "location": "extracted location name or null",
                "quantity": "extracted quantity (e.g., 10 tons, 5 acres) or null"
            }}
            """
            
            payload = {
                "model": self.llm_model,
                "prompt": prompt,
                "stream": False,
                "format": "json" # Force JSON mode if supported by Ollama/model
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(self.ollama_url, json=payload, timeout=10)
            )
            
            if response.status_code == 200:
                json_str = response.json().get("response", "").strip()
                logger.info(f"Raw LLM Intent Response: {json_str}")
                
                # Clean up potential markdown code blocks
                
                # Use regex to find the first '{' and last '}'
                match = re.search(r'(\{.*\})', json_str, re.DOTALL)
                if match:
                    json_str = match.group(1)
                
                try:
                    data = json.loads(json_str)
                    
                    # Double check intent - if unknown but text has keywords, force advice
                    if data.get("intent") == "unknown":
                        text_lower = text.lower()
                        keywords = ["crop", "plant", "grow", "price", "weather", "rain", "disease", "fertilizer", "water", "soil"]
                        if any(k in text_lower for k in keywords):
                            logger.info("Overriding 'unknown' intent to 'harvest_advice' based on keywords")
                            data["intent"] = "harvest_advice"
                        else:
                            # Default to general chat for unknown non-farming queries
                            data["intent"] = "general_chat"
                            
                    return data
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse LLM intent JSON: {json_str}")
                    # Try to fix common JSON errors or just fallback
                    return {"intent": "general_chat"} 
            else:
                logger.error(f"Ollama Intent Error: {response.status_code}")
                return {"intent": "general_chat"}
                
        except Exception as e:
            logger.error(f"Intent Determination Error: {e}")
            # Trip circuit breaker on connection issues
            self._ollama_available = False
            self._ollama_down_until_ts = time.time() + 300
            
            # Fallback: Rule-based intent determination
            text_lower = text.lower()
            
            # 1. Market Price
            if any(k in text_lower for k in ["price", "cost", "rate", "daralu", "viluva", "dhara", "ధర", "విలువ"]):
                return {
                    "intent": "market_price",
                    "crop": rule_based_data.get("crop"),
                    "location": rule_based_data.get("location")
                }
            
            # 2. Weather
            if any(k in text_lower for k in ["weather", "rain", "temperature", "climate", "varsham", "yenda", "వర్షం", "ఎండ", "వాతావరణం"]):
                return {
                    "intent": "weather",
                    "location": rule_based_data.get("location")
                }
                
            # 3. News
            if any(k in text_lower for k in ["news", "update", "headline", "samacharam", "varthalu", "వార్తలు", "సమాచారం"]):
                return {"intent": "news"}
                
            # 4. Greeting/General Chat
            if any(k in text_lower for k in ["hi", "hello", "namaste", "vanakkam", "who", "how", "నమస్కారం"]):
                return {"intent": "general_chat"}

            return {"intent": "general_chat"}

    async def _generate_llm_response(self, query: str, context: str, language: str = "en", system_instruction: str = None, timeout: int = 30) -> str:
        """
        Generate a response using the local LLM (Qwen 2.5).
        
        Args:
            query: The user's query
            context: Context from RAG or conversation history
            language: Target language for the response
            system_instruction: Optional system instruction override
            
        Returns:
            Generated response string
        """
        import time
        try:
            if not self._ollama_available and time.time() < self._ollama_down_until_ts:
                raise RuntimeError("Ollama in cooldown")
            # Map language to full name for the prompt
            lang_map = {
                "en": "English",
                "en-IN": "English", 
                "te": "Telugu", 
                "te-IN": "Telugu",
                "hi": "Hindi",
                "hi-IN": "Hindi"
            }
            lang_name = lang_map.get(language, "English")
            
            # Construct the prompt with Few-Shot Examples for better quality
            
            # Base system prompt with strict language enforcement
            if system_instruction and system_instruction.strip().startswith("You are"):
                 # Override persona but keep language enforcement
                 base_system_prompt = f"""{system_instruction}

CRITICAL INSTRUCTION: You must answer ONLY in {lang_name}.
Do NOT answer in Chinese. Do NOT answer in English (unless requested).
If the user speaks {lang_name}, you MUST reply in {lang_name}.
Do not use Chinese characters.

Guidelines:
        1. Answer ONLY in {lang_name}.
        2. Keep answers concise.
        3. Do NOT repeat yourself.
        4. DO NOT CORRECT GEOGRAPHY OR POLITICS. If the user says "Hyderabad Telangana", accept it. Do not lecture about state capitals.
        """
            else:
                base_system_prompt = f"""You are Krishi, a friendly and helpful AI Co-pilot for farmers in India. 
Your goal is to assist farmers with agriculture, weather, market prices, and general farming advice.

CRITICAL INSTRUCTION: You must answer ONLY in {lang_name}.
Do NOT answer in Chinese. Do NOT answer in English (unless requested).
If the user speaks {lang_name}, you MUST reply in {lang_name}.
Do not use Chinese characters.

Guidelines:
        1. Answer ONLY in {lang_name}.
        2. Be encouraging, respectful, and clear.
        3. If the user asks a general question (e.g., "How are you?"), answer naturally in {lang_name}.
        4. If the user asks about farming, provide actionable advice in {lang_name}.
        5. Keep answers concise (2-4 sentences).
        6. Do NOT repeat yourself or output gibberish.
        7. DO NOT CORRECT GEOGRAPHY OR POLITICS. If the user says "Hyderabad Telangana", accept it. Do not lecture about state capitals.
        """

            # Add Few-Shot Examples based on language
            if lang_name == "Telugu":
                base_system_prompt += """
Examples:
User: బాగున్నారా? (How are you?)
Assistant: నేను బాగున్నాను! రైతు సోదరా, నేను మీకు ఎలా సహాయపడగలను? (I am fine! Farmer brother, how can I help you?)

User: టమాటా ధర ఎంత? (Tomato price?)
Assistant: ప్రస్తుతం మదనపల్లె మార్కెట్‌లో టమాటా ధర కిలోకు రూ. 20 నుండి రూ. 30 వరకు ఉంది. (Currently tomato price in Madanapalle is Rs 20-30.)
"""
            elif lang_name == "Hindi":
                base_system_prompt += """
Examples:
User: कैसे हो? (How are you?)
Assistant: मैं ठीक हूँ! किसान भाई, मैं आपकी कैसे मदद कर सकता हूँ? (I am fine! Farmer brother, how can I help you?)

User: टमाटर का भाव क्या है? (Tomato price?)
Assistant: वर्तमान में मंडी में टमाटर का भाव 20 से 30 रुपये प्रति किलो है। (Currently tomato price in Mandi is Rs 20-30.)
"""

            # Handle system_instruction override or append
            if system_instruction:
                if system_instruction.strip().startswith("You are") or system_instruction.strip().startswith("మీరు") or system_instruction.strip().startswith("आप"):
                    # Complete override if it looks like a full persona definition
                    base_system_prompt = system_instruction
                    # Ensure critical instruction is preserved even in override
                    if "DO NOT CORRECT GEOGRAPHY" not in base_system_prompt:
                         base_system_prompt += "\n\nCRITICAL: DO NOT CORRECT GEOGRAPHY OR POLITICS. If the user says 'Hyderabad Telangana', accept it."
                else:
                    # Append if it looks like just additional instructions
                    base_system_prompt += f"\n\nAdditional Instruction: {system_instruction}"

            if context:
                user_prompt = f"Context information:\n{context}\n\nUser Question: {query}\n\nAnswer in {lang_name}:"
            else:
                user_prompt = f"User Question: {query}\n\nAnswer in {lang_name}:"

            # Log the prompt for debugging
            logger.info(f"LLM Prompt (Lang: {lang_name}): {user_prompt[:100]}...")

            # Call Ollama API
            # We use the generate endpoint for flexibility
            payload = {
                "model": self.llm_model,
                "prompt": user_prompt,
                "system": base_system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2, # Lower temperature for more deterministic/focused output
                    "num_predict": 256, # Limit output length
                    "repeat_penalty": 1.4, # Stronger penalty for repetition
                    "stop": ["User:", "Context:", "System:", "Chinese:", "你好", "Assistant:", "Examples:"] # Stop tokens
                }
            }
            
            # Run in thread pool to avoid blocking event loop
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(self.ollama_url, json=payload, timeout=timeout)
            )
            response.raise_for_status()
            result = response.json()
            
            response_text = result.get("response", "").strip()
            
            # Fallback if empty or Chinese or Gibberish (repetition)
            if not response_text or any(u'\u4e00' <= c <= u'\u9fff' for c in response_text):
                logger.warning(f"LLM returned empty or Chinese text. Fallback to rule-based.")
                if language.startswith("te"):
                    return "నమస్కారం, నేను వ్యవసాయ సహాయకుడిని. దయచేసి మళ్ళీ అడగండి."
                elif language.startswith("hi"):
                    return "नमस्ते, मैं कृषि सहायक हूँ। कृपया फिर से पूछें।"
                else:
                    return "Hello, I am Krishi Assistant. Please ask again."
            
            # Check for repetition (gibberish detector)
            is_gibberish = False
            
            # 1. Simple start repetition
            if len(response_text) > 50 and response_text[:20] == response_text[20:40]:
                    logger.warning(f"LLM returned repetitive text (Start). Fallback.")
                    is_gibberish = True
            # 2. Loop detection (e.g. "abc abc abc")
            elif len(response_text) > 100:
                # Check compression ratio - repetitive text compresses highly
                import zlib
                compressed = zlib.compress(response_text.encode('utf-8'))
                ratio = len(compressed) / len(response_text.encode('utf-8'))
                # Increased threshold to catch more subtle repetition loops
                if ratio < 0.25: 
                    logger.warning(f"LLM returned repetitive text (Compression Ratio: {ratio}). Fallback.")
                    is_gibberish = True
                else:
                    is_gibberish = False
            
            # 3. Telugu/Hindi specific gibberish check (English words in non-English output)
            if not is_gibberish and (language.startswith("te") or language.startswith("hi")):
                # Check for repeated small tokens (like "Na, Na, Na" or "Ra, Ra, Ra")
                if re.search(r'(.{1,5}[,.\s]+)\1{4,}', response_text):
                    logger.warning(f"LLM returned repetitive short tokens. Fallback.")
                    is_gibberish = True
                
                # If more than 70% of words are English (and text is long enough), it's likely a language mismatch
                words = response_text.split()
                if len(words) > 8:
                    english_word_count = sum(1 for w in words if re.match(r'^[a-zA-Z]+$', w))
                    if english_word_count / len(words) > 0.7:
                        logger.warning(f"LLM returned too much English ({english_word_count}/{len(words)}) in {language} response. Fallback.")
                        is_gibberish = True

            # 4. Check for unprofessional/weird responses (e.g. "Hahaha", "lol")
            unprofessional_keywords = ["hahaha", "hehehe", "lol", "rofl", "lmao"]
            lower_response = response_text.lower()
            if any(keyword in lower_response for keyword in unprofessional_keywords):
                 logger.warning(f"LLM returned unprofessional text: {response_text}. Fallback.")
                 is_gibberish = True

            if is_gibberish:
                    if language.startswith("te"):
                        return "క్షమించండి, నాకు సరిగ్గా అర్థం కాలేదు. దయచేసి మళ్ళీ అడగండి."
                    elif language.startswith("hi"):
                        return "क्षमा करें, मुझे ठीक से समझ नहीं आया। कृपया फिर से पूछें।"
                    else:
                        return "Sorry, I didn't understand. Please ask again."
                
            return response_text

        except Exception as e:
            logger.error(f"LLM Generation Error: {e}")
            # Trip circuit breaker on connection issues
            self._ollama_available = False
            self._ollama_down_until_ts = time.time() + 300
            # Fallback messages
            if language.startswith("te"):
                return "క్షమించండి, సాంకేతిక సమస్య ఉంది."
            elif language.startswith("hi"):
                return "क्षमा करें, कोई तकनीकी समस्या है।"
            return "I apologize, I'm having trouble thinking right now."

    async def generate_response_stream(self, query: str, context: Optional[Union[str, List[Dict[str, str]]]] = None, language: str = "en-IN", profile: Optional[Dict] = None):
        import time
        try:
            if not self._ollama_available and time.time() < self._ollama_down_until_ts:
                raise RuntimeError("Ollama in cooldown")
            lang_name = language
            if language == "te-IN": lang_name = "Telugu"
            elif language == "hi-IN": lang_name = "Hindi"
            elif language == "en-IN": lang_name = "English"
            
            system_prompt = f"""
            You are Krishi, a friendly AI Co-pilot for farmers.
            CRITICAL: Answer ONLY in {lang_name}. Do NOT use Chinese.
            """
            
            # Inject Profile
            if profile:
                 user_name = profile.get("name", "Farmer")
                 location = profile.get("location", "")
                 crop = profile.get("primary_crop", "")
                 system_prompt += f"\nUser Profile: Name={user_name}, Location={location}, Crop={crop}."
            
            ctx = ""
            if context:
                if isinstance(context, list):
                    for msg in context[-10:]:
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        if role == 'user':
                            ctx += f"Farmer: {content}\n"
                        elif role == 'assistant':
                            ctx += f"Krishi: {content}\n"
                elif isinstance(context, str):
                    ctx = context
                    
            prompt = f"""
            Context:
            {ctx}
            
            User Question: {query}
            
            Instruction: Answer ONLY in {lang_name}. Do NOT generate Chinese text.
            Response ({lang_name}):
            """
            
            payload = {
                "model": self.llm_model,
                "prompt": system_prompt + "\n" + prompt,
                "stream": True
            }
            loop = asyncio.get_running_loop()
            q: asyncio.Queue = asyncio.Queue()
            def run_req():
                try:
                    r = requests.post(self.ollama_url, json=payload, stream=True, timeout=60)
                    for line in r.iter_lines():
                        if not line:
                            continue
                        try:
                            obj = json.loads(line.decode("utf-8"))
                        except Exception:
                            continue
                        chunk = obj.get("response", "")
                        done = obj.get("done", False)
                        if chunk:
                            asyncio.run_coroutine_threadsafe(q.put(chunk), loop)
                        if done:
                            break
                finally:
                    asyncio.run_coroutine_threadsafe(q.put(None), loop)
            loop.run_in_executor(None, run_req)
            while True:
                item = await q.get()
                if item is None:
                    break
                yield item
        except Exception as e:
            logger.error(f"LLM Stream Error: {e}")
            # Trip circuit breaker
            self._ollama_available = False
            self._ollama_down_until_ts = time.time() + 300
            yield ""
