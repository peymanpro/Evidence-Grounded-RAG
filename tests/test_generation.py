import pytest

from evidence_rag.generation import UnconfiguredGenerator, build_grounded_prompt
from evidence_rag.grounding import select_evidence
from evidence_rag.models import Chunk, SearchResult


def test_grounded_prompt_contains_question_and_citations() -> None:
    evidence = select_evidence(
        [SearchResult(Chunk("a", "doc", "Evidence text", 0), 1.0, "hybrid")]
    )

    prompt = build_grounded_prompt("What is this?", evidence)

    assert "What is this?" in prompt
    assert "[E1]" in prompt
    assert "Do not invent facts" in prompt


def test_unconfigured_generator_fails_explicitly() -> None:
    with pytest.raises(RuntimeError, match="No LLM provider"):
        UnconfiguredGenerator().generate("prompt")
