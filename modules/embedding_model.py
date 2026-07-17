"""
embedding_model.py

Responsible for:
1. Loading the embedding model.
2. Creating embeddings for documents.
3. Creating embeddings for user queries.
"""

from typing import Any

import numpy as np
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """Generates embeddings using Sentence Transformers."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-base-en-v1.5",
    ) -> None:
        """
        Initialize the embedding model.w

        Args:
            model_name: Hugging Face model name.
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_documents(
        self,
        documents: list[Document],
    ) -> np.ndarray:
        """
        Generate embeddings for a list of documents.

        Args:
            documents: List of LangChain Documents.

        Returns:
            NumPy array of document embeddings.
        """

        texts: list[str] = [document.page_content for document in documents]

        embeddings: np.ndarray = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        return embeddings

    def embed_query(
        self,
        query: str,
    ) -> np.ndarray:
        """
        Generate an embedding for a user query.

        Args:
            query: User question.

        Returns:
            NumPy array representing the query embedding.
        """

        embedding: np.ndarray = self.model.encode(
            query,
            convert_to_numpy=True,
        )

        return embedding
