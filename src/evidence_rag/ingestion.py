from pathlib import Path

from .models import Document


def load_markdown(path: str | Path, document_id: str | None = None) -> Document:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    resolved_id = document_id or file_path.stem
    title = _title_from_markdown(text) or file_path.stem
    return Document(
        document_id=resolved_id,
        source=str(file_path),
        title=title,
        text=text,
        metadata={"format": "markdown"},
    )


def _title_from_markdown(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or None
    return None
