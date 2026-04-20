"""Parse epub and txt files, extracting chapters and cleaning content."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub


@dataclass
class Chapter:
    """Represents a single book chapter."""

    title: str
    content: str

    def __repr__(self) -> str:
        return f"Chapter(title={self.title!r}, chars={len(self.content)})"


# Tags whose inner text should be silently dropped (not read aloud)
_SKIP_TAGS = {"style", "script", "meta", "link", "head"}

# Regex patterns used by clean_text
_RE_URL = re.compile(r"https?://\S+|www\.\S+")
_RE_EMAIL = re.compile(r"\S+@\S+\.\S+")
_RE_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_RE_MULTI_NEWLINE = re.compile(r"\n{3,}")
_RE_NON_PRINTABLE = re.compile(
    r"[^\x20-\x7E\n\r\t"
    r"\u00C0-\u024F"   # Latin Extended
    r"\u2018\u2019\u201C\u201D\u2013\u2014\u2026"
    r"]"
)

# Chapter-heading pattern for plain-text books
_RE_CHAPTER_HEADING = re.compile(
    r"^(?:CHAPTER|Chapter|chapter|PART|Part|part)\s+"
    r"(?:[IVXLCDM]+|\d+|[A-Za-z]+)"
    r"(?:\s*[:.\-–—]?\s*.{0,80})?$",
    re.MULTILINE,
)


def clean_text(text: str) -> str:
    """Remove noise from extracted text and normalise punctuation."""
    text = _RE_URL.sub("", text)
    text = _RE_EMAIL.sub("", text)

    # Normalise Unicode punctuation to ASCII equivalents
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201C", '"').replace("\u201D", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "--")
    text = text.replace("\u2026", "...")

    text = _RE_NON_PRINTABLE.sub(" ", text)
    text = _RE_MULTI_SPACE.sub(" ", text)
    text = _RE_MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def _soup_text(soup: BeautifulSoup) -> str:
    """Extract readable text from a BeautifulSoup object, skipping noise tags."""
    for tag in soup.find_all(list(_SKIP_TAGS)):
        tag.decompose()
    return soup.get_text(separator="\n")


def parse_epub(file_path: str) -> List[Chapter]:
    """Parse an epub file and return a list of :class:`Chapter` objects."""
    book = epub.read_epub(file_path)
    chapters: List[Chapter] = []

    for item in book.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue

        soup = BeautifulSoup(item.get_content(), "lxml")

        # Determine chapter title
        heading = soup.find(["h1", "h2", "h3"])
        if heading:
            title = heading.get_text(strip=True)
        else:
            title = f"Chapter {len(chapters) + 1}"

        text = clean_text(_soup_text(soup))

        # Skip nearly-empty documents (cover pages, TOC entries, etc.)
        if len(text) < 50:
            continue

        chapters.append(Chapter(title=title, content=text))

    return chapters


def parse_txt(file_path: str) -> List[Chapter]:
    """Parse a plain-text file and return a list of :class:`Chapter` objects."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
        content = fh.read()

    content = clean_text(content)

    splits = list(_RE_CHAPTER_HEADING.finditer(content))

    if splits:
        chapters: List[Chapter] = []
        for i, match in enumerate(splits):
            title = match.group().strip()
            start = match.end()
            end = splits[i + 1].start() if i + 1 < len(splits) else len(content)
            chapter_text = content[start:end].strip()
            if len(chapter_text) >= 50:
                chapters.append(Chapter(title=title, content=chapter_text))
        return chapters

    # No chapter headings detected — treat the whole file as a single chapter
    return [Chapter(title="Chapter 1", content=content)]
