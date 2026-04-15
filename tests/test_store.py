import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from paper_trail.models import Chunk, Paper
from paper_trail.store.lance import Store

DIM = 8


def _make_paper(title: str = "Test Paper") -> Paper:
    return Paper(
        id=str(uuid.uuid4()),
        title=title,
        authors=["A. Author", "B. Author"],
        filename=f"{title.lower().replace(' ', '_')}.pdf",
        ingested_at=datetime.now(UTC),
        num_pages=10,
        num_chunks=2,
    )


def _make_chunks(paper_id: str) -> list[Chunk]:
    return [
        Chunk(
            id=str(uuid.uuid4()),
            paper_id=paper_id,
            text="The first chunk discusses the methodology.",
            section="Methods",
            page_number=3,
            chunk_index=0,
        ),
        Chunk(
            id=str(uuid.uuid4()),
            paper_id=paper_id,
            text="The second chunk reports experimental results.",
            section="Results",
            page_number=5,
            chunk_index=1,
        ),
    ]


def _vecs(n: int, val: float) -> list[list[float]]:
    return [[val] * DIM for _ in range(n)]


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(vector_size=DIM, path=str(tmp_path))


def test_upsert_and_search_returns_chunks(store: Store):
    paper = _make_paper()
    chunks = _make_chunks(paper.id)
    store.upsert_chunks(chunks, _vecs(len(chunks), 1.0), paper)

    hits = store.search([1.0] * DIM, top_k=2)
    assert len(hits) == 2
    sections = {h["section"] for h in hits}
    assert sections == {"Methods", "Results"}
    assert all("vector" not in h for h in hits)
    assert all("score" in h for h in hits)


def test_search_filters_by_paper_id(store: Store):
    p1, p2 = _make_paper("Paper One"), _make_paper("Paper Two")
    store.upsert_chunks(_make_chunks(p1.id), _vecs(2, 1.0), p1)
    store.upsert_chunks(_make_chunks(p2.id), _vecs(2, 0.5), p2)

    hits = store.search([1.0] * DIM, top_k=10, paper_id=p1.id)
    assert len(hits) == 2
    assert {h["paper_id"] for h in hits} == {p1.id}


def test_list_papers_returns_full_metadata(store: Store):
    paper = _make_paper("Indexed Paper")
    store.upsert_chunks(_make_chunks(paper.id), _vecs(2, 1.0), paper)

    papers = store.list_papers()
    assert len(papers) == 1
    p = papers[0]
    assert p["title"] == "Indexed Paper"
    assert p["authors"] == ["A. Author", "B. Author"]
    assert p["num_pages"] == 10


def test_find_paper_by_prefix(store: Store):
    paper = _make_paper()
    store.upsert_chunks(_make_chunks(paper.id), _vecs(2, 1.0), paper)
    found = store.find_paper(paper.id[:8])
    assert found is not None
    assert found["paper_id"] == paper.id
    assert store.find_paper("nonexistent") is None


def test_delete_removes_paper_and_chunks(store: Store):
    paper = _make_paper()
    store.upsert_chunks(_make_chunks(paper.id), _vecs(2, 1.0), paper)

    store.delete_paper(paper.id)
    assert store.list_papers() == []
    assert store.search([1.0] * DIM, top_k=10) == []


def test_vector_dim_mismatch_raises(tmp_path: Path):
    Store(vector_size=DIM, path=str(tmp_path))
    with pytest.raises(RuntimeError, match="vector dim"):
        Store(vector_size=DIM + 1, path=str(tmp_path))
