from datetime import datetime

from pydantic import BaseModel


class Paper(BaseModel):
    id: str
    title: str
    authors: list[str]
    filename: str
    ingested_at: datetime
    num_pages: int
    num_chunks: int


class Chunk(BaseModel):
    id: str
    paper_id: str
    text: str
    section: str
    page_number: int
    chunk_index: int
    embedding: list[float] | None = None


class Citation(BaseModel):
    paper_id: str
    paper_title: str
    section: str
    page_number: int
    relevant_text: str = ""


class Answer(BaseModel):
    text: str
    citations: list[Citation] = []
