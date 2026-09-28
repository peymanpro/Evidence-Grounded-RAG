from dataclasses import dataclass
from math import log2

from .pipeline import RetrievalPipeline


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    relevant_chunk_ids: set[str]


@dataclass(frozen=True)
class RetrievalMetric:
    recall_at_k: float
    precision_at_k: float
    reciprocal_rank: float
    ndcg_at_k: float


def evaluate_retrieval(
    pipeline: RetrievalPipeline, cases: list[RetrievalCase], k: int = 5
) -> RetrievalMetric:
    if not cases or k <= 0:
        return RetrievalMetric(0.0, 0.0, 0.0, 0.0)

    recalls, precisions, reciprocal_ranks, ndcgs = [], [], [], []
    for case in cases:
        ids = [result.chunk.chunk_id for result in pipeline.search(case.query, k=k).results]
        relevant = case.relevant_chunk_ids
        hits = [chunk_id in relevant for chunk_id in ids]
        recalls.append(1.0 if relevant.intersection(ids) else 0.0)
        precisions.append(sum(hits) / k)
        rank = next((i for i, is_hit in enumerate(hits, start=1) if is_hit), None)
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)

        dcg = sum((1.0 if is_hit else 0.0) / log2(index + 1) for index, is_hit in enumerate(hits, 1))
        ideal_hits = min(len(relevant), k)
        idcg = sum(1.0 / log2(index + 1) for index in range(1, ideal_hits + 1))
        ndcgs.append(dcg / idcg if idcg else 0.0)

    return RetrievalMetric(
        recall_at_k=sum(recalls) / len(recalls),
        precision_at_k=sum(precisions) / len(precisions),
        reciprocal_rank=sum(reciprocal_ranks) / len(reciprocal_ranks),
        ndcg_at_k=sum(ndcgs) / len(ndcgs),
    )
