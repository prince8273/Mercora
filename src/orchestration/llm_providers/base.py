"""Base LLM Provider interface"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """
    Normalized LLM response across providers.
    
    Attributes:
        content: Response text content
        prompt_tokens: Number of tokens in prompt
        completion_tokens: Number of tokens in completion
        total_tokens: Total tokens used
        model: Model name used
        cost_usd: Estimated cost in USD
    """
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    cost_usd: float


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers (OpenAI, Gemini, Anthropic, etc.) must implement
    this interface to ensure consistent behavior and easy switching.
    """
    
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = True
    ) -> LLMResponse:
        """
        Generate completion from LLM.
        
        Args:
            prompt: User prompt/query
            conversation_history: Optional conversation history
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            json_mode: Whether to force JSON response format
            
        Returns:
            LLMResponse with normalized response data
            
        Raises:
            Exception: On API errors (should be handled by caller)
        """
        pass
    
    @abstractmethod
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Estimate cost for token usage.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the model name being used.
        
        Returns:
            Model name string
        """
        pass
