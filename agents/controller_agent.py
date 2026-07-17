"""
controller_agent.py

Responsible for:
1. Orchestrating all AI agents.
2. Displaying the main menu.
3. Routing user requests to the appropriate agent.
"""

from agents.notes_agent import NotesAgent
from modules.rag_pipeline import RAGPipeline


class ControllerAgent:
    """Coordinates all AI agents."""

    def __init__(
        self,
        rag_pipeline: RAGPipeline,
    ) -> None:
        """
        Initialize all agents.

        Args:
            rag_pipeline: Shared RAG pipeline.
        """

        self.notes_agent = NotesAgent(rag_pipeline)

        # Future agents
        # self.flashcard_agent = FlashcardAgent(rag_pipeline)
        # self.exam_agent = ExamAnalysisAgent(rag_pipeline)
        # self.quality_agent = QualityAuditorAgent(rag_pipeline)

    def show_menu(self) -> str:
        """
        Display the main menu.

        Returns:
            User's menu choice.
        """

        print("\n" + "=" * 80)
        print("Multi-Agent Student Study Assistant")
        print("=" * 80)
        print("1. Retrieval Agent (Ask Questions)")
        print("2. Notes Agent")
        print("3. Flashcard Agent (Coming Soon)")
        print("4. Exam Analysis Agent (Coming Soon)")
        print("5. Quality Auditor Agent (Coming Soon)")
        print("6. Exit")
        print("=" * 80)

        return input("Select an option: ").strip()

    def retrieval_agent(
        self,
        rag: RAGPipeline,
    ) -> None:
        """
        Handle question answering.
        """

        query = input("\nEnter your question: ").strip()

        if not query:
            return

        print("\nThinking...\n")

        answer, documents = rag.answer(query)

        print("=" * 80)
        print("ANSWER")
        print("=" * 80)
        print(answer)

        print("\n" + "=" * 80)
        print("SOURCES")
        print("=" * 80)

        for i, document in enumerate(documents, start=1):

            metadata = document.metadata

            print(f"\n{i}. {metadata.get('source', 'Unknown')}")
            print(f"   Class   : {metadata.get('class', 'Unknown')}")
            print(f"   Subject : {metadata.get('subject', 'Unknown')}")
            print(f"   Chapter : {metadata.get('chapter_number', 'Unknown')}")

    def notes_agent_menu(self) -> None:
        """
        Handle Notes Agent.
        """

        topic = input("\nEnter chapter/topic: ").strip()

        if not topic:
            return

        print("\nGenerating notes...\n")

        notes, output_path = self.notes_agent.run(topic)

        print("=" * 80)
        print("NOTES GENERATED")
        print("=" * 80)

        print(notes[:1000])

        if len(notes) > 1000:
            print("\n...(output truncated)...")

        print(f"\nSaved to: {output_path}")

    def run(
        self,
        rag: RAGPipeline,
    ) -> None:
        """
        Start the Controller Agent.
        """

        while True:

            choice = self.show_menu()

            if choice == "1":

                self.retrieval_agent(rag)

            elif choice == "2":

                self.notes_agent_menu()

            elif choice == "3":

                print("\nFlashcard Agent is under development.")

            elif choice == "4":

                print("\nExam Analysis Agent is under development.")

            elif choice == "5":

                print("\nQuality Auditor Agent is under development.")

            elif choice == "6":

                print("\nGoodbye!")

                break

            else:

                print("\nInvalid choice.")
