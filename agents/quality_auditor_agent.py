"""
quality_auditor_agent.py

Responsible for:
1. Verifying formatting.
2. Checking factual consistency.
3. Detecting possible hallucinations.
4. Returning an audit report.
"""

from modules.llm_client import LLMClient


class QualityAuditorAgent:
    """Reviews AI-generated content."""

    def __init__(
        self,
        llm: LLMClient,
    ) -> None:
        """
        Initialize the Quality Auditor.

        Args:
            llm:
                Language model client.
        """

        self.llm = llm

    def build_prompt(
        self,
        generated_output: str,
        reference_context: str,
    ) -> str:
        """
        Build the quality audit prompt.
        """

        return f"""
You are an expert AI Quality Auditor.

Compare the generated content against the reference context.

Evaluate:

1. Formatting
2. Factual consistency
3. Hallucinations
4. Missing important information

Return your response in exactly this format:

## Formatting
PASS or FAIL

## Factual Consistency
PASS or FAIL

## Hallucination Check
PASS or FAIL

## Missing Information
- item 1
- item 2

## Overall Score
Give a score out of 100.

Reference Context:

{reference_context}

Generated Content:

{generated_output}
"""

    def run(
        self,
        generated_output: str,
        reference_context: str,
    ) -> str:
        """
        Audit generated content.

        Args:
            generated_output:
                Content produced by another agent.

            reference_context:
                Original retrieved context.

        Returns:
            Audit report.
        """

        prompt = self.build_prompt(
            generated_output=generated_output,
            reference_context=reference_context,
        )

        return self.llm.generate(prompt)