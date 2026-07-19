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
"""

from collections import Counter, defaultdict
import json
import os

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

    # ==========================================================
    # DATABASE
    # ==========================================================

    def load_database(self):

        if not os.path.exists(self.database_path):
            return []

        with open(self.database_path, "r", encoding="utf-8") as file:
            return json.load(file)

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
    # CHAPTER WEIGHTAGE
    # ==========================================================

    def chapter_statistics(self):

        counter = Counter()

        for item in self.database:

            counter[item["chapter"]] += 1

        total = sum(counter.values())

        stats = []

        for chapter, count in counter.most_common():

            percentage = round(count * 100 / total, 1)

            stats.append(
                {
                    "chapter": chapter,
                    "questions": count,
                    "percentage": percentage,
                }
            )

        return stats

    # ==========================================================
    # CONCEPT STATISTICS
    # ==========================================================

    def concept_statistics(self, questions):

        counter = Counter()

        for item in questions:

            concept = item.get("concept", "Unknown")

            if concept != "Unknown":

                counter[concept] += 1

        return counter

    # ==========================================================
    # YEAR STATISTICS
    # ==========================================================

    def year_statistics(self, questions):

        result = defaultdict(int)

        for item in questions:

            result[item["year"]] += 1

        return dict(result)

    # ==========================================================
    # REPEATED QUESTIONS
    # ==========================================================

    def repeated_questions(self, questions):

        counter = Counter()

        originals = {}

        for item in questions:

            q = item["question"].strip()

            counter[q] += 1

            originals[q] = item

        repeated = []

        for question, freq in counter.items():

            if freq > 1:

                repeated.append(
                    {
                        "question": question,
                        "frequency": freq,
                    }
                )

        repeated.sort(
            key=lambda x: x["frequency"],
            reverse=True,
        )

        return repeated[:10]

    # ==========================================================
    # BUILD SUMMARY
    # ==========================================================

    def build_statistics(self, topic):

        questions = self.filter_questions(topic)

        concepts = self.concept_statistics(questions)

        years = self.year_statistics(questions)

        repeated = self.repeated_questions(questions)

        chapters = self.chapter_statistics()

        return {
            "questions": questions,
            "concepts": concepts,
            "years": years,
            "repeated": repeated,
            "chapters": chapters,
        }
        # ==========================================================

    # FORMAT CHAPTER WEIGHTAGE
    # ==========================================================

    def format_chapter_weightage(self, chapters):

        text = []

        for item in chapters:

            text.append(
                f"- {item['chapter']} : "
                f"{item['questions']} questions "
                f"({item['percentage']}%)"
            )

        return "\n".join(text)

    # ==========================================================
    # FORMAT CONCEPTS
    # ==========================================================

    def format_concepts(self, concepts):

        if not concepts:
            return "No recurring concepts found."

        lines = []

        for concept, freq in concepts.most_common():

            lines.append(f"- {concept} ({freq} times)")

        return "\n".join(lines)

    # ==========================================================
    # FORMAT YEAR DISTRIBUTION
    # ==========================================================

    def format_years(self, years):

        if not years:
            return "No data."

        lines = []

        for year in sorted(years):

            lines.append(f"- {year}: {years[year]} questions")

        return "\n".join(lines)

    # ==========================================================
    # FORMAT REPEATED QUESTIONS
    # ==========================================================

    def format_repeated_questions(self, repeated):

        if not repeated:
            return "No repeated questions."

        lines = []

        for item in repeated:

            q = item["question"]

            if len(q) > 180:
                q = q[:180] + "..."

            lines.append(f"- ({item['frequency']}x) {q}")

        return "\n".join(lines)

    # ==========================================================
    # FORMAT PYQs
    # ==========================================================

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
    # BUILD PROMPT
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
        # ==========================================================

    # GENERATE REPORT
    # ==========================================================

    def generate_report(
        self,
        topic: str,
    ) -> str:
        """
        Generates an evidence-based report.
        """

        stats = self.build_statistics(topic)

        if len(stats["questions"]) == 0:

            return (
                f"No previous-year questions were found for '{topic}'. "
                "Add more sample papers or check the topic name."
            )

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

    def run(
        self,
        topic: str,
        context: str = "",
    ) -> str:
        """
        Main entry point.

        Parameters
        ----------
        topic : str
            Chapter or concept name.

        context : str
            Ignored now.
            Kept only for compatibility with the existing project.
        """

        return self.generate_report(topic)

    # ==========================================================
    # DEBUG
    # ==========================================================

    def preview(self, topic: str):

        stats = self.build_statistics(topic)

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
