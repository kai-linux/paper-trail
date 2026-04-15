from paper_trail.ingest.embedder import Embedder
from paper_trail.store.qdrant import Store


def retrieve(
    query: str,
    embedder: Embedder,
    store: Store,
    top_k: int = 5,
    paper_id: str | None = None,
) -> list[dict]:
    qvec = embedder.embed_query(query)
    hits = store.search(qvec, top_k=top_k, paper_id=paper_id)
    return [{"score": h.score, **(h.payload or {})} for h in hits]
