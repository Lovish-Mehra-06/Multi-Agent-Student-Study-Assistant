"""
notes_agent.py

Responsible for:
1. Generating chapter notes.
2. Producing Markdown.
3. Formatting equations using LaTeX.
"""

from modules.llm_client import LLMClient
from modules.markdown_writer import MarkdownWriter


class NotesAgent:

    def __init__(
        self,
        llm: LLMClient,
        writer: MarkdownWriter,
    ) -> None:

        self.llm = llm
        self.writer = writer

    def build_prompt(
        self,
        query: str,
        context: str,
    ) -> str:
        """
        Build the prompt for note generation.
        """

        return f"""
You are an expert NCERT teacher.

Use ONLY the provided textbook context.

Generate well-structured study notes in Markdown.

Requirements:

- Use Markdown headings.
- Explain concepts clearly.
- Use bullet points where appropriate.
- Include important definitions.
- Include formulas.
- Write mathematical equations in LaTeX.
- Mention important facts.
- Do not invent information.
- If information is missing, state that clearly.

Context:

{context}

Topic:

{query}
"""

    def run(
        self,
        query: str,
        context: str,
    ) -> tuple[str, str]:

        prompt = self.build_prompt(
            query=query,
            context=context,
        )

        markdown = self.llm.generate(prompt)

        file_path = self.writer.save(
            topic=query,
            markdown=markdown,
        )

        return markdown, str(file_path)
