import re
from collections.abc import Iterable

from .models import Chunk, Document


def _paragraphs(text: str) -> Iterable[str]:
    return (part.strip() for part in re.split(r"\n\s*\n", text) if part.strip())


def chunk_document(document: Document, max_chars: int = 1200) -> list[Chunk]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")

    chunks: list[Chunk] = []
    buffer = ""
    position = 0

    for paragraph in _paragraphs(document.text):
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if buffer and len(candidate) > max_chars:
            chunks.append(
                Chunk(
                    chunk_id=f"{document.document_id}:{position}",
                    document_id=document.document_id,
                    text=buffer,
                    position=position,
                    metadata=document.metadata,
                )
            )
            position += 1
            buffer = paragraph
        else:
            buffer = candidate

    if buffer:
        chunks.append(
            Chunk(
                chunk_id=f"{document.document_id}:{position}",
                document_id=document.document_id,
                text=buffer,
                position=position,
                metadata=document.metadata,
            )
        )

    return chunks
