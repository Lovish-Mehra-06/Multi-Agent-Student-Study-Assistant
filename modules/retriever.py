"""
retriever.py

Responsible for:
1. Loading the vector database.
2. Searching for relevant documents.
3. Returning the most relevant chunks.
"""

from langchain_core.documents import Document

from modules.vector_store import VectorStore


class Retriever:
    """Retrieves relevant documents from the vector database."""

    def __init__(
        self,
        vector_store: VectorStore,
        k: int = 5,
    ) -> None:
        """
        Initialize the retriever.

        Args:
            vector_store: Loaded VectorStore object.
            k: Number of documents to retrieve.
        """

        if vector_store.db is None:
            raise ValueError("Vector database is not loaded.")

        self.retriever = vector_store.db.as_retriever(search_kwargs={"k": k})

    def search(
        self,
        query: str,
    ) -> list[Document]:
        """
        Retrieve the most relevant documents.

        Args:
            query: User question.

        Returns:
            List of relevant LangChain Documents.
        """

        documents = self.retriever.invoke(query)

        return documents
