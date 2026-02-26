"""Google Gemini LLM Provider implementation"""
import asyncio
import json
from typing import List, Dict, Any, Optional

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from src.orchestration.llm_providers.base import BaseLLMProvider, LLMResponse


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini API provider implementation.
    
    Supports Gemini Pro, Gemini Pro Vision, and other Gemini models.
    """
    
    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        'gemini-pro': {'prompt': 0.50, 'completion': 1.50},  # Per 1M tokens (legacy)
        'gemini-1.5-pro': {'prompt': 3.50, 'completion': 10.50},  # Per 1M tokens
        'gemini-1.5-flash': {'prompt': 0.075, 'completion': 0.30},  # Per 1M tokens (updated pricing)
        'gemini-2.0-flash': {'prompt': 0.10, 'completion': 0.40},  # Per 1M tokens
    }
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-pro",
        timeout: int = 30,
        max_retries: int = 2
    ):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Google Gemini API key
            model: Model name to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries on failure
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )
        
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize model
        self.client = genai.GenerativeModel(model)
    
    async def complete(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = True
    ) -> LLMResponse:
        """
        Generate completion using Gemini API.
        
        Args:
            prompt: User prompt/query
            conversation_history: Optional conversation history
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: Whether to force JSON response format
            
        Returns:
            LLMResponse with normalized response data
        """
        # Build conversation context
        full_prompt = prompt
        
        if conversation_history:
            # Format conversation history for Gemini
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-5:]  # Last 5 messages
            ])
            full_prompt = f"{history_text}\n\nuser: {prompt}"
        
        # Add JSON instruction if requested
        if json_mode:
            full_prompt = f"{full_prompt}\n\nIMPORTANT: Respond with valid JSON only."
        
        # Configure generation
        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            candidate_count=1
        )
        
        # Call API with retry logic
        for attempt in range(self.max_retries + 1):
            try:
                # Generate content (synchronous call, wrap in async)
                response = await asyncio.to_thread(
                    self.client.generate_content,
                    full_prompt,
                    generation_config=generation_config
                )
                
                # Extract response text
                content = response.text
                
                # Estimate token usage (Gemini doesn't provide exact counts in all cases)
                prompt_tokens = self._estimate_tokens(full_prompt)
                completion_tokens = self._estimate_tokens(content)
                total_tokens = prompt_tokens + completion_tokens
                
                # Calculate cost
                cost = self.estimate_cost(prompt_tokens, completion_tokens)
                
                return LLMResponse(
                    content=content,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
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
                    raise Exception(f"Gemini API error after {self.max_retries} retries: {str(e)}")
    
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Estimate cost for Gemini token usage.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Estimated cost in USD
        """
        # Get pricing for model (default to gemini-pro if not found)
        model_key = self.model
        if model_key not in self.PRICING:
            # Try to match partial model name
            for key in self.PRICING:
                if key in model_key.lower():
                    model_key = key
                    break
            else:
                model_key = 'gemini-pro'  # Default fallback
        
        pricing = self.PRICING[model_key]
        
        # Gemini pricing is per 1M tokens
        prompt_cost = (prompt_tokens / 1_000_000) * pricing['prompt']
        completion_cost = (completion_tokens / 1_000_000) * pricing['completion']
        
        return round(prompt_cost + completion_cost, 6)  # More precision for smaller costs
    
    def get_model_name(self) -> str:
        """Get the Gemini model name being used"""
        return self.model
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Gemini doesn't always provide exact token counts, so we estimate.
        Rough approximation: 1 token ≈ 4 characters for English text.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
