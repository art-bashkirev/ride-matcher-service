"""NVIDIA AI client service."""

import aiohttp
from typing import Optional

from config.log_setup import get_logger
from config.settings import get_config
from .models import ChatRequest, ChatResponse

logger = get_logger(__name__)


class NvidiaAIClient:
    """NVIDIA AI API client."""
    
    BASE_URL = "https://integrate.api.nvidia.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client with API key."""
        self.config = get_config()
        self.api_key = api_key or self.config.nvidia_ai_api_key
        self._session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key:
            raise ValueError("NVIDIA AI API key is required")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
            logger.debug("Created new aiohttp session for NVIDIA AI")
        return self._session

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Send chat completion request to NVIDIA AI API."""
        logger.info("Sending chat completion request to NVIDIA AI")
        
        session = await self._get_session()
        url = f"{self.BASE_URL}/chat/completions"
        
        try:
            payload = request.model_dump(exclude_none=True)
            logger.debug("Request payload: %s", payload)
            
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                logger.debug("Response data: %s", data)
                
                return ChatResponse(**data)
                
        except aiohttp.ClientError as e:
            logger.error("HTTP error during NVIDIA AI request: %s", e)
            raise
        except Exception as e:
            logger.error("Unexpected error during NVIDIA AI request: %s", e)
            raise

    async def simple_prompt(self, prompt: str) -> str:
        """Send a simple text prompt and get response."""
        logger.info("Sending simple prompt to NVIDIA AI")
        
        request = ChatRequest(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=1.0
        )
        
        response = await self.chat_completion(request)
        
        if response.choices:
            return response.choices[0].message.content
        else:
            logger.warning("No choices in NVIDIA AI response")
            return "No response generated"

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.debug("Closed NVIDIA AI client session")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()