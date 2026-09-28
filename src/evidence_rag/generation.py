from collections.abc import Protocol, Sequence

from .grounding import Evidence, build_context


class Generator(Protocol):
    def generate(self, prompt: str) -> str: ...


def build_grounded_prompt(question: str, evidence: Sequence[Evidence]) -> str:
    context = build_context(list(evidence))
    return f"""Answer the question using only the supplied evidence.

Question:
{question}

Evidence:
{context}

Rules:
- Do not invent facts that are not supported by the evidence.
- Cite supporting evidence using its [E#] identifier.
- If the evidence is insufficient, say so clearly.
"""


class UnconfiguredGenerator:
    """Explicit placeholder until a real LLM provider is selected."""

    def generate(self, prompt: str) -> str:
        raise RuntimeError(
            "No LLM provider is configured. Implement the Generator protocol first."
        )
