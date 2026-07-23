"""
llm_client.py

Responsible for:
1. Connecting to Groq.
2. Sending prompts to the LLM.
3. Returning generated responses.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI


class LLMClient:
    """Client for interacting with Groq models."""

    def __init__(
        self,
        # model: str = "llama-3.3-70b-versatile",
        model: str = "llama-3.1-8b-instant",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> None:
        """
        Initialize the Groq client.
        """

        load_dotenv()

        api_key = os.getenv("GROQ_API_KEY")

        if api_key is None:
            raise ValueError("GROQ_API_KEY not found in .env file.")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(
        self,
        prompt: str,
        system_prompt: str = (
            "You are a helpful AI tutor that answers ONLY using the provided context."
        ),
    ) -> str:
        """
        Generate a response from the LLM.
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
