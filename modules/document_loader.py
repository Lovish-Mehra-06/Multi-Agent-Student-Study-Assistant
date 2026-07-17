"""
document_loader.py

Responsible for:
1. Loading all PDFs from a folder.
2. Calling PDFLoader for each PDF.
3. Enriching metadata (class & subject).
4. Returning a list of Documents.
"""

from pathlib import Path
from typing import List

from langchain_core.documents import Document

from modules.pdf_loader import PDFLoader


class DocumentLoader:
    """Loads all PDFs from a directory."""

    def __init__(self, folder_path: str):
        self.folder_path = Path(folder_path).resolve()

    def _validate_folder(self) -> None:
        """Ensure the folder exists."""

        if not self.folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {self.folder_path}")

    def _extract_folder_metadata(self) -> dict:
        """
        Extract metadata from the folder structure.

        Example:
        data/books/Class10/Science/
        """

        return {
            "class": self.folder_path.parent.name.replace("Class", ""),
            "subject": self.folder_path.name,
        }

    def load(self) -> List[Document]:
        """Load every PDF inside the folder."""

        self._validate_folder()

        folder_metadata = self._extract_folder_metadata()

        documents: List[Document] = []

        pdf_files = sorted(self.folder_path.glob("*.pdf"))

        for pdf_file in pdf_files:

            loader = PDFLoader(str(pdf_file))

            document = loader.load()

            document.metadata.update(folder_metadata)

            documents.append(document)

        return documents


"""
-------------------------------  Notes: ------------------------------
Why did I create _extract_folder_metadata()?

Many beginners would write:

document.metadata["class"] = ...
document.metadata["subject"] = ...

inside the loop.

Instead, we calculate the folder metadata once:

folder_metadata = self._extract_folder_metadata()

Then reuse it for every document.

It's a small optimization now, but it also makes the code cleaner and easier to extend."""
