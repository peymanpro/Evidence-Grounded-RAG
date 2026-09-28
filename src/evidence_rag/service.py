from __future__ import annotations

from dataclasses import dataclass

from .generation import Generator, build_grounded_prompt
from .grounding import Evidence, select_evidence
from .models import Chunk
from .pipeline import RetrievalPipeline
from .reranking import LexicalReranker


@dataclass(frozen=True)
class Answer:
    question: str
    answer: str
    evidence: list[Evidence]


class EvidenceRAGService:
    def __init__(
        self,
        chunks: list[Chunk],
        generator: Generator,
        embedder=None,
        reranker: LexicalReranker | None = None,
    ) -> None:
        self.retrieval = RetrievalPipeline(chunks, embedder=embedder)
        self.generator = generator
        self.reranker = reranker or LexicalReranker()

    def answer(self, question: str, retrieval_k: int = 12, evidence_k: int = 5) -> Answer:
        candidates = self.retrieval.search(question, k=retrieval_k).results
        ranked = self.reranker.rerank(question, candidates, k=evidence_k)
        evidence = select_evidence(ranked, max_items=evidence_k)
        if not evidence:
            return Answer(question, "I do not have enough evidence to answer this question.", [])
        prompt = build_grounded_prompt(question, evidence)
        return Answer(question, self.generator.generate(prompt), evidence)
