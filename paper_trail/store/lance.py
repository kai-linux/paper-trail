import os
from pathlib import Path

import lancedb
import pyarrow as pa

from paper_trail.models import Chunk, Paper

TABLE = "papers"
DEFAULT_PATH = "./paper-trail-data"


class Store:
    def __init__(self, vector_size: int, path: str | None = None):
        self.vector_size = vector_size
        self.path = Path(path or os.getenv("PAPER_TRAIL_DB_PATH", DEFAULT_PATH))
        self.path.mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(str(self.path))
        self.table = self._ensure_table()

    def _schema(self) -> pa.Schema:
        return pa.schema(
            [
                pa.field("id", pa.string()),
                pa.field("paper_id", pa.string()),
                pa.field("paper_title", pa.string()),
                pa.field("text", pa.string()),
                pa.field("section", pa.string()),
                pa.field("page_number", pa.int32()),
                pa.field("chunk_index", pa.int32()),
                pa.field("vector", pa.list_(pa.float32(), self.vector_size)),
            ]
        )

    def _ensure_table(self):
        if TABLE in self.db.table_names():
            tbl = self.db.open_table(TABLE)
            existing_dim = tbl.schema.field("vector").type.list_size
            if existing_dim != self.vector_size:
                raise RuntimeError(
                    f"LanceDB table '{TABLE}' has vector dim {existing_dim}, "
                    f"but the current embedder produces {self.vector_size}. "
                    "Use a matching embedding model or recreate the table."
                )
            return tbl
        return self.db.create_table(TABLE, schema=self._schema())

    def upsert_chunks(
        self, chunks: list[Chunk], embeddings: list[list[float]], paper: Paper
    ) -> None:
        rows = [
            {
                "id": chunk.id,
                "paper_id": chunk.paper_id,
                "paper_title": paper.title,
                "text": chunk.text,
                "section": chunk.section,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "vector": vec,
            }
            for chunk, vec in zip(chunks, embeddings, strict=True)
        ]
        self.table.add(rows)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        paper_id: str | None = None,
    ) -> list[dict]:
        q = self.table.search(query_vector).limit(top_k)
        if paper_id:
            q = q.where(f"paper_id = '{paper_id}'", prefilter=True)
        rows = q.to_list()
        for r in rows:
            r["score"] = -r.pop("_distance", 0.0)
            r.pop("vector", None)
        return rows

    def list_papers(self) -> list[dict]:
        arrow = self.table.to_arrow().select(["paper_id", "paper_title"])
        seen: dict[str, dict] = {}
        for row in arrow.to_pylist():
            pid = row["paper_id"]
            if pid and pid not in seen:
                seen[pid] = {"paper_id": pid, "title": row["paper_title"]}
        return list(seen.values())
