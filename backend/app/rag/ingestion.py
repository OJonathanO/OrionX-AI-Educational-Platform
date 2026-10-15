"""Document ingestion pipeline: extract, chunk, embed, and store documents."""
import os
import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from .chunking import TextChunker, Chunk
from .embeddings import EmbeddingProvider, get_embedding_provider
from .vector_store import VectorStore, VectorRecord, get_vector_store
from app.config import settings

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for processing and ingesting documents into the RAG pipeline."""

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        chunker: Optional[TextChunker] = None,
    ):
        self.embedding_provider = embedding_provider or get_embedding_provider(
            settings.EMBEDDING_PROVIDER, settings.EMBEDDING_MODEL
        )
        self.vector_store = vector_store or get_vector_store()
        self.chunker = chunker or TextChunker(
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP,
        )

    def process_document(
        self,
        file_path: str,
        document_id: str,
        owner_id: int,
        title: str,
        file_type: str,
        is_public: bool = False,
    ) -> Tuple[List[Chunk], int]:
        """Process a document file: extract text, chunk, embed, and store.

        Args:
            file_path: Path to the document file.
            document_id: Unique identifier for the document.
            owner_id: ID of the document owner.
            title: Document title.
            file_type: File type - 'pdf', 'docx', or 'txt'.
            is_public: Whether the document is publicly accessible.

        Returns:
            Tuple of (list of Chunk objects, number of chunks created).

        Raises:
            ValueError: If the file is empty, corrupted, or unsupported.
            FileNotFoundError: If the file does not exist.
        """
        file_path = Path(file_path)

        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")

        # Validate file type
        file_type = file_type.lower().lstrip(".")
        supported_types = {"pdf", "docx", "txt"}
        if file_type not in supported_types:
            raise ValueError(
                f"Unsupported file type '{file_type}'. "
                f"Supported types: {', '.join(supported_types)}"
            )

        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            raise ValueError(f"Document file is empty: {file_path}")

        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            raise ValueError(
                f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds "
                f"maximum allowed ({settings.MAX_UPLOAD_SIZE_MB}MB)"
            )

        # Extract text based on file type
        logger.info(f"Extracting text from {file_type} file: {file_path}")
        try:
            if file_type == "pdf":
                raw_text, page_numbers = self._extract_pdf(file_path)
            elif file_type == "docx":
                raw_text = self._extract_docx(file_path)
                page_numbers = None
            else:  # txt
                raw_text = self._extract_txt(file_path)
                page_numbers = None
        except Exception as e:
            raise ValueError(f"Failed to extract text from {file_type} file: {e}")

        # Clean the extracted text
        cleaned_text = self._clean_text(raw_text)

        if not cleaned_text or not cleaned_text.strip():
            raise ValueError(
                f"No extractable text found in document. "
                f"The file may be corrupted, scanned (image-only PDF), or empty."
            )

        # Chunk the text
        logger.info(f"Chunking document '{title}' ({len(cleaned_text)} chars)")
        chunks = self.chunker.chunk_text(
            text=cleaned_text,
            document_id=document_id,
            owner_id=owner_id,
            title=title,
            page_numbers=page_numbers,
        )

        if not chunks:
            raise ValueError(
                f"Document produced no chunks after processing. "
                f"The text may be too short or improperly formatted."
            )

        # Generate embeddings for all chunks
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_provider.embed(chunk_texts)

        if len(embeddings) != len(chunks):
            raise ValueError(
                f"Embedding count mismatch: got {len(embeddings)} embeddings "
                f"for {len(chunks)} chunks"
            )

        # Create vector records
        records = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            record = VectorRecord(
                id=f"{document_id}_chunk_{chunk.index}",
                text=chunk.text,
                embedding=embedding,
                document_id=document_id,
                owner_id=owner_id,
                metadata={
                    "document_id": document_id,
                    "owner_id": owner_id,
                    "title": title,
                    "page_number": chunk.page_number,
                    "section_heading": chunk.section_heading,
                    "chunk_index": chunk.index,
                    "is_public": is_public,
                    "file_type": file_type,
                    "token_count": len(chunk.text.split()),
                },
            )
            records.append(record)

        # Store in vector store
        logger.info(f"Storing {len(records)} chunks in vector store")
        self.vector_store.add(records)

        logger.info(
            f"Successfully ingested document '{title}' (ID: {document_id}) "
            f"with {len(chunks)} chunks"
        )

        return chunks, len(chunks)

    def delete_document(self, document_id: str) -> int:
        """Remove all chunks for a document from the vector store.

        Args:
            document_id: The document ID to delete.

        Returns:
            Number of chunks removed.
        """
        logger.info(f"Deleting document {document_id} from vector store")
        count = self.vector_store.delete_by_document(document_id)
        logger.info(f"Deleted {count} chunks for document {document_id}")
        return count

    def _extract_pdf(self, file_path: Path) -> Tuple[str, Optional[List[int]]]:
        """Extract text from a PDF file using PyMuPDF.

        Returns:
            Tuple of (extracted text, list of page numbers per chunk).
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF is not installed. Install it with: pip install pymupdf"
            )

        text_parts = []
        page_numbers = []

        try:
            doc = fitz.open(str(file_path))
        except Exception as e:
            raise ValueError(f"Cannot open PDF file (may be corrupted): {e}")

        if doc.page_count == 0:
            raise ValueError("PDF has no pages")

        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            if page_text.strip():
                text_parts.append(page_text)
                page_numbers.append(page_num + 1)  # 1-based page numbers

        doc.close()

        if not text_parts:
            raise ValueError(
                "No text content found in PDF. It may be a scanned/image-only document."
            )

        return "\n\n".join(text_parts), page_numbers

    def _extract_docx(self, file_path: Path) -> str:
        """Extract text from a DOCX file using python-docx."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "python-docx is not installed. Install it with: pip install python-docx"
            )

        try:
            doc = Document(str(file_path))
        except Exception as e:
            raise ValueError(f"Cannot open DOCX file (may be corrupted): {e}")

        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)

        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    paragraphs.append(row_text)

        if not paragraphs:
            raise ValueError("No text content found in DOCX file")

        return "\n\n".join(paragraphs)

    def _extract_txt(self, file_path: Path) -> str:
        """Extract text from a plain text file."""
        # Try multiple encodings
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                text = file_path.read_text(encoding=encoding)
                if text.strip():
                    return text
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise ValueError(
            f"Could not decode text file with any supported encoding: {file_path}"
        )

    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing excessive whitespace and null bytes."""
        if not text:
            return ""

        # Remove null bytes
        text = text.replace("\x00", "")

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove excessive whitespace (more than 2 consecutive newlines)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove excessive spaces (more than 2 consecutive spaces)
        text = re.sub(r" {2,}", " ", text)

        # Remove non-printable characters except newlines and tabs
        text = re.sub(r"[^\x20-\x7E\n\t]", "", text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text


# Singleton instance
_ingestion_service: Optional[IngestionService] = None


def get_ingestion_service() -> IngestionService:
    """Get or create the global ingestion service instance."""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service
