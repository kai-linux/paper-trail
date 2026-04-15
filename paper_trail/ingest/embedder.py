import os
from typing import Protocol


class Embedder(Protocol):
    dim: int
    model: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, query: str) -> list[float]: ...


_VOYAGE_DIMS = {
    "voyage-3-large": 1024,
    "voyage-3": 1024,
    "voyage-3-lite": 512,
    "voyage-code-3": 1024,
}

_OPENAI_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


class VoyageEmbedder:
    def __init__(self, model: str = "voyage-3-large"):
        import voyageai

        self.client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
        self.model = model
        self.dim = _VOYAGE_DIMS.get(model, 1024)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.client.embed(texts, model=self.model, input_type="document").embeddings

    def embed_query(self, query: str) -> list[float]:
        return self.client.embed([query], model=self.model, input_type="query").embeddings[0]


class OpenAIEmbedder:
    def __init__(self, model: str = "text-embedding-3-small"):
        from openai import OpenAI

        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model
        self.dim = _OPENAI_DIMS.get(model, 1536)

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.embeddings.create(input=texts, model=self.model)
        return [d.embedding for d in resp.data]

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query])[0]


def get_embedder() -> Embedder:
    provider = os.getenv("PAPER_TRAIL_EMBED_PROVIDER", "voyage").lower()
    model = os.getenv("PAPER_TRAIL_EMBED_MODEL")
    if provider == "voyage":
        return VoyageEmbedder(model or "voyage-3-large")
    if provider == "openai":
        return OpenAIEmbedder(model or "text-embedding-3-small")
    raise ValueError(f"Unknown embedding provider: {provider!r} (expected 'voyage' or 'openai')")
