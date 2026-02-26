"""OpenAI LLM Provider implementation"""
import asyncio
from typing import List, Dict, Any, Optional

from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion

from src.orchestration.llm_providers.base import BaseLLMProvider, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider implementation.
    
    Supports GPT-4, GPT-3.5-turbo, and other OpenAI models.
    """
    
    # Pricing per 1K tokens (as of 2024)
    PRICING = {
        'gpt-4': {'prompt': 0.03, 'completion': 0.06},
        'gpt-4-turbo': {'prompt': 0.01, 'completion': 0.03},
        'gpt-3.5-turbo': {'prompt': 0.0015, 'completion': 0.002},
    }
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        timeout: int = 30,
        max_retries: int = 2
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries on failure
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize async client
        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries
        )
    
    async def complete(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = True
    ) -> LLMResponse:
        """
        Generate completion using OpenAI API.
        
        Args:
            prompt: User prompt/query
            conversation_history: Optional conversation history
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: Whether to force JSON response format
            
        Returns:
            LLMResponse with normalized response data
        """
        # Build messages
        messages = []
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history[-5:])  # Last 5 messages
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request parameters
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add JSON mode if requested
        if json_mode:
            request_params["response_format"] = {"type": "json_object"}
        
        # Call API with retry logic
        for attempt in range(self.max_retries + 1):
            try:
                response: ChatCompletion = await self.client.chat.completions.create(
                    **request_params
                )
                
                # Extract response data
                content = response.choices[0].message.content
                usage = response.usage
                
                # Calculate cost
                cost = self.estimate_cost(
                    usage.prompt_tokens,
                    usage.completion_tokens
                )
                
                return LLMResponse(
                    content=content,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    model=self.model,
                    cost_usd=cost
                )
                
            except Exception as e:
                if attempt < self.max_retries:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    # Final attempt failed
                    raise Exception(f"OpenAI API error after {self.max_retries} retries: {str(e)}")
    
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Estimate cost for OpenAI token usage.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Estimated cost in USD
        """
        # Get pricing for model (default to gpt-4 if not found)
        model_key = self.model
        if model_key not in self.PRICING:
            # Try to match partial model name
            for key in self.PRICING:
                if key in model_key.lower():
                    model_key = key
                    break
            else:
                model_key = 'gpt-4'  # Default fallback
        
        pricing = self.PRICING[model_key]
        
        prompt_cost = (prompt_tokens / 1000) * pricing['prompt']
        completion_cost = (completion_tokens / 1000) * pricing['completion']
        
        return round(prompt_cost + completion_cost, 4)
    
    def get_model_name(self) -> str:
        """Get the OpenAI model name being used"""
        return self.model
