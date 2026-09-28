from __future__ import annotations

import re

from .grounding import Evidence


_CITATION_RE = re.compile(r"\[E(\d+)\]")


def cited_evidence_ids(answer: str) -> set[str]:
    return {f"E{number}" for number in _CITATION_RE.findall(answer)}


def verify_citations(answer: str, evidence: list[Evidence]) -> tuple[bool, set[str]]:
    allowed = {item.citation_id for item in evidence}
    cited = cited_evidence_ids(answer)
    return cited.issubset(allowed), cited


def has_unsupported_citations(answer: str, evidence: list[Evidence]) -> bool:
    valid, _ = verify_citations(answer, evidence)
    return not valid
