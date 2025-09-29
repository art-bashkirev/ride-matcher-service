"""AI models for NVIDIA API integration."""

from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")


class ChatRequest(BaseModel):
    """Chat completion request model."""
    model: str = Field(default="meta/llama-4-maverick-17b-128e-instruct", description="AI model to use")
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    max_tokens: int = Field(default=512, description="Maximum number of tokens to generate")
    temperature: float = Field(default=1.0, description="Sampling temperature")
    top_p: float = Field(default=1.0, description="Top-p sampling parameter")
    frequency_penalty: float = Field(default=0.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, description="Presence penalty")
    stream: bool = Field(default=False, description="Whether to stream the response")


class ChatChoice(BaseModel):
    """Chat completion choice."""
    index: int = Field(..., description="Choice index")
    message: ChatMessage = Field(..., description="Generated message")
    finish_reason: Optional[str] = Field(None, description="Reason for finishing")


class ChatUsage(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total number of tokens")


class ChatResponse(BaseModel):
    """Chat completion response model."""
    id: str = Field(..., description="Response ID")
    object: str = Field(..., description="Object type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: List[ChatChoice] = Field(..., description="List of completion choices")
    usage: Optional[ChatUsage] = Field(None, description="Token usage information")