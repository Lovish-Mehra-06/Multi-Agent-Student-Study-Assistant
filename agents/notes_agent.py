"""
notes_agent.py

Responsible for:
1. Generating structured study notes.
2. Saving notes as Markdown.
"""

from pathlib import Path
from modules.rag_pipeline import RAGPipeline

NOTES_PROMPT = """ 
You are an expert NCERT teacher.

Using ONLY the provided context, generate well-structured study notes.

Requirements:
- Use Markdown formatting.
- Add clear headings and subheadings.
- Explain concepts in simple language.
- Include important definitions.
- Include important points as bullet lists.
- Include chemical equations or formulas where applicable.
- Do NOT use outside knowledge.
- If information is missing, do not invent it.

Context:
{context}

Topic:
{question}

Generate comprehensive study notes.
"""


class NotesAgent:
    """Generates structured study notes."""

    def __init__(
        self, rag_pipeline: RAGPipeline, output_dir: str = "outputs/notes"
    ) -> None:

        self.rag = rag_pipeline
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_notes(self, topic: str) -> str:
        """
        Generate notes for a topic.

        Args:
            topic: Topic or chapter name.

        Returns:
            Markdown notes.
        """
        notes, documents = self.rag.answer(query=topic, prompt_template=NOTES_PROMPT)
        return notes

    def save_notes(self, topic: str, notes: str) -> Path:
        """
        Save notes to a Markdown file.

        Args:
            topic: Topic or chapter name.
            notes: Markdown notes.

        Returns:
            Path to the saved file.
        """
        filename = topic.lower().replace(" ", "_").replace("/", "_").replace("\\", "_")

        output_path = self.output_dir / f"{filename}.md"

        output_path.write_text(notes, encoding="utf-8")

        return output_path

    def run(self, topic: str) -> Path:
        """
        Generate and save notes.

        Args:
            topic: Topic or chapter name.

        Returns:
            Path to saved notes.
        """
        notes = self.generate_notes(topic)
        return self.save_notes(topic, notes)
