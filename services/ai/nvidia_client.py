"""NVIDIA AI API client using aiohttp."""

import os
from typing import Optional

import aiohttp

from config.log_setup import get_logger

logger = get_logger(__name__)


class NvidiaAIClient:
    """NVIDIA AI API client for chat completions."""
    
    BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    def __init__(self, api_key: str | None = None, timeout: int = 30):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise RuntimeError("NVIDIA_API_KEY not provided")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def start(self):
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def chat_completion(self, user_message: str) -> str:
        """Send a chat completion request to NVIDIA AI."""
        await self.start()
        if not self._session:
            raise RuntimeError("Client session not initialized and could not be started.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "google/gemma-3-27b-it",
            "messages": [{"role": "user", "content": user_message}],
            "max_tokens": 512,
            "temperature": 1.00,
            "top_p": 1.00,
            "frequency_penalty": 0.00,
            "presence_penalty": 0.00,
            "stream": False
        }
        
        try:
            async with self._session.post(self.BASE_URL, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                
                # Extract response content from API response structure
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
                else:
                    logger.warning("Unexpected response structure from NVIDIA AI API: %s", data)
                    return "I'm sorry, I couldn't process your message."
                    
        except aiohttp.ClientError as e:
            logger.error("HTTP error when calling NVIDIA AI API: %s", e)
            return "I'm sorry, I'm having trouble connecting to the AI service."
        except Exception as e:
            logger.error("Unexpected error when calling NVIDIA AI API: %s", e)
            return "I'm sorry, something went wrong while processing your message."