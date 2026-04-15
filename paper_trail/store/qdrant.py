import os

from qdrant_client import QdrantClient, models

from paper_trail.models import Chunk, Paper

COLLECTION = "papers"


class Store:
    def __init__(self, vector_size: int, url: str | None = None):
        self.vector_size = vector_size
        self.client = QdrantClient(url=url or os.getenv("QDRANT_URL", "http://localhost:6333"))
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        existing = {c.name for c in self.client.get_collections().collections}
        if COLLECTION in existing:
            info = self.client.get_collection(COLLECTION)
            existing_size = info.config.params.vectors.size
            if existing_size != self.vector_size:
                raise RuntimeError(
                    f"Qdrant collection '{COLLECTION}' has vector size {existing_size}, "
                    f"but the current embedder produces size {self.vector_size}. "
                    "Use a matching embedding model or recreate the collection."
                )
            return
        self.client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=self.vector_size, distance=models.Distance.COSINE),
        )
        self.client.create_payload_index(COLLECTION, "paper_id", models.PayloadSchemaType.KEYWORD)

    def upsert_chunks(self, chunks: list[Chunk], embeddings: list[list[float]], paper: Paper) -> None:
        points = [
            models.PointStruct(
                id=chunk.id,
                vector=vec,
                payload={
                    "paper_id": chunk.paper_id,
                    "paper_title": paper.title,
                    "text": chunk.text,
                    "section": chunk.section,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                },
            )
            for chunk, vec in zip(chunks, embeddings, strict=True)
        ]
        self.client.upsert(COLLECTION, points=points)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        paper_id: str | None = None,
    ) -> list[models.ScoredPoint]:
        flt = None
        if paper_id:
            flt = models.Filter(
                must=[models.FieldCondition(key="paper_id", match=models.MatchValue(value=paper_id))]
            )
        return self.client.query_points(
            collection_name=COLLECTION,
            query=query_vector,
            limit=top_k,
            query_filter=flt,
            with_payload=True,
        ).points

    def list_papers(self) -> list[dict]:
        seen: dict[str, dict] = {}
        offset = None
        while True:
            points, offset = self.client.scroll(
                COLLECTION, offset=offset, limit=200, with_payload=True
            )
            for p in points:
                pid = p.payload.get("paper_id")
                if pid and pid not in seen:
                    seen[pid] = {
                        "paper_id": pid,
                        "title": p.payload.get("paper_title", "Unknown"),
                    }
            if offset is None:
                break
        return list(seen.values())
