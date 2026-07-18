"""
csv_writer.py

Responsible for:
1. Saving generated flashcards as CSV.
"""

from pathlib import Path


class CSVWriter:
    """Writes CSV flashcards."""

    def __init__(
        self,
        output_dir: str = "outputs/flashcards",
    ) -> None:

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _sanitize_filename(
        filename: str,
    ) -> str:

        invalid = '<>:"/\\|?*'

        for ch in invalid:
            filename = filename.replace(ch, "")

        return filename.strip().replace(" ", "_")

    def save(
        self,
        topic: str,
        csv_text: str,
    ) -> Path:
        """
        Save flashcards.

        Args:
            topic:
                Chapter/topic.

            csv_text:
                CSV returned by the LLM.

        Returns:
            Saved file path.
        """

        filename = self._sanitize_filename(topic)

        file_path = self.output_dir / f"{filename}.csv"

        file_path.write_text(
            csv_text,
            encoding="utf-8",
        )

        return file_path
