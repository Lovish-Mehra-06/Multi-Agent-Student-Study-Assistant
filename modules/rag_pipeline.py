"""
rag_pipeline.py

Responsible for:
1. Retrieving relevant documents.
2. Building a context from retrieved chunks.
3. Sending the context to the LLM.
4. Returning the generated answer along with source documents.
"""

from langchain_core.documents import Document

from modules.llm_client import LLMClient
from modules.retriever import Retriever


class RAGPipeline:
    """Handles the Retrieval-Augmented Generation (RAG) workflow."""

    def __init__(
        self,
        retriever: Retriever,
        llm: LLMClient,
    ) -> None:
        """
        Initialize the RAG pipeline.

        Args:
            retriever: Retriever object.
            llm: LLM client.
        """

        self.retriever = retriever
        self.llm = llm

    def retrieve(
        self,
        query: str,
    ) -> list[Document]:
        """
        Retrieve relevant documents.

        Args:
            query: User question.

        Returns:
            List of retrieved documents.
        """

        return self.retriever.search(query)

    def build_context(
        self,
        documents: list[Document],
    ) -> str:
        """
        Build a context string from retrieved documents.

        Args:
            documents: Retrieved documents.

        Returns:
            Context string.
        """

        context_parts: list[str] = []

        for i, document in enumerate(documents, start=1):

            metadata = document.metadata

            context_parts.append(
                "\n".join(
                    [
                        f"Document {i}",
                        f"Source: {metadata.get('source', 'Unknown')}",
                        f"Class: {metadata.get('class', 'Unknown')}",
                        f"Subject: {metadata.get('subject', 'Unknown')}",
                        f"Chapter: {metadata.get('chapter_number', 'Unknown')}",
                        "",
                        document.page_content,
                    ]
                )
            )

        return "\n\n" + ("\n" + "=" * 80 + "\n\n").join(context_parts)

    def get_context(
        self,
        query: str,
    ) -> tuple[str, list[Document]]:
        """
        Retrieve documents and build the context.

        Args:
            query: User question.

        Returns:
            Tuple containing:
                - Context string
                - Retrieved documents
        """

        documents = self.retrieve(query)

        context = self.build_context(documents)

        return context, documents



    def answer(
        self,
        query: str,
        prompt_template: str | None = None,
    ) -> tuple[str, list[Document]]:
        """
        Answer a question using Retrieval-Augmented Generation.

        Args:
            query: User question.
            prompt_template: Optional custom prompt template.

        Returns:
            Tuple containing:
                - Generated answer
                - Retrieved documents
        """

        context, documents = self.get_context(query)

        if prompt_template is None:

            prompt = f"""
    You are an expert NCERT tutor.

    Answer ONLY using the provided context.

    If the answer is not present in the context, reply exactly:

    "I could not find this information in the provided documents."

    Do not make up information.
    Do not use outside knowledge.
    Keep your answer clear, concise, and suitable for Class 10 students.

    Context:
    {context}

    Question:
    {query}

    Answer:
    """

        else:

            prompt = prompt_template.format(
                context=context,
                question=query,
            )

        answer = self.llm.generate(prompt)

        return answer, documents
