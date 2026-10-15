"""Text chunking with overlap, preserving document structure."""
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Chunk:
    text: str
    index: int
    page_number: Optional[int] = None
    section_heading: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class TextChunker:
    """Split text into overlapping chunks while preserving structure."""

    def __init__(self, chunk_size: int = 800, overlap: int = 120):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(
        self,
        text: str,
        document_id: str = "",
        owner_id: Optional[int] = None,
        title: str = "",
        source_type: str = "document",
        page_numbers: Optional[List[int]] = None,
    ) -> List[Chunk]:
        """Split text into chunks with overlap, preserving paragraph boundaries."""
        if not text or not text.strip():
            return []

        # Split into paragraphs first to preserve structure
        paragraphs = self._split_paragraphs(text)
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        current_heading = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Track headings
            if self._is_heading(para):
                current_heading = para[:200]
                continue

            para_size = len(para.split())

            if current_size + para_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = "\n\n".join(current_chunk)
                page = None
                if page_numbers and chunk_index < len(page_numbers):
                    page = page_numbers[chunk_index]

                chunks.append(Chunk(
                    text=chunk_text,
                    index=chunk_index,
                    page_number=page,
                    section_heading=current_heading,
                    metadata={
                        "document_id": document_id,
                        "owner_id": owner_id,
                        "title": title,
                        "source_type": source_type,
                        "token_count": len(chunk_text.split()),
                    }
                ))
                chunk_index += 1

                # Keep overlap
                overlap_text = self._get_overlap(current_chunk)
                current_chunk = [overlap_text] if overlap_text else []
                current_size = len(current_chunk[0].split()) if current_chunk else 0

            current_chunk.append(para)
            current_size += para_size

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            page = None
            if page_numbers and chunk_index < len(page_numbers):
                page = page_numbers[chunk_index]

            chunks.append(Chunk(
                text=chunk_text,
                index=chunk_index,
                page_number=page,
                section_heading=current_heading,
                metadata={
                    "document_id": document_id,
                    "owner_id": owner_id,
                    "title": title,
                    "source_type": source_type,
                    "token_count": len(chunk_text.split()),
                }
            ))

        return chunks

    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs, preserving list items and structure."""
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Split on double newlines (paragraph breaks)
        paragraphs = re.split(r"\n\s*\n", text)
        result = []
        for p in paragraphs:
            p = p.strip()
            if p:
                result.append(p)
        return result

    def _is_heading(self, text: str) -> bool:
        """Detect if a line is a heading."""
        if len(text) > 100:
            return False
        # Markdown-style headings
        if re.match(r"^#{1,6}\s", text):
            return True
        # Numbered headings like "1. Introduction" or "Chapter 1: ..."
        if re.match(r"^(\d+\.|\d+\.\d+|Chapter\s+\d+|Section\s+\d+)", text, re.IGNORECASE):
            return True
        # ALL CAPS headings
        if text.isupper() and len(text) < 80:
            return True
        return False

    def _get_overlap(self, paragraphs: List[str]) -> str:
        """Get overlap text from the end of current chunk."""
        if not paragraphs:
            return ""
        overlap_words = []
        word_count = 0
        for para in reversed(paragraphs):
            words = para.split()
            for word in reversed(words):
                overlap_words.insert(0, word)
                word_count += 1
                if word_count >= self.overlap:
                    return " ".join(overlap_words)
        return " ".join(overlap_words)
