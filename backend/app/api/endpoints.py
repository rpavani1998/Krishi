from fastapi import APIRouter, HTTPException, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import logging
import os
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.models.harvest import HarvestInput, HarvestDecision
from app.services.ceda_service import ceda_service
from app.services.weather_service import weather_service
from app.services.decision_service import decision_service
from app.services.news_service import news_service
from app.services.onboarding_service import get_onboarding_service

# Import both services
from app.services.aws_service import aws_service
from app.services.local_ai_service import LocalAIService

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

def _to_wav_bytes_if_possible(audio_bytes: bytes, filename: Optional[str]) -> bytes:
    if not audio_bytes:
        return audio_bytes
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        return audio_bytes
    suffix = ""
    if filename:
        try:
            suffix = Path(filename).suffix or ""
        except Exception:
            suffix = ""
    in_path = None
    out_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix or ".bin", delete=False) as f_in:
            f_in.write(audio_bytes)
            in_path = f_in.name
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f_out:
            out_path = f_out.name
        cmd = [
            ffmpeg_path,
            "-y",
            "-i", in_path,
            "-ac", "1",
            "-ar", "16000",
            "-f", "wav",
            out_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        with open(out_path, "rb") as f:
            return f.read()
    except Exception:
        return audio_bytes
    finally:
        for p in (in_path, out_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

# CONFIGURATION: Choose AI Provider
# Force Local AI Service for debugging
logger.info("Using Local Open Source AI Service")
ai_service = LocalAIService()

# --- Endpoint Models ---
class ChatRequest(BaseModel):
    message: str
    language: str = "en"

class TextInteractionRequest(BaseModel):
    text: str
    language: str = "en"
    context: Optional[dict] = None

class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    voice_settings: Optional[dict] = None

class OnboardingRequest(BaseModel):
    """Request for onboarding flow."""
    user_input: str
    session_state: Optional[dict] = None
    language: str = "en"

# --- Endpoints ---

@router.post("/voice/speak")
async def text_to_speech(request: TTSRequest, background_tasks: BackgroundTasks):
    """
    Generate audio for the given text using local TTS.
    Returns an audio file.
    """
    try:
        if hasattr(ai_service, 'generate_audio'):
            # Pass voice_settings if available
            audio_path = await ai_service.generate_audio(
                request.text, 
                request.language, 
                voice_settings=request.voice_settings
            )
            
            if audio_path and os.path.exists(audio_path):
                # Schedule cleanup of temp file after response is sent
                background_tasks.add_task(os.remove, audio_path)
                return FileResponse(audio_path, media_type="audio/mpeg", filename="response.mp3")
            else:
                 raise HTTPException(status_code=500, detail="Failed to generate audio")
        else:
             raise HTTPException(status_code=501, detail="TTS not supported by current AI provider")
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice/interact_text")
async def voice_interaction_text(request: TextInteractionRequest):
    """
    Handle text-based interaction: Extract Intent (AI) -> Return Text & Data
    """
    logger.info(f"DEBUG: voice_interaction_text called with text='{request.text}' language='{request.language}'")
    try:
        # 1. Map language code
        lang_code = request.language
        if request.language == "te": lang_code = "te-IN"
        elif request.language == "hi": lang_code = "hi-IN"
        elif request.language == "en": lang_code = "en-IN"
        
        transcript = request.text
        
        # 2. Extract Intent & Entities
        user_profile = None
        if request.context and "profile" in request.context:
            user_profile = request.context["profile"]
            logger.info(f"DEBUG: Received Profile in Text Interaction: {user_profile}")
        else:
            logger.warning("DEBUG: No Profile found in Text Interaction context")
        
        chat_context = None
        if request.context and "history" in request.context:
            chat_context = request.context["history"]
        
        # Pass profile to analyze_intent
        extracted_data = await ai_service.analyze_intent(transcript, lang_code, profile=user_profile, history=chat_context)
        logger.info(f"DEBUG: Analyzed Intent Result: {extracted_data}")
        
        intent = extracted_data.get("intent", "decision_support")
        
        # 3. Determine AI Response Text
        response_text = ""
        
        if extracted_data.get("response"):
             response_text = extracted_data["response"]
        elif extracted_data.get("tool_response"):
             response_text = extracted_data["tool_response"]
        elif extracted_data.get("rag_context"):
             response_text = extracted_data["rag_context"]
        else:
             # Fallback to general generation if no specific response
             response_text = await ai_service.generate_response(transcript, context=chat_context, language=lang_code, profile=user_profile)

        return {
            "response_text": response_text,
            "transcript": transcript,
            "intent": intent,
            "data": extracted_data,
            "profile": user_profile 
        }

    except Exception as e:
        logger.error(f"Voice Text Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voice/interact_text_stream")
async def voice_interaction_text_stream(text: str, language: str = "en", profile: Optional[str] = None):
    try:
        lang_code = language
        if language == "te": lang_code = "te-IN"
        elif language == "hi": lang_code = "hi-IN"
        elif language == "en": lang_code = "en-IN"
        
        user_profile = None
        if profile:
            try:
                user_profile = json.loads(profile)
                logger.info(f"DEBUG: Received Profile in Stream: {user_profile}")
            except Exception as e:
                logger.warning(f"Failed to parse profile in stream: {e}")

        intent_data = await ai_service.analyze_intent(text, lang_code, profile=user_profile)
        intent = intent_data.get("intent", "general_chat")
        data_payload = intent_data.get("data")
        
        # Log the received intent for debugging
        logger.info(f"INTENT_DEBUG: Received intent: {intent} for text: '{text}'")

        
        # Determine intent for routing
        # Stricter check for harvest advice to avoid false positives
        harvest_keywords = ["harvest", "sell", "market", "price", "crop", "when should i sell", "mandi"]
        is_harvest_advice = intent == "harvest_advice" and any(keyword in text.lower() for keyword in harvest_keywords)

        is_general_knowledge = intent == "general_knowledge"

        async def gen():
            # Send metadata as a standard data event first so JS parser picks it up
            # JS ignores 'event: meta', so we use standard data event
            meta_obj = {'intent': intent}
            if data_payload:
                meta_obj['data'] = jsonable_encoder(data_payload)
            
            yield f"data: {json.dumps(meta_obj)}\n\n"

            if is_harvest_advice and user_profile:
                try:
                    # 1. Construct HarvestInput
                    harvest_input = HarvestInput(
                        crop=user_profile.get("primary_crop", "Unknown"),
                        quantity=100,  # Placeholder
                        harvest_date=date.today(),
                        location=user_profile.get("location", "Unknown"),
                        latitude=user_profile.get("latitude", 13.55),
                        longitude=user_profile.get("longitude", 78.50),
                        storage_condition="open" # Placeholder
                    )

                    # 2. Get Market Prices
                    prices = await ceda_service.get_market_prices(
                        commodity=harvest_input.crop,
                        state="Andhra Pradesh",
                        district=harvest_input.location
                    )

                    # 3. Get Weather Forecast
                    weather = await weather_service.get_forecast(harvest_input.latitude, harvest_input.longitude)

                    # 4. Generate Decision
                    decision = decision_service.evaluate(harvest_input, prices, weather, language=language)
                    
                    # 5. Generate recommendation text
                    recommendation_text = decision_service.generate_recommendation_text(decision, language)
                    decision.recommendation_text = recommendation_text

                    # 6. Stream decision
                    yield f"data: {json.dumps({'decision': jsonable_encoder(decision)})}\n\n"

                except Exception as e:
                    logger.error(f"Error generating harvest decision: {e}")
                    yield f"data: {json.dumps({'text': 'Sorry, I could not get the harvest advice.'})}\n\n"
            
            elif is_general_knowledge:
                # Route to RAG service for general questions
                if not ai_service.rag_service:
                    from app.services.rag_service import RAGService
                    ai_service.rag_service = RAGService()
                
                query = text # Use the original text as the query
                if data_payload and data_payload.get('query'):
                    query = data_payload.get('query')
                
                rag_response = await ai_service.rag_service.query(query)
                yield f"data: {json.dumps({'text': rag_response})}\n\n"

            elif hasattr(ai_service, "generate_response_stream"):
                async for chunk in ai_service.generate_response_stream(text, None, lang_code, profile=user_profile):
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
            else:
                resp = await ai_service.generate_response(text, context=None, language=lang_code, profile=user_profile)
                yield f"data: {json.dumps({'text': resp})}\n\n"
            yield "event: done\ndata: {}\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"SSE Voice Text Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice/interact")
async def voice_interaction(
    file: UploadFile = File(...),
    language: str = Form("en"),
    pre_transcribed_text: Optional[str] = Form(None),
    profile: Optional[str] = Form(None),
    history: Optional[str] = Form(None)
):
    """
    Handle voice interaction: Transcribe -> Extract Intent (AI) -> Return Text & Data
    """
    try:
        # 2. Map language code
        lang_code = "en-IN"
        lang_input = language.lower()
        if "te" in lang_input: lang_code = "te-IN"
        elif "hi" in lang_input: lang_code = "hi-IN"
        
        # Parse Profile and History
        user_profile = None
        if profile:
            try:
                import json
                user_profile = json.loads(profile)
                logger.info(f"DEBUG: Received Profile: {user_profile}")
            except Exception as e:
                logger.warning(f"Failed to parse profile JSON: {e}")
        
        chat_history = None
        if history:
            try:
                import json
                chat_history = json.loads(history)
            except Exception as e:
                logger.warning(f"Failed to parse history JSON: {e}")
        
        transcript = ""

        
        # Optimization: Use browser transcript if available and valid (longer than 2 chars)
        # BUT prefer backend transcription for non-English to ensure accuracy if enabled
        if pre_transcribed_text and len(pre_transcribed_text) > 2 and "en" in lang_code:
             logger.info(f"Using pre-transcribed text: {pre_transcribed_text}")
             transcript = pre_transcribed_text
        else:
             # 1. Read audio file
             audio_bytes = await file.read()
             audio_bytes = _to_wav_bytes_if_possible(audio_bytes, getattr(file, "filename", None))
             
             # 2. Transcribe (Backend Whisper)
             # Even if pre_transcribed_text exists, we might override it if it looks weak
             backend_transcript = await ai_service.transcribe_audio(audio_bytes, lang_code)
             
             if backend_transcript and "Error" not in backend_transcript:
                 transcript = backend_transcript
             elif pre_transcribed_text and len(pre_transcribed_text) > 2:
                 # Fallback to browser text if backend failed
                 logger.warning("Backend transcription failed, falling back to browser text")
                 transcript = pre_transcribed_text
             else:
                 transcript = ""
        
        if not transcript or "Error" in transcript:
            msg = "Could not understand audio. Please try again."
            if lang_code.startswith("te"): 
                msg = "క్షమించండి, మీ మాటలు వినపడలేదు. దయచేసి మళ్ళీ చెప్పండి."
            elif lang_code.startswith("hi"): 
                msg = "क्षमा करें, आपकी आवाज़ सुनाई नहीं दी। कृपया फिर से बोलें।"

            return {
                "response_text": msg, 
                "transcript": "(No Speech Detected)", 
                "intent": "unknown", 
                "data": None
            }

        # 4. Extract Intent & Entities (Abstracted)
        extracted_data = await ai_service.analyze_intent(transcript, lang_code, profile=user_profile, history=chat_history)
        
        intent = extracted_data.get("intent", "harvest_advice")
        
        # Determine AI Response Text
        response_text = "నేను సహాయం చేయలేకపోతున్నాను." # Telugu default
        
        if extracted_data.get("response"):
             response_text = extracted_data["response"]
        elif extracted_data.get("tool_response"):
             response_text = extracted_data["tool_response"]
        elif extracted_data.get("rag_context"):
             response_text = extracted_data["rag_context"]
        elif intent == "harvest_advice" or intent == "general_chat":
             # If it's advice or general chat, generate a full response using the LLM
             response_text = await ai_service.generate_response(transcript, context=chat_history, language=lang_code, profile=user_profile)

        return {
            "response_text": response_text,
            "transcript": transcript, # Original user input
            "intent": intent,
            "data": extracted_data
        }

    except Exception as e:
        logger.error(f"Voice Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/onboarding/interact_audio")
async def onboarding_interact_audio(
    file: UploadFile = File(...),
    language: str = Form("en"),
    session_state: Optional[str] = Form(None)
):
    try:
        onboarding = get_onboarding_service(
            ai_service=ai_service,
            weather_service=weather_service,
            price_service=ceda_service,
            news_service=news_service,
            decision_service=decision_service
        )

        decoded_state = None
        if session_state:
            try:
                decoded_state = json.loads(session_state)
            except Exception as e:
                logger.error(f"Failed to decode session_state: {e}. Raw: {session_state[:100]}...")
                decoded_state = None

        if not decoded_state:
            logger.warning("No valid session_state found. Resetting to initial state.")
            decoded_state = onboarding.get_initial_state()

        lang_code = "en-IN"
        lang_input = (language or "en").lower()
        if "te" in lang_input:
            lang_code = "te-IN"
        elif "hi" in lang_input:
            lang_code = "hi-IN"

        audio_bytes = await file.read()
        audio_bytes = _to_wav_bytes_if_possible(audio_bytes, getattr(file, "filename", None))
        transcript = await ai_service.transcribe_audio(audio_bytes, lang_code)
        if not transcript or "Error" in transcript:
            msg = "Could not understand audio. Please try again."
            if lang_code.startswith("te"):
                msg = "క్షమించండి, మీ మాటలు వినపడలేదు. దయచేసి మళ్ళీ చెప్పండి."
            elif lang_code.startswith("hi"):
                msg = "क्षमा करें, आपकी आवाज़ सुनाई नहीं दी। कृपया फिर से बोलें।"

            return {
                "success": False,
                "transcript": "(No Speech Detected)",
                "next_prompt": msg,
                "session_state": decoded_state,
                "completed": False,
                "profile": decoded_state.get("profile"),
                "scenario": None
            }

        result = await onboarding.process_input(
            user_input=transcript,
            session_state=decoded_state,
            language=language
        )

        return {
            "success": True,
            "transcript": transcript,
            "session_state": result,
            "next_prompt": result.get("next_prompt"),
            "completed": result.get("completed", False),
            "profile": result.get("profile"),
            "scenario": result.get("scenario")
        }
    except Exception as e:
        logger.error(f"Onboarding audio error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/query")
async def chat_query(request: ChatRequest):
    """
    Text-based chat using RAG (if available)
    """
    try:
        lang_code = "en-IN"
        if request.language == "te": lang_code = "te-IN"
        if request.language == "hi": lang_code = "hi-IN"
        
        response = await ai_service.generate_response(request.message, language=lang_code)
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/harvest/decision", response_model=HarvestDecision)
async def get_harvest_decision(data: HarvestInput):
    # 1. Get Market Prices (CEDA)
    prices = await ceda_service.get_market_prices(
        commodity=data.crop,
        state="Andhra Pradesh", # Hardcoded for prototype
        district=data.location,
        date_filter=data.harvest_date
    )
    
    # 2. Get Weather Forecast
    weather = await weather_service.get_forecast(data.latitude, data.longitude)
    
    # 3. Generate Decision
    decision = decision_service.evaluate(data, prices, weather)
    
    return decision

@router.get("/rag/ingest")
async def ingest_knowledge_base():
    """
    Trigger ingestion of documents for RAG (Local only)
    """
    if AI_PROVIDER != "LOCAL":
        return {"message": "RAG ingestion only available in LOCAL mode"}
        
    try:
        # Access the internal RAG service directly for admin task
        if hasattr(ai_service, 'rag_service'):
            # Lazy init
            if not ai_service.rag_service:
                from app.services.rag_service import RAGService
                ai_service.rag_service = RAGService()
                
            kb_path = os.path.join(os.getcwd(), "knowledge_base")
            ai_service.rag_service.ingest_documents(kb_path)
            return {"message": "Ingestion started/completed."}
        else:
            return {"message": "Current AI Service does not support RAG ingestion."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market/news")
async def get_market_news():
    """
    Get latest market news from knowledge base
    """
    try:
        news_path = os.path.join(os.getcwd(), "knowledge_base", "market_news.txt")
        if os.path.exists(news_path):
            with open(news_path, "r") as f:
                content = f.read()
            return {"content": content}
        return {"content": "No market news available at the moment."}
    except Exception as e:
        logger.error(f"Error reading news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather/forecast")
async def get_weather_forecast(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location: Optional[str] = None
):
    """
    Get weather forecast for given coordinates or location using Open-Meteo.
    If location name is provided, it will be geocoded first.
    """
    try:
        # Geocode if location provided and coordinates are missing
        if location and (latitude is None or longitude is None):
            coords = await weather_service.get_coordinates(location)
            if coords:
                latitude = coords["latitude"]
                longitude = coords["longitude"]
            else:
                 logger.warning(f"Geocoding failed for {location}, falling back to default")

        # Default fallback if nothing provided (Madanapalle, AP)
        if latitude is None or longitude is None:
             latitude = 13.55
             longitude = 78.50

        data = await weather_service.get_forecast(latitude, longitude)
        
        # Add location info to response
        if location:
            data["location_name"] = location
            
        return data
    except Exception as e:
        logger.error(f"Error fetching weather forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news")
async def get_news(
    language: str = "en",
    category: str = "agriculture",
    limit: int = 10,
    crop: Optional[str] = None,
    region: Optional[str] = None
):
    """
    Get latest agricultural news from news service
    """
    try:
        from app.services.news_service import news_service
        
        # Fetch news articles
        news_data = await news_service.get_news(
            crop=crop,
            region=region,
            language=language,
            limit=limit
        )
        
        articles = news_data.get("articles", [])
        
        # Translate articles if language is not English and AI service supports it
        # User requested to disable translation and rely on API's native language support
        # if not language.startswith("en") and hasattr(ai_service, 'translate_news_items'):
        #      try:
        #          articles = await ai_service.translate_news_items(articles, language)
        #      except Exception as e:
        #          logger.error(f"Failed to translate news items: {e}")
        
        # Return in the format expected by frontend
        return {
            "articles": articles,
            "count": news_data.get("total", 0),
            "data_source": news_data.get("data_source", "unknown")
        }
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        # Return empty list on error
        return {
            "articles": [],
            "count": 0,
            "data_source": "error",
            "error": str(e)
        }

@router.get("/market/prices")
async def get_market_prices(
    commodity: str = "Tomato",
    state: str = "Andhra Pradesh",
    district: str = "Krishna",
    language: str = "en"
):
    """
    Get current market prices for a commodity from CEDA service
    """
    try:
        from datetime import date
        
        # Fetch prices from CEDA service
        prices = await ceda_service.get_market_prices(
            commodity=commodity,
            state=state,
            district=district,
            date_filter=date.today()
        )
        
        return prices
    except Exception as e:
        logger.error(f"Error fetching market prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "ok"}


# --- Onboarding Endpoint ---

@router.post("/onboarding/process")
async def process_onboarding(request: OnboardingRequest):
    """
    Process onboarding conversation flow.
    
    This endpoint handles the voice-based farmer onboarding:
    1. Collects farmer profile (name, location, crop, farm size)
    2. Generates decision scenario based on weather, news, and mandi rates
    
    Args:
        request: OnboardingRequest with user input and session state
        
    Returns:
        Updated session state with next prompt or final scenario
    """
    try:
        # Get onboarding service
        onboarding = get_onboarding_service(
            ai_service=ai_service,
            weather_service=weather_service,
            price_service=ceda_service,
            news_service=news_service,
            decision_service=decision_service
        )
        
        # Initialize session state if not provided
        if not request.session_state:
            session_state = onboarding.get_initial_state()
        else:
            session_state = request.session_state
        
        # Process user input
        result = await onboarding.process_input(
            user_input=request.user_input,
            session_state=session_state,
            language=request.language
        )
        
        logger.info(f"Onboarding step completed: completed={result.get('completed')}")
        
        return {
            "success": True,
            "session_state": result,
            "next_prompt": result.get('next_prompt'),
            "completed": result.get('completed', False),
            "profile": result.get('profile'),
            "scenario": result.get('scenario')
        }
        
    except Exception as e:
        logger.error(f"Onboarding error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


import httpx

@router.get("/onboarding/start")
async def start_onboarding(
    language: str = "en",
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
):
    """
    Start a new onboarding session.
    
    Args:
        language: User's preferred language (en, te, hi)
        latitude: User's latitude (optional)
        longitude: User's longitude (optional)
        
    Returns:
        Initial session state with greeting prompt
    """
    try:
        # Get onboarding service
        onboarding = get_onboarding_service(
            ai_service=ai_service,
            weather_service=weather_service,
            price_service=ceda_service,
            news_service=news_service,
            decision_service=decision_service
        )
        
        # Get initial state
        session_state = onboarding.get_initial_state()
        
        # Handle Location Detection
        if latitude and longitude:
            try:
                # Simple Reverse Geocoding via Nominatim
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        "https://nominatim.openstreetmap.org/reverse",
                        params={"lat": latitude, "lon": longitude, "format": "json"},
                        headers={"User-Agent": "KrishiApp/1.0"},
                        timeout=5.0
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        address = data.get("address", {})
                        # Extract most relevant location name
                        city = address.get("city") or address.get("town") or address.get("village") or address.get("county") or address.get("district")
                        
                        if city:
                            logger.info(f"Detected location: {city}")
                            session_state['profile']['suggested_location'] = city
            except Exception as e:
                logger.error(f"Reverse geocoding failed: {e}")
        
        # Get initial greeting (Deterministic - Data Collection Focus)
        if language == 'te':
            greeting = "నమస్కారం! మీ కోసం సరైన సలహాలు ఇవ్వడానికి, నాకు మీ గురించి కొన్ని వివరాలు కావాలి. మీ పేరు ఏమిటి?"
        elif language == 'hi':
            greeting = "नमस्ते! आपको सही सलाह देने के लिए, मुझे आपके बारे में कुछ जानकारी चाहिए। आपका नाम क्या है?"
        else:
            greeting = "Hi! To give you the best agricultural advice, I need a few details. Let's start with your name."

        # Add greeting to conversation history
        session_state['conversation_history'].append({
            'role': 'assistant',
            'content': greeting
        })
        
        return {
            "success": True,
            "session_state": session_state,
            "greeting": greeting
        }
        
    except Exception as e:
        logger.error(f"Start onboarding error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
