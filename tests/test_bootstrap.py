import pytest
from pathlib import Path

from evidence_rag.bootstrap import load_corpus


def test_load_corpus_recursively_assigns_stable_document_ids(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    nested = corpus / "nested"
    nested.mkdir(parents=True)
    (corpus / "guide.md").write_text("# Guide\n\nThe API uses evidence.", encoding="utf-8")
    (nested / "retrieval.md").write_text(
        "# Retrieval\n\nHybrid search combines lexical and semantic signals.",
        encoding="utf-8",
    )
    (corpus / "ignore.txt").write_text("Not a Markdown document.", encoding="utf-8")

    chunks = load_corpus(corpus)

    assert [chunk.document_id for chunk in chunks] == ["guide", "nested/retrieval"]
    assert chunks[0].text.startswith("# Guide")
    assert chunks[1].text.startswith("# Retrieval")


def test_load_corpus_requires_existing_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Corpus directory does not exist"):
        load_corpus(tmp_path / "missing")


def test_load_corpus_requires_markdown_documents(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "notes.txt").write_text("Not Markdown.", encoding="utf-8")

    with pytest.raises(ValueError, match="No Markdown documents found"):
        load_corpus(corpus)
