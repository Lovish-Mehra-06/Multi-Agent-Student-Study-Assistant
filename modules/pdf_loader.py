"""
pdf_loader.py

Responsible for:
1. Validating a PDF.
2. Extracting text.
3. Cleaning extracted text.
4. Extracting basic metadata.
5. Returning a LangChain Document.
"""

from pathlib import Path
import re

import fitz
from langchain_core.documents import Document

from typing import cast


class PDFLoader:
    """Loads a single PDF and returns a LangChain Document."""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path).resolve()

    def _validate_pdf(self) -> None:
        """
        Validate that the PDF exists.
        """

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        """

        text = re.sub(r"\n{2,}", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    def _extract_text(self) -> tuple[str, int]:
        """
        Extract text and page count from the PDF.

        Returns:
            tuple[str, int]:
                Clean text and number of pages.
        """

        text_parts: list[str] = []

        with fitz.open(self.pdf_path) as pdf:

            page_count = len(pdf)

            for page in pdf:
                text = cast(str, page.get_text("text"))
                text_parts.append(text)

        full_text = "\n".join(text_parts)

        full_text = self._clean_text(full_text)

        return full_text, page_count

    def _extract_metadata(self, page_count: int) -> dict:
        """
        Extract metadata for the document.
        """

        metadata = {
            "source": self.pdf_path.name,
            "file_path": str(self.pdf_path),
            "pages": page_count,
            "chapter_number": self._extract_chapter_number(),
        }

        return metadata

    def _extract_chapter_number(self) -> int | None:
        """
        Extract chapter number from the PDF filename.

        Example:
            jesc101.pdf -> 1
            jesc113.pdf -> 13

        ---
        Why this regex?
            Filename: jesc101
            self.pdf_path.stem removes .pdf:
            jesc101

            Regex:  r"(\\ d{3})$"   means:
            \\ d{3} → exactly three digits
            $ → at the end of the filename

            So it extracts:
            101

            Then:
            chapter_code[1:]
            takes:  01 and
            int("01")  --becomes:--> 1

            Similarly:113 --becomes:--> 13
        """

        match = re.search(r"(\d{3})$", self.pdf_path.stem)

        if not match:
            return None

        chapter_code = match.group(1)

        return int(chapter_code[1:])

    def load(self) -> Document:
        """
        Load the PDF and return a LangChain Document.
        """

        self._validate_pdf()

        text, page_count = self._extract_text()

        metadata = self._extract_metadata(page_count)

        return Document(
            page_content=text,
            metadata=metadata,
        )


"""
------------------------------------------------------------------------------------------
------------------------------------ ** Extra Notes ** -----------------------------------
------------------------------------------------------------------------------------------
Understand why LangChain has a `Document` class.
Imagine we only return text:
text = "Chemical reactions are..."

Later, the user asks:
"From which chapter did this answer come?"
You can't answer.

Now imagine this:
Document(
    page_content="Chemical reactions are...",
    metadata={
        "class": "10",
        "subject": "Science",
        "chapter": "Chemical Reactions and Equations",
        "source": "01_Chemical_Reactions_and_Equations.pdf"
    }
)
Now the retriever can return:
Source: Class 10 Science → Chapter 1 → Chemical Reactions and Equations
This is one of the reasons RAG systems are trusted—they can point back to the source.
------------------------------------------------------------------------------------------
Question: Why langchain_core instead of langchain?
Because the Document class now lives in the core package.
It's lightweight and doesn't pull in unnecessary dependencies.
------------------------------------------------------------------------------------------
Why did we use Path instead of a string for the PDF path?
Instead of:
pdf_path = "abc.pdf"
we use:
from pathlib import Path
self.pdf_path = Path(pdf_path)

Path makes working with files much easier:
self.pdf_path.name

returns
jesc101.pdf

while
self.pdf_path.parent
returns
Science

We'll use these features later to extract metadata.
------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
"""
