"""
quality_auditor_agent.py

Responsible for:
1. Evaluating Groundedness (detecting hallucinations).
2. Measuring Completeness (context recall).
3. Assessing Coherence and Conciseness.
4. Returning a structured, professional audit report with quantifiable metrics.
"""

from modules.llm_client import LLMClient


class QualityAuditorAgent:
    """Reviews AI-generated content using professional evaluation metrics."""

    def __init__(
        self,
        llm: LLMClient,
    ) -> None:
        """
        Initialize the Quality Auditor.a

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
        Build the quality audit prompt using standard LLM evaluation metrics.
        """

        return f"""
You are an expert AI Quality Auditor using industry-standard evaluation metrics for Retrieval-Augmented Generation (RAG) and LLM outputs.

Evaluate the generated content against the reference context using the following professional metrics:

1. Groundedness (Faithfulness): Measures if all claims in the generated content are directly supported by the reference context. High scores indicate no hallucinations.
2. Completeness (Context Recall): Measures whether all crucial and relevant information from the reference context is successfully captured in the generated content.
3. Coherence: Measures the logical flow, structural organization, and readability of the generated content.
4. Conciseness: Measures whether the generated content is direct, relevant, and free of unnecessary verbosity or repetition.

Return your response in exactly this format:

## 1. Groundedness (Score: 1-5)
- **Justification:** [Briefly explain the score]
- **Hallucinations/Unsupported Claims:** [List any found, or state "None"]

## 2. Completeness (Score: 1-5)
- **Justification:** [Briefly explain the score]
- **Missing Information:** [List key omitted details, or state "None"]

## 3. Coherence (Score: 1-5)
- **Justification:** [Briefly evaluate flow, transitions, and readability]

## 4. Conciseness (Score: 1-5)
- **Justification:** [Briefly evaluate verbosity and directness]

## Overall Summary
[Provide a brief 2-3 sentence executive summary of the content's quality.]

## Final Score
[Calculate the percentage: (Sum of scores / 20) * 100]%

---
**Reference Context:**
{reference_context}

**Generated Content:**
{generated_output}
"""

    def run(
        self,
        generated_output: str,
        reference_context: str,
    ) -> str:
        """
        Audit generated content using professional metrics.

        Args:
            generated_output:
                Content produced by another agent.
            reference_context:
                Original retrieved context used as the source of truth.

        Returns:
            Structured audit report with scores and justifications.
        """
        prompt = self.build_prompt(
            generated_output=generated_output,
            reference_context=reference_context,
        )

        return self.llm.generate(prompt)
