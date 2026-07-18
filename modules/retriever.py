"""
retriever_tool.py

Responsible for:
1. Retrieving relevant document chunks
   from the FAISS vector database.
"""

from langchain_core.documents import Document

from modules.vector_store import VectorStore


class RetrieverTool:
    """Shared retrieval tool used by AI agents."""

    def __init__(
        self,
        vector_store: VectorStore,
    ) -> None:

        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        k: int = 5,
    ) -> list[Document]:
        """
        Retrieve relevant documents.

        Args:
            query:
                User question.

            k:
                Number of chunks.

        Returns:
            Retrieved documents.
        """

        return self.vector_store.search(
            query=query,
            k=k,
        )
