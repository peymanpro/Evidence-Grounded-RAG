from evidence_rag.grounding import build_context, select_evidence
from evidence_rag.models import Chunk, SearchResult


def test_context_contains_stable_citation_ids() -> None:
    result = SearchResult(Chunk("a", "doc", "The answer is here.", 0), 0.9, "hybrid")

    evidence = select_evidence([result])

    assert build_context(evidence) == "[E1] The answer is here."
