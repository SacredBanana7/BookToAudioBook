"""Tests for src/book_parser.py"""

import os
import tempfile

import pytest

from src.book_parser import Chapter, clean_text, parse_txt


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------


def test_clean_text_removes_http_urls():
    result = clean_text("Visit https://example.com for details.")
    assert "https://" not in result
    assert "details" in result


def test_clean_text_removes_www_urls():
    result = clean_text("See www.example.com for info.")
    assert "www." not in result


def test_clean_text_removes_emails():
    result = clean_text("Contact us at support@example.com today.")
    assert "@" not in result
    assert "today" in result


def test_clean_text_normalises_curly_quotes():
    result = clean_text("\u201CHello\u201D she said")
    assert '"Hello"' in result


def test_clean_text_normalises_smart_apostrophe():
    result = clean_text("It\u2019s a fine day")
    assert "It's a fine day" in result


def test_clean_text_normalises_ellipsis():
    result = clean_text("Wait\u2026 what?")
    assert "..." in result


def test_clean_text_collapses_multiple_blank_lines():
    result = clean_text("First\n\n\n\n\nSecond")
    assert "\n\n\n" not in result
    assert "First" in result
    assert "Second" in result


def test_clean_text_collapses_multiple_spaces():
    result = clean_text("Hello     world")
    assert "  " not in result


# ---------------------------------------------------------------------------
# parse_txt — single chapter (no headings)
# ---------------------------------------------------------------------------


def _write_tmp(content: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        fh.write(content)
    return fh.name


def test_parse_txt_no_headings_returns_one_chapter():
    path = _write_tmp(
        "This is the beginning of the story.\n\n"
        "It continues here with more events and adventures for everyone."
    )
    try:
        chapters = parse_txt(path)
        assert len(chapters) == 1
        assert "beginning" in chapters[0].content
    finally:
        os.unlink(path)


def test_parse_txt_detects_chapter_headings():
    path = _write_tmp(
        "Chapter 1\n\n"
        "This is the first chapter with more than enough content to pass "
        "the minimum length filter that is applied during parsing.\n\n"
        "Chapter 2\n\n"
        "This is the second chapter which also contains more than enough "
        "content to pass the minimum length filter during parsing."
    )
    try:
        chapters = parse_txt(path)
        assert len(chapters) == 2
        assert "first chapter" in chapters[0].content
        assert "second chapter" in chapters[1].content
    finally:
        os.unlink(path)


def test_parse_txt_chapter_titles_captured():
    path = _write_tmp(
        "Chapter 1\n\n"
        "Content of the first chapter goes here and has enough length to pass "
        "the minimum character threshold that is applied during parsing.\n\n"
        "Chapter 2\n\n"
        "Content of the second chapter is also long enough to be retained "
        "and stored correctly in the list of parsed chapter objects."
    )
    try:
        chapters = parse_txt(path)
        assert chapters[0].title == "Chapter 1"
        assert chapters[1].title == "Chapter 2"
    finally:
        os.unlink(path)


def test_parse_txt_skips_short_chapters():
    path = _write_tmp(
        "Chapter 1\n\nShort.\n\n"
        "Chapter 2\n\n"
        "This second chapter has enough content to survive the length filter applied."
    )
    try:
        chapters = parse_txt(path)
        # Chapter 1 body is too short; only chapter 2 should survive
        assert all("second chapter" in ch.content for ch in chapters)
    finally:
        os.unlink(path)


def test_chapter_repr():
    ch = Chapter(title="Intro", content="Hello world")
    assert "Intro" in repr(ch)
    assert "chars=11" in repr(ch)
