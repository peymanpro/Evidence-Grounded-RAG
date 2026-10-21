from pathlib import Path

from .chunking import chunk_document
from .ingestion import load_markdown
from .models import Chunk


def load_corpus(corpus_dir: str | Path, max_chars: int = 1200) -> list[Chunk]:
    """Load every Markdown document under a corpus directory and chunk it deterministically."""
    root = Path(corpus_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Corpus directory does not exist: {root}")

    markdown_paths = sorted(path for path in root.rglob("*.md") if path.is_file())
    if not markdown_paths:
        raise ValueError(f"No Markdown documents found in corpus directory: {root}")

    chunks: list[Chunk] = []
    for path in markdown_paths:
        relative_path = path.relative_to(root)
        document_id = relative_path.with_suffix("").as_posix()
        document = load_markdown(path, document_id=document_id)
        chunks.extend(chunk_document(document, max_chars=max_chars))

    if not chunks:
        raise ValueError(f"Markdown corpus contains no extractable text: {root}")

    return chunks
