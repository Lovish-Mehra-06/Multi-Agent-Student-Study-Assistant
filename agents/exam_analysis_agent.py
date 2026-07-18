
"""
exam_analysis_agent.py

Responsible for:
1. Analyzing previous-year questions.
2. Identifying recurring concepts.
3. Estimating chapter weightage.
"""

from modules.llm_client import LLMClient


class ExamAnalysisAgent:
    """Analyzes previous-year exam questions."""

    def __init__(
        self,
        llm: LLMClient,
    ) -> None:
        """
        Initialize the Exam Analysis Agent.

        Args:
            llm:
                Language model client.
        """

        self.llm = llm

    def build_prompt(
        self,
        topic: str,
        context: str,
    ) -> str:
        """
        Build prompt for exam analysis.
        """

        return f"""
You are an experienced CBSE exam analyst.

Analyze ONLY the previous-year questions provided.

Generate the following:

# Important Topics

# Frequently Asked Concepts

# Repeated Questions

# Estimated Chapter Weightage

# Preparation Tips

Topic:
{topic}

Previous Year Questions:

{context}
"""

    def run(
        self,
        topic: str,
        context: str,
    ) -> str:
        """
        Analyze previous-year questions.

        Args:
            topic:
                Chapter/topic.

            context:
                Retrieved PYQs.

        Returns:
            Analysis report.
        """

        prompt = self.build_prompt(
            topic=topic,
            context=context,
        )

        report = self.llm.generate(prompt)

        return report