import uuid

from paper_trail.models import Chunk

CHARS_PER_TOKEN = 4
TARGET_CHUNK_TOKENS = 500
OVERLAP_TOKENS = 50

TARGET_CHARS = TARGET_CHUNK_TOKENS * CHARS_PER_TOKEN
OVERLAP_CHARS = OVERLAP_TOKENS * CHARS_PER_TOKEN

Block = tuple[int, str, str]


def _split_with_overlap(text: str) -> list[str]:
    if len(text) <= TARGET_CHARS:
        return [text]

    pieces: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + TARGET_CHARS, n)
        if end < n:
            search_floor = start + TARGET_CHARS // 2
            for delim in (". ", "\n", " "):
                idx = text.rfind(delim, search_floor, end)
                if idx > 0:
                    end = idx + len(delim)
                    break
        pieces.append(text[start:end].strip())
        if end >= n:
            break
        start = max(start + 1, end - OVERLAP_CHARS)
    return [p for p in pieces if p]


def chunk_blocks(paper_id: str, blocks: list[Block]) -> list[Chunk]:
    grouped: list[Block] = []
    for page, section, text in blocks:
        if (
            grouped
            and grouped[-1][0] == page
            and grouped[-1][1] == section
            and len(grouped[-1][2]) + len(text) + 2 < TARGET_CHARS
        ):
            p, s, t = grouped[-1]
            grouped[-1] = (p, s, f"{t}\n\n{text}")
        else:
            grouped.append((page, section, text))

    chunks: list[Chunk] = []
    chunk_index = 0
    for page, section, text in grouped:
        for piece in _split_with_overlap(text):
            chunks.append(
                Chunk(
                    id=str(uuid.uuid4()),
                    paper_id=paper_id,
                    text=piece,
                    section=section,
                    page_number=page,
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1
    return chunks
