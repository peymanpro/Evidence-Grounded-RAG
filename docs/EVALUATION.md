# Evaluation

Evaluation is a first-class part of the project.

## Retrieval

The system will maintain a small, versioned question set with expected evidence. Retrieval experiments will compare semantic, lexical, hybrid, and reranked retrieval.

Useful measurements include Recall@k, Precision@k, MRR, and latency.

## Generation and grounding

Generation will be evaluated separately from retrieval. The benchmark will inspect whether claims are supported by retrieved evidence, citations point to supporting sources, the system abstains when evidence is insufficient, and answers remain faithful with distractor documents.

No quality metric will be claimed until its benchmark methodology is implemented.
