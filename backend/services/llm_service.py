import json
import logging
import asyncio
from openai import OpenAI
from config import get_settings

logger = logging.getLogger("llm_service")


class LLMService:
    """Cerebras LLM service wrapper (Llama 3.3 70B via OpenAI-compatible API)."""

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(
            base_url="https://api.cerebras.ai/v1",
            api_key=settings.CEREBRAS_API_KEY,
        )
        self.model = "llama-3.3-70b"

    async def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """Generate text content."""
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
                top_p=1,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise

    async def generate_json(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.2,
        max_tokens: int = 8192,
    ) -> dict:
        """Generate structured JSON output."""
        system = system_instruction or ""
        system += "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no code blocks, no explanation. Just the raw JSON object or array."

        response = await self.generate(
            prompt,
            system_instruction=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Clean response — strip markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}\nResponse: {cleaned[:500]}")
            raise ValueError(f"LLM returned invalid JSON: {e}")


# Singleton
_llm_service = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
