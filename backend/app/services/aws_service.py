
import boto3
import logging
import asyncio
import os
import uuid
import time
import requests
import json
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any, Optional, List, Union

from .ai_service_interface import AIService

logger = logging.getLogger(__name__)

class AWSService(AIService):
    """
    AWS Implementation of AI Service using:
    - Transcribe (Voice)
    - Bedrock (NLU/RAG)
    """
    def __init__(self):
        # Initialize AWS clients
        # In a real scenario, credentials should be in .env or ~/.aws/credentials
        
        self.region = os.getenv("AWS_REGION", "ap-south-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "krishi-audio-uploads")
        self.bedrock_model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
        
        try:
            # Check for credentials implicitly via boto3
            self.transcribe = boto3.client('transcribe', region_name=self.region)
            self.s3 = boto3.client('s3', region_name=self.region)
            self.bedrock = boto3.client('bedrock-runtime', region_name=self.region)
            self.polly = boto3.client('polly', region_name=self.region)
            logger.info("AWS Service initialized successfully")
        except (NoCredentialsError, ClientError) as e:
            logger.warning(f"AWS Credentials not found or invalid: {e}. Using MOCK mode.")
            self.transcribe = None
            self.s3 = None
            self.bedrock = None
            self.polly = None
        except Exception as e:
            logger.error(f"Failed to initialize AWS Service: {e}")
            self.transcribe = None
            self.s3 = None
            self.bedrock = None
            self.polly = None

    async def transcribe_audio(self, audio_bytes, language_code='te-IN') -> str:
        """
        Orchestrate upload and transcription.
        If AWS is not configured, fallback to mock.
        """
        if not self.transcribe or not self.s3:
            return await self.mock_transcribe(audio_bytes, language_code)

        try:
            # 1. Upload to S3
            file_key = f"uploads/{uuid.uuid4()}.wav"
            self.s3.put_object(Body=audio_bytes, Bucket=self.bucket_name, Key=file_key)
            file_uri = f"s3://{self.bucket_name}/{file_key}"
            
            # 2. Start Transcription Job
            job_name = f"krishi-transcribe-{uuid.uuid4()}"
            
            self.transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': file_uri},
                MediaFormat='wav',
                LanguageCode=language_code,
                Settings={'ShowSpeakerLabels': False}
            )
            
            # 3. Poll for completion (Simple loop for MVP)
            max_tries = 60
            while max_tries > 0:
                await asyncio.sleep(1)
                status = self.transcribe.get_transcription_job(TranscriptionJobName=job_name)
                job_status = status['TranscriptionJob']['TranscriptionJobStatus']
                
                if job_status in ['COMPLETED', 'FAILED']:
                    break
                max_tries -= 1
            
            if job_status == 'COMPLETED':
                transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                response = requests.get(transcript_uri)
                data = response.json()
                transcript_text = data['results']['transcripts'][0]['transcript']
                
                # Cleanup (Optional)
                # self.s3.delete_object(Bucket=self.bucket_name, Key=file_key)
                
                return transcript_text
            else:
                logger.error(f"Transcription Job Failed: {status}")
                return await self.mock_transcribe(audio_bytes, language_code)

        except Exception as e:
            logger.error(f"AWS Transcribe Process Error: {e}")
            return await self.mock_transcribe(audio_bytes, language_code)

    async def analyze_intent(self, text: str, language_code: str = 'en-IN', target_field: Optional[str] = None, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Use Amazon Bedrock (Claude 3 Sonnet) to analyze intent and extract entities.
        """
        # Pass profile to Bedrock logic if needed, for now just updating signature
        return await self.analyze_intent_with_bedrock(text, language_code, target_field, profile=profile)

    async def generate_response(self, prompt: str, context: Optional[Union[str, List[Dict[str, str]]]] = None, language: str = "en-IN", system_instruction: str = None, profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a natural language response using Bedrock (Claude 3 Sonnet).
        """
        if not self.bedrock:
            return "AWS Bedrock is not configured. Please check your credentials."

        try:
            # Construct System Prompt
            sys_prompt = system_instruction or "You are a helpful agricultural assistant for Indian farmers."
            
            if language.startswith("te"):
                sys_prompt += " Reply in Telugu."
            elif language.startswith("hi"):
                sys_prompt += " Reply in Hindi."
            else:
                sys_prompt += " Reply in English."

            if profile:
                 sys_prompt += f"\nUser Profile: {json.dumps(profile, ensure_ascii=False)}"

            # Context handling
            context_str = ""
            if context:
                if isinstance(context, list):
                    context_str = "\nConversation History:\n" + "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in context])
                else:
                    context_str = f"\nContext: {context}"

            final_prompt = f"{sys_prompt}\n{context_str}\nUser: {prompt}"

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": final_prompt
                            }
                        ]
                    }
                ]
            })

            response = self.bedrock.invoke_model(
                modelId=self.bedrock_model_id,
                body=body
            )
            
            response_body = json.loads(response.get('body').read())
            response_text = response_body['content'][0]['text']
            return response_text

        except Exception as e:
            logger.error(f"Bedrock Generation Error: {e}. Falling back to Mock.")
            return await self.mock_generate_response(prompt, language, context, profile)

    async def generate_audio(self, text: str, language: str = "en-IN", voice_settings: Optional[dict] = None) -> Optional[str]:
        """
        Generate audio using AWS Polly.
        """
        if not self.polly:
            return None
        
        try:
            # Default to Aditi (Standard) which is robust for Indian context and supports Hindi/English
            voice_id = "Aditi"
            engine = "standard"
            
            # Use Kajal for Neural if explicitly requested or for better quality in Hi/En
            # Kajal (Neural) is available in ap-south-1
            if (language.lower().startswith("en") or language.lower().startswith("hi")) and not "male" in (voice_settings or {}).get("gender", ""):
                 voice_id = "Kajal"
                 engine = "neural"

            # Fallback for male voices or others - Aditi standard is safest
            if "male" in (voice_settings or {}).get("gender", ""):
                # No specific male Indian voice in standard/neural consistently available in all regions
                # Using Aditi as fallback or could use 'Matthew' (US)
                voice_id = "Aditi"
                engine = "standard"

            try:
                response = self.polly.synthesize_speech(
                    Text=text,
                    OutputFormat='mp3',
                    VoiceId=voice_id,
                    Engine=engine
                )
            except Exception as e:
                logger.warning(f"Polly failed with {voice_id} {engine}: {e}. Falling back to Aditi standard.")
                # Fallback to Aditi Standard (safest)
                response = self.polly.synthesize_speech(
                    Text=text,
                    OutputFormat='mp3',
                    VoiceId="Aditi",
                    Engine="standard"
                )
            
            # Save to temp file
            import tempfile
            # Use /tmp for Lambda compatibility
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir="/tmp" if os.path.exists("/tmp") else None) as f:
                f.write(response['AudioStream'].read())
                return f.name
            
        except Exception as e:
            logger.error(f"Polly Error: {e}")
            return None

    async def mock_generate_response(self, prompt, language, context=None, profile=None):
        """
        Robust fallback for when Bedrock fails (e.g. Model not enabled).
        Generates plausible responses based on keywords.
        """
        prompt_lower = prompt.lower()
        
        # 1. Harvest/Sell Advice
        if "harvest" in prompt_lower or "sell" in prompt_lower or "price" in prompt_lower:
            if "te" in language:
                return "ప్రస్తుతం మార్కెట్ ధరలు స్థిరంగా ఉన్నాయి. నా సలహా ప్రకారం, మీరు మీ పంటలో 50% ఇప్పుడు అమ్మి, మిగిలినది వచ్చే వారం అమ్మితే మంచి లాభం రావచ్చు."
            elif "hi" in language:
                return "वर्तमान बाजार भाव स्थिर हैं। मेरी सलाह है कि आप अपनी फसल का 50% अभी बेच दें और बाकी अगले हफ्ते के लिए रोक कर रखें।"
            else:
                return "Current market prices are stable. I recommend selling 50% of your harvest now and storing the rest, as prices might increase next week."

        # 2. Weather
        if "weather" in prompt_lower or "rain" in prompt_lower:
            if "te" in language:
                return "రాబోయే 3 రోజుల్లో వర్షం పడే అవకాశం ఉంది. దయచేసి మీ పంటను సురక్షితంగా ఉంచండి."
            elif "hi" in language:
                return "अगले 3 दिनों में बारिश होने की संभावना है। कृपया अपनी फसल को सुरक्षित रखें।"
            else:
                return "There is a chance of rain in the next 3 days. Please ensure your harvested crop is stored safely."

        # 3. News
        if "news" in prompt_lower or "scheme" in prompt_lower:
             if "te" in language:
                return "ప్రభుత్వం రైతుల కోసం కొత్త బీమా పథకాన్ని ప్రకటించింది. దీనివల్ల పంట నష్టపోతే పరిహారం త్వరగా అందుతుంది."
             elif "hi" in language:
                return "सरकार ने किसानों के लिए नई बीमा योजना की घोषणा की है। इससे फसल नुकसान होने पर मुआवजा जल्दी मिलेगा।"
             else:
                return "The government has announced a new insurance scheme for farmers. This will ensure faster compensation for crop loss."

        # 4. General Greeting/Help
        if "hello" in prompt_lower or "hi" in prompt_lower or "help" in prompt_lower:
             if "te" in language:
                return "నమస్కారం! నేను మీ వ్యవసాయ సహాయకుడిని. పంటలు, ధరలు లేదా వాతావరణం గురించి అడగండి."
             elif "hi" in language:
                return "नमस्ते! मैं आपका कृषि सहायक हूँ। आप मुझसे फसलों, कीमतों या मौसम के बारे में पूछ सकते हैं।"
             else:
                return "Namaste! I am your farming assistant. You can ask me about crops, market prices, or weather."

        # 5. Default Fallback
        if "te" in language:
            return "క్షమించండి, నాకు అర్థం కాలేదు. దయచేసి పంటలు లేదా ధరల గురించి అడగండి."
        elif "hi" in language:
            return "क्षमा करें, मुझे समझ नहीं आया। कृपया फसलों या कीमतों के बारे में पूछें।"
        else:
            return "I'm sorry, I didn't quite catch that. Could you please ask about your crop, market prices, or the weather?"

    async def analyze_intent_with_bedrock(self, transcript, language_code, target_field: Optional[str] = None, profile: Optional[Dict[str, Any]] = None):
        """
        Use Amazon Bedrock (Claude 3 Sonnet) to analyze intent and extract entities.
        """
        if not self.bedrock:
            return await self.mock_bedrock_analysis(transcript)

        try:
            # Construct Prompt for Claude 3 Sonnet
            if target_field:
                prompt = f"""
                You are an agricultural assistant. The user was asked to provide their {target_field}.
                
                User Input: "{transcript}"
                
                Task: Extract the {target_field} from the input.
                - If the input contains the {target_field}, extract it cleanly.
                - **Single-word answers are valid.** (e.g., "Kadapa" -> "Kadapa", "Ramesh" -> "Ramesh")
                - If the input is garbage or irrelevant (e.g. "oh my god", "what"), return null.
                
                Detailed Instructions for {target_field}:
                """
                
                if target_field == 'location':
                    prompt += """
                    - Look for Village, Mandal, District, or City names.
                    - If multiple parts are given (e.g., "Pulivendula Mandal, Kadapa District"), extract the full location string.
                    """
                
                prompt += f"""
                Return ONLY a JSON object with keys: {target_field}.
                """
            else:
                prompt = f"""
                You are an agricultural assistant. Analyze the following user input (which may be in English, Telugu, or Hindi) and extract structured data.
                
                User Input: "{transcript}"
                
                Return a JSON object with the following fields:
                - intent: "sell_advice" (if asking for advice), "market_price" (if asking for price), "weather" (if asking for weather), or "unknown"
                - crop: Name of the crop (e.g., Tomato, Onion) in English. If not mentioned, null.
                - quantity: Quantity as a number. If not mentioned, null.
                - quantity_unit: Unit (e.g., quintals, kg). If not mentioned, assume "quintals".
                - location: Location/City name in English. If not mentioned, null.
                - harvest_date: Date if mentioned (YYYY-MM-DD), else null.
                
                Only return the JSON object, no other text.
                """

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            })

            response = self.bedrock.invoke_model(
                modelId=self.bedrock_model_id,
                body=body
            )
            
            response_body = json.loads(response.get('body').read())
            response_text = response_body['content'][0]['text']
            
            # Extract JSON from response (in case of extra text)
            try:
                # Find JSON block if wrapped in markdown
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                json_str = response_text[start:end]
                data = json.loads(json_str)
                return data
            except:
                logger.error(f"Failed to parse Bedrock response: {response_text}")
                return await self.mock_bedrock_analysis(transcript)

        except Exception as e:
            logger.error(f"Bedrock Error: {e}")
            return await self.mock_bedrock_analysis(transcript)

    # Fallback/Mock for when AWS keys are missing in Hackathon environment
    async def mock_transcribe(self, audio_bytes, language_code):
        """
        Simulate transcription for demo purposes if AWS keys are invalid
        """
        logger.info(f"Using Mock Transcribe for language: {language_code}")
        await asyncio.sleep(1.5) # Simulate processing delay
        
        # Return hardcoded strings based on language for demo flow
        if language_code.startswith('te'):
            return "నా దగ్గర మదనపల్లెలో 50 క్వింటాళ్ల టమాటా ఉంది, నేను ఇప్పుడే అమ్మాలా?" 
        elif language_code.startswith('hi'):
            return "मेरे पास मदनपल्ली में 50 क्विंटल टमाटर है, क्या मुझे अभी बेचना चाहिए?"
        else:
            return "I have 50 quintals of Tomato in Madanapalle, should I sell now?"

    async def mock_bedrock_analysis(self, transcript):
        """
        Simulate LLM Analysis with better intent classification
        """
        logger.info("Using Mock Bedrock Analysis")
        await asyncio.sleep(0.1)
        
        transcript_lower = transcript.lower()
        
        data = {
            "intent": "general_chat",
            "crop": None,
            "quantity": None,
            "quantity_unit": "quintals",
            "location": None,
            "harvest_date": None
        }
        
        # Intent Rules
        if "weather" in transcript_lower or "rain" in transcript_lower:
            data["intent"] = "weather"
        elif "price" in transcript_lower or "market" in transcript_lower:
            data["intent"] = "market_price"
        elif "sell" in transcript_lower or "harvest" in transcript_lower:
            data["intent"] = "sell_advice"
        elif "news" in transcript_lower or "scheme" in transcript_lower:
            # Assuming news intent exists or falls back to general
            data["intent"] = "general_chat" 

        # Entity Rules
        if "tomato" in transcript_lower or "టమాటా" in transcript_lower or "टमाटर" in transcript_lower:
            data["crop"] = "Tomato"
        elif "onion" in transcript_lower:
            data["crop"] = "Onion"
        elif "banana" in transcript_lower:
            data["crop"] = "Banana"
            
        # Quantity
        import re
        qty_match = re.search(r'(\d+)', transcript_lower)
        if qty_match:
            data["quantity"] = int(qty_match.group(1))
            
        # Location
        if "madanapalle" in transcript_lower or "మదనపల్లె" in transcript_lower:
            data["location"] = "Madanapalle"
        elif "moinabad" in transcript_lower:
             data["location"] = "Moinabad"
        elif "kadapa" in transcript_lower:
             data["location"] = "Kadapa"
             
        return data

aws_service = AWSService()

