from dataclasses import dataclass

from .pipeline import RetrievalPipeline


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    relevant_chunk_ids: set[str]


@dataclass(frozen=True)
class RetrievalMetric:
    recall_at_k: float
    reciprocal_rank: float


def evaluate_retrieval(
    pipeline: RetrievalPipeline, cases: list[RetrievalCase], k: int = 5
) -> RetrievalMetric:
    if not cases:
        return RetrievalMetric(0.0, 0.0)

    recalls = []
    reciprocal_ranks = []
    for case in cases:
        results = pipeline.search(case.query, k=k).results
        ids = [result.chunk.chunk_id for result in results]
        hits = case.relevant_chunk_ids.intersection(ids)
        recalls.append(1.0 if hits else 0.0)

        rank = next((i for i, chunk_id in enumerate(ids, start=1)
                     if chunk_id in case.relevant_chunk_ids), None)
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)

    return RetrievalMetric(
        recall_at_k=sum(recalls) / len(recalls),
        reciprocal_rank=sum(reciprocal_ranks) / len(reciprocal_ranks),
    )
