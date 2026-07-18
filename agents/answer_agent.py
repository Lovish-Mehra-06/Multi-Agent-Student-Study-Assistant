"""
answer_agent.py

Responsible for:
1. Answering user questions using retrieved context.
"""

from modules.llm_client import LLMClient


class AnswerAgent:
    """Generates answers from retrieved context."""

    def __init__(
        self,
        llm: LLMClient,
    ) -> None:
        self.llm = llm

    def build_prompt(
        self,
        query: str,
        context: str,
    ) -> str:
        """
        Build the prompt for answering questions.
        """

        return f"""
You are an expert NCERT Science teacher.

Answer ONLY using the provided context.

Rules:
- Do not use outside knowledge.
- If the answer is not present, reply:
"I could not find the answer in the provided textbook."
- Be concise.
- Explain clearly.
- Use bullet points if needed.

Context:
{context}

Question:
{query}

Answer:
"""

    def run(
        self,
        query: str,
        context: str,
    ) -> str:
        """
        Generate an answer.

        Args:
            query: User question.
            context: Retrieved textbook context.

        Returns:
            Generated answer.
        """

        prompt = self.build_prompt(
            query=query,
            context=context,
        )

        return self.llm.generate(prompt)
