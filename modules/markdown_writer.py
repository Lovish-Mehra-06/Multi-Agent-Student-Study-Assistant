"""
markdown_writer.py

Responsible for:
1. Saving generated notes as Markdown.
"""

from pathlib import Path


class MarkdownWriter:
    """Writes Markdown content to a file."""

    def __init__(
        self,
        output_dir: str = "outputs/notes",
    ) -> None:
        """
        Initialize the Markdown Writer.

        Args:
            output_dir:
                Directory where Markdown files are saved.
        """

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _sanitize_filename(
        filename: str,
    ) -> str:
        """
        Convert a topic into a safe filename.
        """

        invalid = '<>:"/\\|?*'

        for ch in invalid:
            filename = filename.replace(ch, "")

        filename = filename.strip().replace(" ", "_")

        return filename

    def save(
        self,
        topic: str,
        markdown: str,
    ) -> Path:
        """
        Save Markdown notes.

        Args:
            topic:
                Topic name.

            markdown:
                Markdown content.

        Returns:
            Path of the saved file.
        """

        filename = self._sanitize_filename(topic)

        file_path = self.output_dir / f"{filename}.md"

        file_path.write_text(
            markdown,
            encoding="utf-8",
        )

        return file_path