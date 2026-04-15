import os
from datetime import UTC, datetime
from pathlib import Path

import lancedb
import pyarrow as pa

from paper_trail.models import Chunk, Paper

CHUNKS_TABLE = "chunks"
PAPERS_TABLE = "papers"
DEFAULT_PATH = "./paper-trail-data"


class Store:
    def __init__(self, vector_size: int, path: str | None = None):
        self.vector_size = vector_size
        self.path = Path(path or os.getenv("PAPER_TRAIL_DB_PATH", DEFAULT_PATH))
        self.path.mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(str(self.path))
        self.chunks = self._ensure_chunks_table()
        self.papers = self._ensure_papers_table()

    def _chunks_schema(self) -> pa.Schema:
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

    def _papers_schema(self) -> pa.Schema:
        return pa.schema(
            [
                pa.field("paper_id", pa.string()),
                pa.field("title", pa.string()),
                pa.field("authors", pa.list_(pa.string())),
                pa.field("filename", pa.string()),
                pa.field("ingested_at", pa.timestamp("us", tz="UTC")),
                pa.field("num_pages", pa.int32()),
                pa.field("num_chunks", pa.int32()),
            ]
        )

    def _ensure_chunks_table(self):
        if CHUNKS_TABLE in self.db.list_tables().tables:
            tbl = self.db.open_table(CHUNKS_TABLE)
            existing_dim = tbl.schema.field("vector").type.list_size
            if existing_dim != self.vector_size:
                raise RuntimeError(
                    f"LanceDB table '{CHUNKS_TABLE}' has vector dim {existing_dim}, "
                    f"but the current embedder produces {self.vector_size}. "
                    "Use a matching embedding model or recreate the table."
                )
            return tbl
        return self.db.create_table(CHUNKS_TABLE, schema=self._chunks_schema())

    def _ensure_papers_table(self):
        if PAPERS_TABLE in self.db.list_tables().tables:
            return self.db.open_table(PAPERS_TABLE)
        return self.db.create_table(PAPERS_TABLE, schema=self._papers_schema())

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
        self.chunks.add(rows)
        self.papers.add(
            [
                {
                    "paper_id": paper.id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "filename": paper.filename,
                    "ingested_at": paper.ingested_at.astimezone(UTC),
                    "num_pages": paper.num_pages,
                    "num_chunks": paper.num_chunks,
                }
            ]
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        paper_id: str | None = None,
    ) -> list[dict]:
        q = self.chunks.search(query_vector).limit(top_k)
        if paper_id:
            q = q.where(f"paper_id = '{paper_id}'", prefilter=True)
        rows = q.to_list()
        for r in rows:
            r["score"] = -r.pop("_distance", 0.0)
            r.pop("vector", None)
        return rows

    def list_papers(self) -> list[dict]:
        return self.papers.to_arrow().to_pylist()

    def find_paper(self, paper_id_prefix: str) -> dict | None:
        for row in self.papers.to_arrow().to_pylist():
            if row["paper_id"].startswith(paper_id_prefix):
                return row
        return None

    def delete_paper(self, paper_id: str) -> None:
        self.chunks.delete(f"paper_id = '{paper_id}'")
        self.papers.delete(f"paper_id = '{paper_id}'")
