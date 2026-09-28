from __future__ import annotations

import json
import os
from collections.abc import Sequence
from urllib.request import Request, urlopen

from .embeddings import Embedder
from .generation import Generator


class OpenAICompatibleEmbedder:
    """HTTP adapter for OpenAI-compatible embedding APIs."""

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    @classmethod
    def from_env(cls) -> "OpenAICompatibleEmbedder":
        return cls(
            api_key=os.environ["RAG_API_KEY"],
            model=os.environ["RAG_EMBEDDING_MODEL"],
            base_url=os.getenv("RAG_API_BASE_URL", "https://api.openai.com/v1"),
        )

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        payload = json.dumps({"model": self.model, "input": list(texts)}).encode()
        request = Request(
            f"{self.base_url}/embeddings",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read())
        return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]


class OpenAICompatibleGenerator:
    """HTTP adapter for OpenAI-compatible chat-completion APIs."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        temperature: float = 0.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature

    @classmethod
    def from_env(cls) -> "OpenAICompatibleGenerator":
        return cls(
            api_key=os.environ["RAG_API_KEY"],
            model=os.environ["RAG_LLM_MODEL"],
            base_url=os.getenv("RAG_API_BASE_URL", "https://api.openai.com/v1"),
        )

    def generate(self, prompt: str) -> str:
        payload = json.dumps({
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": "You answer from supplied evidence and cite it."},
                {"role": "user", "content": prompt},
            ],
        }).encode()
        request = Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=120) as response:
            data = json.loads(response.read())
        return data["choices"][0]["message"]["content"]


def configured_generator() -> Generator:
    return OpenAICompatibleGenerator.from_env()
