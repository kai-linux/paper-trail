import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

import fitz

from paper_trail.models import Paper

Block = tuple[int, str, str]  # (page_number, section, text)

_NAMED_SECTIONS = (
    "abstract",
    "introduction",
    "background",
    "related work",
    "preliminaries",
    "method",
    "methods",
    "methodology",
    "approach",
    "model",
    "experiments",
    "experimental setup",
    "evaluation",
    "results",
    "analysis",
    "discussion",
    "limitations",
    "conclusion",
    "conclusions",
    "future work",
    "references",
    "acknowledgments",
    "acknowledgements",
    "appendix",
)

_SECTION_PATTERNS = [
    re.compile(rf"^({'|'.join(_NAMED_SECTIONS)})\s*$", re.IGNORECASE),
    re.compile(r"^\d+(\.\d+){0,2}\.?\s+[A-Z][^\n]{2,80}$"),
    re.compile(r"^[IVX]+\.\s+[A-Z][^\n]{2,80}$"),
]


def _looks_like_heading(line: str) -> bool:
    line = line.strip()
    if len(line) < 3 or len(line) > 100:
        return False
    return any(p.match(line) for p in _SECTION_PATTERNS)


def _extract_title(doc: fitz.Document, fallback: str) -> str:
    meta_title = (doc.metadata or {}).get("title", "").strip()
    if meta_title and len(meta_title) > 3:
        return meta_title
    if len(doc) == 0:
        return fallback
    page = doc[0]
    spans: list[tuple[float, str]] = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if text and len(text) > 5:
                    spans.append((span.get("size", 0.0), text))
    if not spans:
        return fallback
    spans.sort(key=lambda s: s[0], reverse=True)
    return spans[0][1]


def _extract_authors(doc: fitz.Document) -> list[str]:
    raw = (doc.metadata or {}).get("author", "") or ""
    parts = re.split(r"[;,]| and ", raw)
    return [p.strip() for p in parts if p.strip()]


def parse_pdf(path: Path) -> tuple[Paper, list[Block]]:
    doc = fitz.open(path)
    try:
        title = _extract_title(doc, fallback=path.stem)
        authors = _extract_authors(doc)

        blocks: list[Block] = []
        current_section = "preamble"

        for page_idx, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            for raw_block in text.split("\n\n"):
                block = raw_block.strip()
                if not block:
                    continue
                first_line, _, rest = block.partition("\n")
                first_line = first_line.strip()
                rest = rest.strip()
                if _looks_like_heading(first_line):
                    current_section = first_line
                    if rest:
                        blocks.append((page_idx, current_section, rest))
                else:
                    blocks.append((page_idx, current_section, block))

        paper = Paper(
            id=str(uuid.uuid4()),
            title=title,
            authors=authors,
            filename=path.name,
            ingested_at=datetime.now(UTC),
            num_pages=len(doc),
            num_chunks=0,
        )
        return paper, blocks
    finally:
        doc.close()
