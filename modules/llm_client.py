"""
llm_client.py

Responsible for:
1. Connecting to OpenRouter.
2. Sending prompts to the LLM.
3. Returning generated responses.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI


class LLMClient:
    """Client for interacting with OpenRouter models."""

    def __init__(
        self,
        model: str = "meta-llama/llama-3.1-8b-instruct:free",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> None:
        """
        Initialize the OpenRouter client.

        Args:
            model: OpenRouter model ID.
            temperature: Controls randomness.
            max_tokens: Maximum response length.
        """

        load_dotenv()

        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in .env file.")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(
        self,
        prompt: str,
        system_prompt: str = (
            "You are a helpful AI tutor that answers using only the provided context."
        ),
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: User prompt.
            system_prompt: System instruction.

        Returns:
            Generated response.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return response.choices[0].message.content or ""