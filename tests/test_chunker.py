from paper_trail.ingest.chunker import (
    OVERLAP_CHARS,
    TARGET_CHARS,
    _split_with_overlap,
    chunk_blocks,
)


def test_short_text_is_single_chunk():
    pieces = _split_with_overlap("a short paragraph.")
    assert pieces == ["a short paragraph."]


def test_long_text_is_split_with_overlap():
    text = ("Sentence number {n}. " * 1000).format(n=1)
    pieces = _split_with_overlap(text)
    assert len(pieces) > 1
    for p in pieces:
        assert len(p) <= TARGET_CHARS + 16  # +slack for boundary search
    joined = " ".join(pieces)
    assert text.strip().split()[0] in joined
    assert text.strip().split()[-1] in joined


def test_chunk_blocks_preserves_section_and_page():
    blocks = [
        (1, "Introduction", "Intro paragraph one."),
        (1, "Introduction", "Intro paragraph two."),
        (2, "Methods", "Methods paragraph."),
    ]
    chunks = chunk_blocks(paper_id="paper-1", blocks=blocks)
    assert all(c.paper_id == "paper-1" for c in chunks)
    sections = {c.section for c in chunks}
    assert sections == {"Introduction", "Methods"}
    pages = {c.page_number for c in chunks}
    assert pages == {1, 2}
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_chunk_blocks_merges_small_same_section():
    blocks = [
        (1, "Methods", "First small paragraph."),
        (1, "Methods", "Second small paragraph."),
    ]
    chunks = chunk_blocks("p", blocks)
    assert len(chunks) == 1
    assert "First" in chunks[0].text and "Second" in chunks[0].text


def test_overlap_constants_sane():
    assert OVERLAP_CHARS < TARGET_CHARS
