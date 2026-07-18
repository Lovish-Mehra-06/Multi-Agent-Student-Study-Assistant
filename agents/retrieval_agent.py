"""
retrieval_agent.py

Responsible for:
1. Retrieving relevant document chunks.
2. Building a single context string.
3. Returning the context and source documents.
"""

from langchain_core.documents import Document

from modules.retriever import RetrieverTool


class RetrievalAgent:
    """Retrieves relevant textbook content."""

    def __init__(
        self,
        retriever: RetrieverTool,
    ) -> None:
        """
        Initialize the Retrieval Agent.

        Args:
            retriever:
                Shared Retriever Tool.
        """

        self.retriever = retriever

    def build_context(
        self,
        documents: list[Document],
    ) -> str:
        """
        Combine retrieved documents into a single context string.

        Args:
            documents:
                Retrieved document chunks.

        Returns:
            Combined context.
        """

        context_parts = []

        for i, document in enumerate(documents, start=1):

            metadata = document.metadata

            source = metadata.get("source", "Unknown")
            chapter = metadata.get("chapter_number", "Unknown")
            subject = metadata.get("subject", "Unknown")

            context_parts.append(f"""
Document {i}

Source: {source}
Subject: {subject}
Chapter: {chapter}

{document.page_content}
""")

        return "\n\n".join(context_parts)

    def run(
        self,
        query: str,
        k: int = 5,
    ) -> tuple[str, list[Document]]:
        """
        Retrieve relevant context.

        Args:
            query:
                User query.

            k:
                Number of chunks.

        Returns:
            Tuple containing:
                - Combined context
                - Retrieved documents
        """

        documents = self.retriever.retrieve(
            query=query,
            k=k,
        )

        context = self.build_context(documents)

        return context, documents
