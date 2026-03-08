from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union

class AIService(ABC):
    """
    Abstract Base Class for AI Services (Voice & NLU).
    Allows switching between AWS (Cloud) and Open Source (Local) implementations.
    """

    @abstractmethod
    async def transcribe_audio(self, audio_bytes: bytes, language_code: str = 'en-IN') -> str:
        """
        Convert audio bytes to text.
        """
        pass

    @abstractmethod
    async def analyze_intent(self, text: str, language_code: str = 'en-IN', target_field: Optional[str] = None, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extract intent and entities from text.
        
        Args:
            text: The user input text.
            language_code: The language code (e.g., 'en-IN', 'te-IN').
            target_field: Optional field name we are specifically looking for (e.g., 'location', 'name').
                          Helps the LLM focus and filter garbage.
            profile: Optional user profile data to provide context (e.g. name, location).
        """
        pass

    @abstractmethod
    async def generate_response(self, prompt: str, context: Optional[Union[str, List[Dict[str, str]]]] = None, language: str = "en-IN", system_instruction: str = None, profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a natural language response (RAG support).
        """
        pass
