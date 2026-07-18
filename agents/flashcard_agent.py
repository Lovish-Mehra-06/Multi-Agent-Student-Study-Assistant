"""
flashcard_agent.py

Responsible for:
1. Generating flashcards from notes.
2. Producing Question-Answer pairs.
3. Returning structured flashcards.
"""

from modules.llm_client import LLMClient
from modules.csv_writer import CSVWriter


class FlashcardAgent:
    """Generates flashcards from Markdown notes."""

    def __init__(
        self,
        llm: LLMClient,
        writer: CSVWriter,
    ) -> None:
        """
        Initialize the Flashcard Agent.

        Args:
            llm:
                Language model.

            writer:
                CSV writer.
        """

        self.llm = llm
        self.writer = writer

    def build_prompt(
        self,
        notes: str,
    ) -> str:
        """
        Build prompt for flashcard generation.
        """

        return f"""
You are an expert teacher.

Generate high-quality study flashcards from the notes below.

Requirements:

- Return ONLY CSV data.
- Columns:
Question,Answer

- Questions should cover:
  • Definitions
  • Concepts
  • Formulae
  • Important facts
  • One-line revision questions

- Keep answers concise.

Notes:

{notes}
"""

    def run(
        self,
        topic: str,
        notes: str,
    ) -> str:
        """
        Generate flashcards.

        Args:
            topic:
                Chapter/topic name.

            notes:
                Markdown notes.

        Returns:
            CSV file path.
        """

        prompt = self.build_prompt(notes)

        csv_data = self.llm.generate(prompt)

        file_path = self.writer.save(
            topic=topic,
            csv_text=csv_data,
        )

        return str(file_path)