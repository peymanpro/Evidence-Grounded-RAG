from evidence_rag.embeddings import HashingEmbedder


def test_hashing_embedder_is_normalized_and_deterministic() -> None:
    embedder = HashingEmbedder(64)

    first = embedder.embed(["vector search"])[0]
    second = embedder.embed(["vector search"])[0]

    assert first == second
    assert abs(sum(value * value for value in first) - 1.0) < 1e-9
