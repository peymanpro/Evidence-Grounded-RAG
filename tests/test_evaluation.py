from evidence_rag.evaluation import RetrievalCase, evaluate_retrieval
from evidence_rag.models import Chunk
from evidence_rag.pipeline import RetrievalPipeline


def test_retrieval_evaluation_reports_hit_and_rank() -> None:
    chunks = [
        Chunk("a", "doc", "pgvector stores embeddings", 0),
        Chunk("b", "doc", "unrelated cache information", 1),
    ]

    metric = evaluate_retrieval(
        RetrievalPipeline(chunks),
        [RetrievalCase("where are embeddings stored?", {"a"})],
        k=2,
    )

    assert metric.recall_at_k == 1.0
    assert metric.reciprocal_rank > 0
