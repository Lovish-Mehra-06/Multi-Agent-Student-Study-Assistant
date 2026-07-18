"""
vector_store.py

Responsible for:
1. Creating a FAISS vector database.
2. Saving the database.
3. Loading the database.
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


class VectorStore:
    """Creates and manages a FAISS vector database."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-base-en-v1.5",
        index_path: str = "data/vector_store",
    ) -> None:
        """
        Initialize the vector store.

        Args:
            model_name: Hugging Face embedding model.
            index_path: Directory where the FAISS index is stored.
        """

        self.index_path = Path(index_path)

        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)

        self.db: FAISS | None = None

    def build(
        self,
        documents: list[Document],
    ) -> None:
        """
        Build a FAISS index from documents.
        """

        self.db = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings,
        )

    def save(self) -> None:
        """
        Save the FAISS index to disk.
        """

        if self.db is None:
            raise ValueError("Vector database has not been built.")

        self.index_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.db.save_local(str(self.index_path))

    def load(self) -> None:
        """
        Load the FAISS index from disk.
        """

        self.db = FAISS.load_local(
            folder_path=str(self.index_path),
            embeddings=self.embeddings,
            allow_dangerous_deserialization=True,
        )

    def search(
        self,
        query: str,
        k: int = 5,
    ) -> list[Document]:
        """
        Search the vector database.

        Args:
            query:
                User query.

            k:
                Number of documents to retrieve.

        Returns:
            Top-k relevant documents.
        """

        if self.db is None:
            raise ValueError("Vector database has not been loaded.")

        return self.db.similarity_search(
            query=query,
            k=k,
        )
