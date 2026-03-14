from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import importlib
from pathlib import Path
import re
from typing import Any

from bs4 import BeautifulSoup


SUPPORTED_EXTENSIONS = {".md", ".pdf", ".html", ".htm", ".txt"}


@dataclass
class ParsedDocument:
    title: str
    content: str
    metadata: dict[str, Any]
    chunks: list[str]


class DocumentParser:
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be >= 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse(self, file_path: str) -> ParsedDocument:
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".md":
            return self.parse_markdown(file_path)
        if suffix == ".pdf":
            return self.parse_pdf(file_path)
        if suffix in {".html", ".htm"}:
            return self.parse_html(file_path)
        if suffix == ".txt":
            return self.parse_text(file_path)

        raise ValueError(f"Unsupported file format: {suffix}")

    def parse_markdown(self, file_path: str) -> ParsedDocument:
        path = Path(file_path)
        markdown_text = path.read_text(encoding="utf-8", errors="ignore")
        markdown_text = self._strip_frontmatter(markdown_text)
        content = self._markdown_to_structured_text(markdown_text)
        return self._build_document(path, "markdown", content)

    def parse_pdf(self, file_path: str) -> ParsedDocument:
        pdfplumber = importlib.import_module("pdfplumber")

        path = Path(file_path)
        pages: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                page_text = self._normalize_text(page_text)
                if page_text:
                    pages.append(page_text)

        content = "\n\n".join(pages).strip()
        return self._build_document(path, "pdf", content)

    def parse_html(self, file_path: str) -> ParsedDocument:
        path = Path(file_path)
        html = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")

        for tag_name in ["script", "style", "nav", "footer", "noscript"]:
            for node in soup.find_all(tag_name):
                node.decompose()

        extracted = soup.get_text(separator="\n")
        content = self._normalize_text(extracted)

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else path.stem
        return self._build_document(path, "html", content, title=title)

    def parse_text(self, file_path: str) -> ParsedDocument:
        path = Path(file_path)
        text = path.read_text(encoding="utf-8", errors="ignore")
        content = self._normalize_text(text)
        return self._build_document(path, "text", content)

    def _chunk_text(self, text: str) -> list[str]:
        normalized = self._normalize_text(text)
        if not normalized:
            return []

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", normalized) if p.strip()]
        raw_chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            units = [paragraph]
            if len(paragraph) > self.chunk_size:
                units = self._split_by_sentence(paragraph)

            for unit in units:
                unit = unit.strip()
                if not unit:
                    continue

                candidate = unit if not current else f"{current}\n\n{unit}"
                if len(candidate) <= self.chunk_size:
                    current = candidate
                    continue

                if current:
                    raw_chunks.append(current.strip())
                if len(unit) > self.chunk_size:
                    raw_chunks.extend(self._split_hard(unit))
                    current = ""
                else:
                    current = unit

        if current:
            raw_chunks.append(current.strip())

        if self.chunk_overlap <= 0:
            return raw_chunks

        overlapped_chunks: list[str] = []
        for idx, chunk in enumerate(raw_chunks):
            if idx == 0:
                overlapped_chunks.append(chunk)
                continue

            previous = raw_chunks[idx - 1]
            overlap_text = previous[-self.chunk_overlap :].strip()
            if overlap_text:
                combined = f"{overlap_text}\n\n{chunk}".strip()
                overlapped_chunks.append(combined)
            else:
                overlapped_chunks.append(chunk)

        return overlapped_chunks

    def parse_directory(
        self,
        dir_path: str,
        extensions: list[str] | None = None,
    ) -> list[ParsedDocument]:
        base = Path(dir_path)
        if not base.exists() or not base.is_dir():
            raise ValueError(f"Invalid directory path: {dir_path}")

        normalized_exts = (
            {
                ext.lower() if ext.startswith(".") else f".{ext.lower()}"
                for ext in extensions
            }
            if extensions
            else SUPPORTED_EXTENSIONS
        )

        parsed: list[ParsedDocument] = []
        for file_path in base.rglob("*"):
            if (
                not file_path.is_file()
                or file_path.suffix.lower() not in normalized_exts
            ):
                continue
            parsed.append(self.parse(str(file_path)))

        return parsed

    def _build_document(
        self,
        path: Path,
        file_format: str,
        content: str,
        title: str | None = None,
    ) -> ParsedDocument:
        clean_content = self._normalize_text(content)
        chunks = self._chunk_text(clean_content)
        metadata = {
            "source_path": str(path.resolve()),
            "format": file_format,
            "parsed_at": datetime.now(timezone.utc).isoformat(),
            "word_count": len(clean_content.split()),
        }
        return ParsedDocument(
            title=title or path.stem,
            content=clean_content,
            metadata=metadata,
            chunks=chunks,
        )

    @staticmethod
    def _strip_frontmatter(markdown_text: str) -> str:
        if not markdown_text.startswith("---"):
            return markdown_text
        return re.sub(r"\A---\s*\n.*?\n---\s*\n", "", markdown_text, flags=re.DOTALL)

    def _markdown_to_structured_text(self, markdown_text: str) -> str:
        lines: list[str] = []
        for raw_line in markdown_text.splitlines():
            line = raw_line.rstrip()
            heading = re.match(r"^(#{1,6})\s+(.*)$", line)
            if heading:
                level = len(heading.group(1))
                heading_text = heading.group(2).strip()
                lines.append(f"{'>' * level} {heading_text}")
                continue

            line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)
            line = re.sub(r"\[([^\]]+)\]\(([^)]*)\)", r"\1", line)
            line = re.sub(r"[`*_~]", "", line)
            lines.append(line)

        return self._normalize_text("\n".join(lines))

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _split_by_sentence(self, paragraph: str) -> list[str]:
        sentences = [
            s.strip() for s in re.split(r"(?<=[.!?])\s+", paragraph) if s.strip()
        ]
        if not sentences:
            return self._split_hard(paragraph)

        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            candidate = sentence if not current else f"{current} {sentence}"
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                if len(sentence) > self.chunk_size:
                    chunks.extend(self._split_hard(sentence))
                    current = ""
                else:
                    current = sentence

        if current:
            chunks.append(current)
        return chunks

    def _split_hard(self, text: str) -> list[str]:
        pieces: list[str] = []
        step = max(1, self.chunk_size - self.chunk_overlap)
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            pieces.append(text[start:end].strip())
            if end >= len(text):
                break
            start += step
        return [piece for piece in pieces if piece]
