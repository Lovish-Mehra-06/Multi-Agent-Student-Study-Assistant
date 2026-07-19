"""
app.py

Main entry point for the Multi-Agent Student Study Assistant.
"""

from pathlib import Path

from agents.answer_agent import AnswerAgent
from agents.controller_agent import ControllerAgent
from agents.exam_analysis_agent import ExamAnalysisAgent
from agents.flashcard_agent import FlashcardAgent
from agents.notes_agent import NotesAgent
from agents.quality_auditor_agent import QualityAuditorAgent
from agents.retrieval_agent import RetrievalAgent

from modules.chunker import DocumentChunker
from modules.csv_writer import CSVWriter
from modules.document_loader import DocumentLoader
from modules.llm_client import LLMClient
from modules.markdown_writer import MarkdownWriter
from modules.retriever import RetrieverTool
from modules.vector_store import VectorStore

BOOKS_PATH = "data/books/Class10/Science"
VECTOR_DB_PATH = "data/vector_store/index.faiss"


def build_vector_database() -> VectorStore:
    """
    Load existing vector database or build a new one.
    """

    vector_store = VectorStore()

    if Path(VECTOR_DB_PATH).exists():

        print("Loading existing vector database...\n")

        vector_store.load()

    else:

        print("Building vector database...\n")

        loader = DocumentLoader(BOOKS_PATH)

        documents = loader.load()

        chunker = DocumentChunker()

        chunks = chunker.split(documents)

        vector_store.build(chunks)

        vector_store.save()

        print("Vector database created successfully.\n")

    return vector_store


def create_controller() -> ControllerAgent:
    """
    Create all agents.
    """

    # -----------------------------------------
    # Build / Load Vector Database
    # -----------------------------------------

    vector_store = build_vector_database()

    retriever_tool = RetrieverTool(
        vector_store,
    )

    retrieval_agent = RetrievalAgent(
        retriever_tool,
    )

    # -----------------------------------------
    # LLM
    # -----------------------------------------

    llm = LLMClient(temperature=0.2)

    # -----------------------------------------
    # Writers
    # -----------------------------------------

    markdown_writer = MarkdownWriter()

    csv_writer = CSVWriter()

    # -----------------------------------------
    # Agents
    # -----------------------------------------

    answer_agent = AnswerAgent(
        llm,
    )

    notes_agent = NotesAgent(
        llm,
        markdown_writer,
    )

    flashcard_agent = FlashcardAgent(
        llm,
        csv_writer,
    )

    # NEW Exam Analysis Agent
    exam_agent = ExamAnalysisAgent(
        llm=llm,
    )

    quality_agent = QualityAuditorAgent(
        llm,
    )

    # -----------------------------------------
    # Controller
    # -----------------------------------------

    controller = ControllerAgent(
        retrieval_agent=retrieval_agent,
        answer_agent=answer_agent,
        notes_agent=notes_agent,
        flashcard_agent=flashcard_agent,
        exam_agent=exam_agent,
        quality_agent=quality_agent,
    )

    return controller


def main() -> None:

    print("=" * 80)
    print("Multi-Agent Student Study Assistant")
    print("=" * 80)

    controller = create_controller()

    while True:

        print("\n" + "-" * 80)

        query = input("Enter your query ('exit' to quit): ").strip()

        if query.lower() == "exit":

            print("\nGoodbye!")

            break

        result = controller.run(query)

        print("\n" + "=" * 80)
        print("RESULT")
        print("=" * 80)

        if result["type"] == "answer":

            print(result["answer"])

        elif result["type"] == "notes":

            print(result["notes"])
            print(f"\nSaved to : {result['notes_file']}")

        elif result["type"] == "flashcards":

            print(result["notes"])
            print(f"\nNotes      : {result['notes_file']}")
            print(f"Flashcards : {result['flashcards_file']}")

        elif result["type"] == "exam_analysis":

            print(result["report"])

            if result["sources"]:

                print("\n" + "=" * 80)
                print("PREVIOUS YEAR QUESTIONS")
                print("=" * 80)

                for i, q in enumerate(result["sources"], start=1):

                    print(f"\nQ{i}. ({q['year']})")

                    print(f"Chapter : {q['chapter']}")

                    print(f"Concept : {q.get('concept','Unknown')}")

                    print(f"\nQuestion:\n{q['question']}")

                    if q["answer"]:
                        print(f"\nAnswer:\n{q['answer']}")

        print("\n" + "=" * 80)
        print("QUALITY REPORT")
        print("=" * 80)

        print(result["audit"])

        print("\n" + "=" * 80)
        print("SOURCES")
        print("=" * 80)

        if result["type"] != "exam_analysis":

            for i, document in enumerate(result["sources"], start=1):

                metadata = document.metadata

                print(f"\n{i}. {metadata.get('source', 'Unknown')}")

                print(f"   Chapter : {metadata.get('chapter_number', 'Unknown')}")

                print(f"   Subject : {metadata.get('subject', 'Unknown')}")


if __name__ == "__main__":
    main()
