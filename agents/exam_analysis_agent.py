"""
agents/exam_analysis_agent.py

Evidence-based Exam Analysis Agent

Uses:
    data/exam_database.json

Responsibilities
----------------
1. Analyze previous-year papers.
2. Compute chapter weightage.
3. Find recurring concepts.
4. Find repeated questions.
5. Produce evidence-backed report using the LLM.
6. Understand natural language queries to determine intent and extract topics.
"""

from collections import Counter, defaultdict
import json
import os
import re

from modules.llm_client import LLMClient


class ExamAnalysisAgent:

    def __init__(self, llm: LLMClient):

        self.llm = llm

        base_dir = os.path.dirname(os.path.dirname(__file__))

        self.database_path = os.path.join(
            base_dir,
            "data",
            "exam_database.json",
        )

        self.database = self.load_database()
        self.vocabulary = self._build_vocabulary()

    # ==========================================================
    # DATABASE
    # ==========================================================

    def load_database(self):

        if not os.path.exists(self.database_path):
            return []

        with open(self.database_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _build_vocabulary(self):
        """
        Dynamically extracts all chapters and concepts from the database 
        to serve as a vocabulary for natural language topic extraction.
        """
        vocab = set()
        for item in self.database:
            chap = item.get("chapter", "").lower().strip()
            conc = item.get("concept", "").lower().strip()

            if chap and chap != "unknown":
                vocab.add(chap)
                # Create aliases for hyphenated chapters (e.g. "Light - Reflection")
                if "-" in chap:
                    for part in chap.split("-"):
                        vocab.add(part.strip())

            if conc and conc != "unknown":
                vocab.add(conc)

        # Add common shorthands just in case
        extras = ["light", "electricity", "carbon", "human eye", "environment", "magnetic effects"]
        for ext in extras:
            vocab.add(ext)

        # Sort by length (descending) to always match the longest specific phrase first
        return sorted([v for v in vocab if len(v) > 2], key=len, reverse=True)

    # ==========================================================
    # NLP / QUERY PARSING PIPELINE
    # ==========================================================

    def detect_intent(self, query: str) -> str:
        """
        Rule-based intent detection using keyword matching.
        No LLM is used here to maintain speed and determinism.
        """
        q = query.lower()

        # 6. Chapter Weightage
        if any(k in q for k in ["weightage", "important chapter", "highest weightage", "chapter weight"]):
            return "Chapter Weightage"

        # 2. Count Previous Year Questions
        if any(k in q for k in ["how many", "number of", "count"]):
            return "Count PYQs"

        # 4. Repeated Questions
        if any(k in q for k in ["repeat", "repeated"]):
            return "Repeated Questions"

        # 5. Recurring Concepts
        if any(k in q for k in ["concept", "recurring concept", "frequently asked concept"]):
            return "Recurring Concepts"

        # 7. Year-wise Distribution
        if any(k in q for k in ["year", "years distribution", "which years"]):
            return "Year-wise Distribution"

        # 3. Show Previous Year Questions
        if any(k in q for k in ["show", "list", "give me previous year"]):
            return "Show PYQs"

        # 1. Full Analysis (Default fallback)
        return "Full Analysis"

    def extract_topic(self, query: str) -> str:
        """
        Extracts the chapter or concept name from a natural language query 
        by matching against the known vocabulary.
        """
        q = query.lower()
        
        for term in self.vocabulary:
            # Look for whole word matches to avoid accidental substring hits
            if re.search(rf"\b{re.escape(term)}\b", q):
                return term
                
        return ""

    # ==========================================================
    # FILTER DATABASE
    # ==========================================================

    def filter_questions(self, topic: str):

        topic = topic.lower()
        results = []

        for item in self.database:
            chapter = item.get("chapter", "").lower()
            concept = item.get("concept", "").lower()
            question = item.get("question", "").lower()

            if topic in chapter or topic in concept or topic in question:
                results.append(item)

        return results

    # ==========================================================
    # STATISTICS METHODS (Preserved)
    # ==========================================================

    def chapter_statistics(self):

        counter = Counter()
        for item in self.database:
            counter[item["chapter"]] += 1

        total = sum(counter.values())
        stats = []

        for chapter, count in counter.most_common():
            percentage = round(count * 100 / total, 1) if total > 0 else 0
            stats.append(
                {
                    "chapter": chapter,
                    "questions": count,
                    "percentage": percentage,
                }
            )

        return stats

    def concept_statistics(self, questions):
        counter = Counter()
        for item in questions:
            concept = item.get("concept", "Unknown")
            if concept != "Unknown":
                counter[concept] += 1
        return counter

    def year_statistics(self, questions):
        result = defaultdict(int)
        for item in questions:
            result[item["year"]] += 1
        return dict(result)

    def repeated_questions(self, questions):
        counter = Counter()
        for item in questions:
            q = item["question"].strip()
            counter[q] += 1

        repeated = []
        for question, freq in counter.items():
            if freq > 1:
                repeated.append(
                    {
                        "question": question,
                        "frequency": freq,
                    }
                )

        repeated.sort(key=lambda x: x["frequency"], reverse=True)
        return repeated[:10]

    def build_statistics(self, questions):
        """
        Consolidated statistics builder using pre-filtered questions.
        """
        return {
            "questions": questions,
            "concepts": self.concept_statistics(questions),
            "years": self.year_statistics(questions),
            "repeated": self.repeated_questions(questions),
            "chapters": self.chapter_statistics(),
        }

    # ==========================================================
    # FORMATTING METHODS
    # ==========================================================

    def format_chapter_weightage(self, chapters):
        if not chapters:
            return "No chapter data available."
            
        text = []
        for item in chapters:
            text.append(
                f"- {item['chapter']} : "
                f"{item['questions']} questions "
                f"({item['percentage']}%)"
            )
        return "\n".join(text)

    def format_concepts(self, concepts):
        if not concepts:
            return "No recurring concepts found."
        lines = []
        for concept, freq in concepts.most_common():
            lines.append(f"- {concept} ({freq} times)")
        return "\n".join(lines)

    def format_years(self, years):
        if not years:
            return "No year data available."
        lines = []
        for year in sorted(years):
            lines.append(f"- {year}: {years[year]} questions")
        return "\n".join(lines)

    def format_repeated_questions(self, repeated):
        if not repeated:
            return "No repeated questions found."
        lines = []
        for item in repeated:
            q = item["question"]
            if len(q) > 180:
                q = q[:180] + "..."
            lines.append(f"- ({item['frequency']}x) {q}")
        return "\n".join(lines)

    def format_questions(self, questions):
        if not questions:
            return "No previous year questions found."
        output = []
        for item in questions:
            answer = item.get("answer", "")
            output.append(f"""
Year: {item['year']}
Question {item['question_no']}:

{item['question']}

Answer:
{answer}

Concept:
{item['concept']}
""".strip())
        return "\n\n---------------------------------\n\n".join(output)

    # ==========================================================
    # LLM REPORT GENERATION
    # ==========================================================

    def build_prompt(self, topic, stats):

        chapter_weightage = self.format_chapter_weightage(stats["chapters"])
        concepts = self.format_concepts(stats["concepts"])
        years = self.format_years(stats["years"])
        repeated = self.format_repeated_questions(stats["repeated"])
        pyqs = self.format_questions(stats["questions"])

        return f"""
You are an expert CBSE Science teacher.

You MUST use ONLY the evidence below.
Do NOT invent trends.
Do NOT assume frequency.
Use ONLY the supplied statistics.

==================================================
TOPIC
==================================================
{topic}

==================================================
CHAPTER WEIGHTAGE
==================================================
{chapter_weightage}

==================================================
YEAR DISTRIBUTION
==================================================
{years}

==================================================
RECURRING CONCEPTS
==================================================
{concepts}

==================================================
REPEATED QUESTIONS
==================================================
{repeated}

==================================================
PREVIOUS YEAR QUESTIONS
==================================================
{pyqs}
==================================================

Prepare a detailed report with exactly these sections.

# Topic Overview
Explain the topic briefly.

# Previous Year Trend
Explain how often this topic appeared.
Mention years.

# Frequently Asked Concepts
Rank concepts from most frequent to least.

# Common Question Patterns
Explain the pattern instead of copying questions.

# Expected Questions
Predict likely questions ONLY based on previous trends.

# Preparation Strategy
Give practical preparation advice.

# Difficulty Level
Easy / Moderate / Difficult
Explain why.

Do NOT hallucinate.
Everything must be supported by the supplied evidence.
"""

    def generate_report(self, topic: str, questions: list) -> str:
        """
        Generates an evidence-based report using the LLM.
        """
        stats = self.build_statistics(questions)

        prompt = self.build_prompt(
            topic=topic,
            stats=stats,
        )

        report = self.llm.generate(
            prompt=prompt,
            system_prompt=(
                "You are an expert CBSE board exam analyst. "
                "Never invent statistics. "
                "Use ONLY the supplied evidence."
            ),
        )

        return report

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def run(self, query: str, context: str = "") -> str:
        """
        Main entry point. Parses the natural language query, 
        determines intent, extracts the topic, and routes to the 
        appropriate sub-routine.
        """
        
        # 1. Pipeline: Intent Detection
        intent = self.detect_intent(query)
        
        # Branch early if the intent does not require a specific topic
        if intent == "Chapter Weightage":
            stats = self.chapter_statistics()
            return f"**Chapter Weightage Analysis:**\n\n{self.format_chapter_weightage(stats)}"

        # 2. Pipeline: Topic Extraction
        topic = self.extract_topic(query)
        
        if not topic:
            return "I couldn't identify a specific chapter or concept in your query. Could you please specify one? (e.g., 'Electricity' or 'Refraction')"

        # 3. Pipeline: Database Filtering
        questions = self.filter_questions(topic)

        if not questions:
            return f"No previous-year questions were found for '{topic.title()}'. Add more sample papers or check the topic name."

        # 4. Pipeline: Statistics Generation / Output Routing
        if intent == "Count PYQs":
            return f"There are **{len(questions)}** previous year questions from **{topic.title()}**."

        if intent == "Show PYQs":
            return f"**Previous Year Questions for {topic.title()}**\n\n" + self.format_questions(questions)

        if intent == "Repeated Questions":
            repeated = self.repeated_questions(questions)
            return f"**Repeated Questions in {topic.title()}**\n\n" + self.format_repeated_questions(repeated)

        if intent == "Recurring Concepts":
            concepts = self.concept_statistics(questions)
            return f"**Frequently Asked Concepts in {topic.title()}**\n\n" + self.format_concepts(concepts)

        if intent == "Year-wise Distribution":
            years = self.year_statistics(questions)
            return f"**Year-wise Distribution for {topic.title()}**\n\n" + self.format_years(years)

        # 5. Pipeline: LLM Report Generation (Only for Full Analysis)
        return self.generate_report(topic.title(), questions)

    # ==========================================================
    # DEBUG
    # ==========================================================

    def preview(self, topic: str):

        questions = self.filter_questions(topic)
        stats = self.build_statistics(questions)

        print("=" * 60)
        print("Topic:", topic)
        print("=" * 60)

        print("\nQuestions:", len(stats["questions"]))

        print("\nConcepts:")
        for concept, freq in stats["concepts"].most_common():
            print(f"  {concept:<35} {freq}")

        print("\nYears:")
        for year, count in sorted(stats["years"].items()):
            print(f"  {year}: {count}")

        print("\nTop Chapter Weightage:")
        for item in stats["chapters"][:10]:
            print(
                f"  {item['chapter']:<40}"
                f"{item['questions']:>3}"
                f" ({item['percentage']}%)"
            )

        print("\nRepeated Questions:")
        for item in stats["repeated"]:
            print("-", item["question"][:100])

        print("=" * 60)