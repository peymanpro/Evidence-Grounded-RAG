from dataclasses import dataclass

from .models import SearchResult


@dataclass(frozen=True)
class Evidence:
    citation_id: str
    result: SearchResult


def select_evidence(results: list[SearchResult], max_items: int = 5) -> list[Evidence]:
    if max_items <= 0:
        return []
    return [
        Evidence(citation_id=f"E{i}", result=result)
        for i, result in enumerate(results[:max_items], start=1)
    ]


def build_context(evidence: list[Evidence]) -> str:
    return "\n\n".join(
        f"[{item.citation_id}] {item.result.chunk.text}" for item in evidence
    )
