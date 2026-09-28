from pathlib import Path

from evidence_rag.ingestion import load_markdown


def test_load_markdown_extracts_title_and_metadata(tmp_path: Path) -> None:
    source = tmp_path / "guide.md"
    source.write_text("# Retrieval Guide\n\nEvidence first.", encoding="utf-8")

    document = load_markdown(source)

    assert document.document_id == "guide"
    assert document.title == "Retrieval Guide"
    assert document.text.startswith("# Retrieval Guide")
    assert document.metadata["format"] == "markdown"
