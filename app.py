"""
app.py

Main entry point for the Multi-Agent Student Study Assistant.
"""

from pathlib import Path

from agents.notes_agent import NotesAgent
from modules.chunker import DocumentChunker
from modules.document_loader import DocumentLoader
from modules.llm_client import LLMClient
from modules.rag_pipeline import RAGPipeline
from modules.retriever import Retriever
from modules.vector_store import VectorStore


VECTOR_DB_PATH = Path("data/vector_store/index.faiss")


def initialize_rag() -> RAGPipeline:
    """
    Initialize the complete RAG pipeline.

    Returns:
        Configured RAGPipeline object.
    """

    vector_store = VectorStore()

    if VECTOR_DB_PATH.exists():

        print("Loading existing vector database...\n")

        vector_store.load()

    else:

        print("No vector database found.")
        print("Building vector database...\n")

        loader = DocumentLoader("data/books/Class10/Science")

        documents = loader.load()

        chunker = DocumentChunker()

        chunks = chunker.split(documents)

        vector_store.build(chunks)

        vector_store.save()

        print("Vector database created successfully!\n")

    retriever = Retriever(vector_store)

    llm = LLMClient()

    return RAGPipeline(
        retriever=retriever,
        llm=llm,
    )


def print_sources(documents) -> None:
    """
    Print retrieved document sources.
    """

    print("\n" + "=" * 80)
    print("SOURCES")
    print("=" * 80)

    for i, document in enumerate(documents, start=1):

        metadata = document.metadata

        print(f"\n{i}. {metadata.get('source', 'Unknown Source')}")
        print(f"   Class   : {metadata.get('class', 'Unknown')}")
        print(f"   Subject : {metadata.get('subject', 'Unknown')}")
        print(f"   Chapter : {metadata.get('chapter_number', 'Unknown')}")


def ask_question(
    rag: RAGPipeline,
) -> None:
    """
    Ask a question using the RAG pipeline.
    """

    query = input("\nEnter your question: ").strip()

    if not query:
        return

    print("\nGenerating answer...\n")

    answer, documents = rag.answer(query)

    print("=" * 80)
    print("ANSWER")
    print("=" * 80)
    print(answer)

    print_sources(documents)


def generate_notes(
    notes_agent: NotesAgent,
) -> None:
    """
    Generate notes for a topic.
    """

    topic = input("\nEnter chapter/topic: ").strip()

    if not topic:
        return

    print("\nGenerating notes...\n")

    notes, output_path = notes_agent.run(topic)

    print("=" * 80)
    print("NOTES GENERATED")
    print("=" * 80)

    print(notes[:1000])

    if len(notes) > 1000:
        print("\n...(output truncated)...")

    print(f"\nSaved to: {output_path}")


def show_menu() -> str:
    """
    Display the main menu.

    Returns:
        User choice.
    """

    print("\n" + "=" * 80)
    print("Multi-Agent Student Study Assistant")
    print("=" * 80)
    print("1. Ask Question")
    print("2. Generate Notes")
    print("3. Exit")
    print("=" * 80)

    return input("Select an option: ").strip()


def main() -> None:

    rag = initialize_rag()

    notes_agent = NotesAgent(rag)

    while True:

        choice = show_menu()

        if choice == "1":

            ask_question(rag)

        elif choice == "2":

            generate_notes(notes_agent)

        elif choice == "3":

            print("\nGoodbye!")

            break

        else:

            print("\nInvalid option. Please try again.")


if __name__ == "__main__":
    main()