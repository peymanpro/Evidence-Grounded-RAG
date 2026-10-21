from evidence_rag.evaluation import RetrievalCase, evaluate_retrieval
from evidence_rag.grounding import build_context, select_evidence
from evidence_rag.models import Chunk
from evidence_rag.pipeline import RetrievalPipeline


chunks = [
    Chunk(
        "rate-limit-1",
        "rate-limit",
        "Distributed rate limiting can coordinate request quotas across application instances.",
        0,
    ),
    Chunk(
        "search-1",
        "search",
        "Hybrid retrieval combines lexical and semantic signals.",
        0,
    ),
]

pipeline = RetrievalPipeline(chunks)
response = pipeline.search("How can distributed rate limiting coordinate quotas?", k=2)
evidence = select_evidence(response.results)

print("Retrieved evidence:")
print(build_context(evidence))

benchmark = [
    RetrievalCase(
        "How can distributed rate limiting coordinate quotas?",
        {"rate-limit-1"},
    )
]
print("Evaluation:", evaluate_retrieval(pipeline, benchmark))
