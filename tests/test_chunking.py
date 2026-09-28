from evidence_rag.chunking import chunk_document
from evidence_rag.models import Document


def test_chunk_document_preserves_source_metadata() -> None:
    document = Document(
        document_id="doc-1",
        source="notes/example.md",
        title="Example",
        text="First paragraph.\n\nSecond paragraph.",
        metadata={"type": "markdown"},
    )

    chunks = chunk_document(document, max_chars=30)

    assert len(chunks) == 2
    assert chunks[0].document_id == "doc-1"
    assert chunks[0].metadata["type"] == "markdown"
    assert chunks[0].position == 0
    assert chunks[1].position == 1


def test_chunk_document_rejects_invalid_size() -> None:
    document = Document("doc-1", "source", "Title", "text")

    try:
        chunk_document(document, max_chars=0)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("expected ValueError")
