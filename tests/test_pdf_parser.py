from paper_trail.ingest.pdf_parser import _looks_like_heading


def test_named_section_matches():
    assert _looks_like_heading("Abstract", set())
    assert _looks_like_heading("INTRODUCTION", set())
    assert _looks_like_heading("Methods", set())
    assert _looks_like_heading("References", set())


def test_numbered_section_matches():
    assert _looks_like_heading("3. Methods", set())
    assert _looks_like_heading("3.2 Architecture", set())
    assert _looks_like_heading("4.1.2 Loss function", set())


def test_body_text_does_not_match():
    assert not _looks_like_heading("the quick brown fox jumps over the lazy dog.", set())
    assert not _looks_like_heading("In this paper we propose a new approach.", set())


def test_too_short_or_long_does_not_match():
    assert not _looks_like_heading("ab", set())
    long_line = "This is a very long line " * 10
    assert not _looks_like_heading(long_line, set())


def test_font_heading_set_matches():
    headings = {"section 3: methods"}
    assert _looks_like_heading("Section 3: Methods", headings)
    assert not _looks_like_heading("Section 3: Methods", set())
