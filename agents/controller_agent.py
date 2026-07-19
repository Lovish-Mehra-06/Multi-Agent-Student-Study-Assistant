"""
controller_agent.py

Responsible for:
1. Receiving user queries.
2. Detecting user intent.
3. Executing the correct workflow.
"""

from agents.answer_agent import AnswerAgent
from agents.exam_analysis_agent import ExamAnalysisAgent
from agents.flashcard_agent import FlashcardAgent
from agents.notes_agent import NotesAgent
from agents.quality_auditor_agent import QualityAuditorAgent
from agents.retrieval_agent import RetrievalAgent


class ControllerAgent:
    """Main orchestrator."""

    def __init__(
        self,
        retrieval_agent: RetrievalAgent,
        answer_agent: AnswerAgent,
        notes_agent: NotesAgent,
        flashcard_agent: FlashcardAgent,
        exam_agent: ExamAnalysisAgent,
        quality_agent: QualityAuditorAgent,
    ) -> None:

        self.retrieval_agent = retrieval_agent
        self.answer_agent = answer_agent
        self.notes_agent = notes_agent
        self.flashcard_agent = flashcard_agent
        self.exam_agent = exam_agent
        self.quality_agent = quality_agent

    # --------------------------------------------------
    # Extract Chapter Name from User Query
    # --------------------------------------------------

    def extract_exam_topic(self, query: str) -> str:

        q = query.lower()

        remove_words = [
            "exam",
            "analysis",
            "analyse",
            "analyze",
            "trend",
            "trends",
            "pyq",
            "previous",
            "year",
            "years",
            "question",
            "questions",
            "of",
            "for",
            "about",
            "chapter",
            "tell",
            "me",
            "show",
            "give",
        ]

        for word in remove_words:
            q = q.replace(word, "")

        return " ".join(q.split()).title()

    # --------------------------------------------------
    # Main Workflow
    # --------------------------------------------------

    def run(
        self,
        query: str,
    ):

        query_lower = query.lower()

        # --------------------------------------------------
        # Flashcards
        # --------------------------------------------------

        if "flashcard" in query_lower:

            context, documents = self.retrieval_agent.run(query)

            notes, notes_path = self.notes_agent.run(
                query,
                context,
            )

            csv_path = self.flashcard_agent.run(
                query,
                notes,
            )

            audit = self.quality_agent.run(
                notes,
                context,
            )

            return {
                "type": "flashcards",
                "notes": notes,
                "notes_file": notes_path,
                "flashcards_file": csv_path,
                "audit": audit,
                "sources": documents,
            }

        # --------------------------------------------------
        # Notes
        # --------------------------------------------------

        if "note" in query_lower:

            context, documents = self.retrieval_agent.run(query)

            notes, notes_path = self.notes_agent.run(
                query,
                context,
            )

            audit = self.quality_agent.run(
                notes,
                context,
            )

            return {
                "type": "notes",
                "notes": notes,
                "notes_file": notes_path,
                "audit": audit,
                "sources": documents,
            }

        # --------------------------------------------------
        # Exam Analysis
        # --------------------------------------------------

        if (
            "exam" in query_lower
            or "pyq" in query_lower
            or "previous year" in query_lower
            or "trend" in query_lower
        ):

            topic = self.extract_exam_topic(query)

            report = self.exam_agent.run(topic)

            audit = self.quality_agent.run(
                report,
                report,
            )

            return {
                "type": "exam_analysis",
                "report": report,
                "audit": audit,
                "sources": [],
            }

        # --------------------------------------------------
        # Default QA
        # --------------------------------------------------

        context, documents = self.retrieval_agent.run(query)

        answer = self.answer_agent.run(
            query,
            context,
        )

        audit = self.quality_agent.run(
            answer,
            context,
        )

        return {
            "type": "answer",
            "answer": answer,
            "audit": audit,
            "sources": documents,
        }
