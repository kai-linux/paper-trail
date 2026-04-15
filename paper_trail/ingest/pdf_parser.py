import re
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import fitz

from paper_trail.models import Paper

Block = tuple[int, str, str]

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
    re.compile(rf"^({'|'.join(_NAMED_SECTIONS)})[\s.:]*$", re.IGNORECASE),
    re.compile(r"^\d+(\.\d+){0,2}\.?\s+[A-Z][^\n]{4,80}$"),
]

_NOISE_PATTERNS = [
    re.compile(r"^arxiv:\d", re.IGNORECASE),
    re.compile(r"^doi[:\s]", re.IGNORECASE),
    re.compile(r"^https?://"),
    re.compile(r"^(proceedings|journal|volume|vol\.)\s", re.IGNORECASE),
    re.compile(r"^\d{1,3}\s*$"),
    re.compile(r"^(department|institute|university|laboratory|cern|école)\b", re.IGNORECASE),
    re.compile(r"^©|^copyright", re.IGNORECASE),
    re.compile(r"^[A-Z]\.\s*[A-Z][a-z]+(,\s*[A-Z]\.\s*[A-Z][a-z]+)*"),
    re.compile(r"\bcollaboration\b", re.IGNORECASE),
    re.compile(r"\b(et al\.|for the [A-Z])"),
]


def _is_noise(text: str) -> bool:
    return any(p.search(text) for p in _NOISE_PATTERNS)


def _normalize(s: str) -> str:
    return " ".join(s.split()).lower()


def _looks_like_heading(line: str, font_headings: set[str]) -> bool:
    line = line.strip()
    if len(line) < 3 or len(line) > 100:
        return False
    if _is_noise(line):
        return False
    if any(p.match(line) for p in _SECTION_PATTERNS):
        return True
    return _normalize(line) in font_headings


def _font_heading_lines(doc: fitz.Document) -> set[str]:
    """Lines that look like headings based on font size or bold weight.

    Recurring lines (page headers / running titles) are filtered out — if a
    candidate appears on more than 40% of pages, it's almost certainly a
    page header, not a section heading.
    """
    n_pages = len(doc)
    page_appearances: Counter[str] = Counter()
    candidates: set[str] = set()

    for page in doc:
        page_seen: set[str] = set()
        records: list[tuple[str, float, bool]] = []
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(s.get("text", "") for s in spans).strip()
                if not text:
                    continue
                dominant = max(spans, key=lambda s: len(s.get("text", "")))
                size = float(dominant.get("size", 0.0))
                bold = bool(dominant.get("flags", 0) & 16)
                records.append((text, size, bold))

        if not records:
            continue

        size_chars: Counter[int] = Counter()
        for text, size, _ in records:
            size_chars[round(size)] += len(text)
        body_size = size_chars.most_common(1)[0][0]

        for text, size, bold in records:
            if not (3 <= len(text) <= 100):
                continue
            if not text[0].isalnum():
                continue
            if _is_noise(text):
                continue
            if size > body_size * 1.15 or (bold and size >= body_size):
                norm = _normalize(text)
                candidates.add(norm)
                page_seen.add(norm)
        for norm in page_seen:
            page_appearances[norm] += 1

    if n_pages <= 2:
        return candidates
    cutoff = max(2, int(0.4 * n_pages))
    return {c for c in candidates if page_appearances[c] < cutoff}


def _extract_title(doc: fitz.Document, fallback: str) -> str:
    meta_title = (doc.metadata or {}).get("title", "").strip()
    if meta_title and len(meta_title) > 3:
        return meta_title
    if len(doc) == 0:
        return fallback
    page = doc[0]
    spans: list[tuple[float, str]] = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if text and len(text) > 5:
                    spans.append((float(span.get("size", 0.0)), text))
    if not spans:
        return fallback
    spans.sort(key=lambda s: s[0], reverse=True)
    return spans[0][1]


def _extract_authors(doc: fitz.Document) -> list[str]:
    raw = (doc.metadata or {}).get("author", "") or ""
    parts = re.split(r"[;,]| and ", raw)
    return [p.strip() for p in parts if p.strip()]


def _block_text(block: dict) -> tuple[str, list[str]]:
    line_texts: list[str] = []
    for line in block.get("lines", []):
        spans = line.get("spans", [])
        if not spans:
            continue
        line_texts.append("".join(s.get("text", "") for s in spans))
    return "\n".join(line_texts).strip(), line_texts


def parse_pdf(path: Path) -> tuple[Paper, list[Block]]:
    doc = fitz.open(path)
    try:
        title = _extract_title(doc, fallback=path.stem)
        authors = _extract_authors(doc)
        font_headings = _font_heading_lines(doc)

        blocks: list[Block] = []
        current_section = "preamble"

        for page_idx, page in enumerate(doc, start=1):
            page_dict = page.get_text("dict")
            for raw_block in page_dict.get("blocks", []):
                if raw_block.get("type") != 0:
                    continue
                text, line_texts = _block_text(raw_block)
                if not text:
                    continue
                first_line = (line_texts[0] if line_texts else text).strip()
                if _looks_like_heading(first_line, font_headings):
                    current_section = first_line
                    rest = "\n".join(line_texts[1:]).strip()
                    if rest:
                        blocks.append((page_idx, current_section, rest))
                else:
                    blocks.append((page_idx, current_section, text))

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
