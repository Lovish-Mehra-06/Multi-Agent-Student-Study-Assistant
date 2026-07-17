"""
chunker.py

Responsible for:
1. Splitting Documents into smaller chunks.
2. Preserving metadata.
"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentChunker:
    """Splits Documents into smaller chunks."""

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
    ):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
    def split(self, documents: list[Document]) -> list[Document]:
        """
        Split documents into chunks.

        Returns:
            List of chunked Documents.
        """

        return self.splitter.split_documents(documents)


"""
------------------------------------------------------------------------------------------
--------------------------------------- * Notes * ----------------------------------------
------------------------------------------------------------------------------------------

Phase 3: Chunking
This is probably the most important component in the entire project. 
A bad chunker = bad retrieval = bad answers.
Many people spend weeks tweaking LLMs when the real issue is poor chunking.
-------------------------------------------
What problem are we solving?
Currently we have:
Document (Chapter 1)
        │
        ▼
25 pages
≈ 20,000 characters

If a student asks:
"What is a displacement reaction?"  Should we send all 20,000 characters to the LLM? NO.

Reasons:
Too much irrelevant information
Slower
Higher token cost (for cloud models)
Lower answer quality

Instead, we split it.
What should a chunk look like?
Imagine this chapter:
Chemical Reactions
...
Types of Chemical Reactions
...
Displacement Reaction
...
Double Displacement Reaction
...
Oxidation

We want:

Chunk 1
Chemical Reactions
...
Chunk 2
Types of Chemical Reactions
...
Chunk 3
Displacement Reaction
...

Now when someone asks:
"Explain displacement reaction."
The Retriever only fetches Chunk 3.
------------------------------------------
Why not split every 1000 characters?
Suppose:
A displacement reaction is one in which
------ SPLIT -----
a more reactive element replaces...
Oops.
The definition got split in half.
That's bad.
Recursive Character Text Splitter
Instead of blindly cutting every 1000 characters, it tries:
Paragraph
↓
Sentence
↓
Word
↓
Character
It only cuts when necessary.
That's why it's one of the most commonly used splitters in LangChain.
----------------------------------------------
What is Chunk Overlap?
Example without overlap:
Chunk 1
Displacement reaction is one in which...
Chunk 2
...a more reactive element replaces...
The definition is split.

With overlap:

Chunk 1
Displacement reaction is one in which...

Chunk 2
one in which...
a more reactive element replaces...

Now both chunks contain the connecting sentence.
Retrieval quality improves.
----------------------------------------------
Choosing Chunk Size
Many tutorials say:
chunk_size = 1000
without explanation.

For textbooks, I recommend starting with:
chunk_size = 800
chunk_overlap = 150

Later we can experiment with:
500, 800, 1000 and compare retrieval quality.
------------------------------------------------------------------------------------------
Expected Output
Documents : 13
Chunks    : 320   (approximately)

Metadata should still contain:
{
    'class': '10',
    'subject': 'Science',
    'chapter_number': 1,
    'pages': 18,
    'source': 'jesc101.pdf',
    'file_path': '...'
}

This is important: LangChain automatically preserves metadata when it splits a Document. 
That means every chunk still knows which class, subject, and chapter it came from.
------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
"""
