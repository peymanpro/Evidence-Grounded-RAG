from evidence_rag.grounding import select_evidence
from evidence_rag.models import Chunk, SearchResult
from evidence_rag.verification import verify_citations


def test_citation_verification_rejects_unknown_ids() -> None:
    evidence = select_evidence([SearchResult(Chunk("c1", "d1", "text", 0), 1.0, "hybrid")])
    valid, cited = verify_citations("Answer [E2]", evidence)
    assert not valid
    assert cited == {"E2"}


def test_citation_verification_accepts_known_ids() -> None:
    evidence = select_evidence([SearchResult(Chunk("c1", "d1", "text", 0), 1.0, "hybrid")])
    valid, cited = verify_citations("Answer [E1]", evidence)
    assert valid
    assert cited == {"E1"}
