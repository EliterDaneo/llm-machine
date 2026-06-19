"""
PDF Extractor Service
Uses PyMuPDF (fitz) to extract text, metadata, and page info from PDFs
"""
import fitz  # PyMuPDF
import os
import uuid
import aiofiles
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class PDFExtractionResult:
    """Result object from PDF extraction."""

    def __init__(self):
        self.text: str = ""
        self.page_count: int = 0
        self.word_count: int = 0
        self.metadata: dict = {}
        self.title: Optional[str] = None
        self.author: Optional[str] = None
        self.subject: Optional[str] = None
        self.language: Optional[str] = None
        self.pages: list[dict] = []
        self.error: Optional[str] = None
        self.success: bool = False

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "page_count": self.page_count,
            "word_count": self.word_count,
            "metadata": self.metadata,
            "title": self.title,
            "author": self.author,
            "subject": self.subject,
            "language": self.language,
            "pages": self.pages,
            "success": self.success,
        }


class PDFExtractorService:
    """Service for extracting content from PDF files."""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_uploaded_file(self, file_content: bytes, original_filename: str) -> dict:
        """
        Save uploaded PDF bytes to disk with a unique filename.
        Returns dict with file info.
        """
        ext = Path(original_filename).suffix.lower()
        if ext != ".pdf":
            raise ValueError(f"File harus berformat PDF, bukan '{ext}'")

        # Check file size
        file_size = len(file_content)
        if file_size > settings.max_file_size_bytes:
            raise ValueError(
                f"File terlalu besar ({file_size / 1024 / 1024:.1f}MB). "
                f"Maksimum {settings.MAX_FILE_SIZE_MB}MB."
            )

        # Generate unique filename
        unique_name = f"{uuid.uuid4().hex}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.pdf"
        file_path = self.upload_dir / unique_name

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)

        logger.info(f"Saved uploaded file: {file_path} ({file_size} bytes)")

        return {
            "filename": unique_name,
            "original_filename": original_filename,
            "file_path": str(file_path),
            "file_size_bytes": file_size,
            "mime_type": "application/pdf",
        }

    def extract(self, file_path: str) -> PDFExtractionResult:
        """
        Synchronously extract text & metadata from a PDF.
        Call this in a thread pool from async context.
        """
        result = PDFExtractionResult()

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            result.error = f"Tidak dapat membuka PDF: {str(e)}"
            logger.error(f"PDF open error: {e}")
            return result

        try:
            # Metadata
            meta = doc.metadata or {}
            result.metadata = meta
            result.title = meta.get("title") or None
            result.author = meta.get("author") or None
            result.subject = meta.get("subject") or None
            result.page_count = doc.page_count

            # Extract text page by page
            all_text_parts = []
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text("text")
                all_text_parts.append(page_text)

                # Per-page summary
                result.pages.append({
                    "page_number": page_num + 1,
                    "char_count": len(page_text),
                    "word_count": len(page_text.split()),
                    "has_images": len(page.get_images()) > 0,
                })

            result.text = "\n\n".join(all_text_parts).strip()
            result.word_count = len(result.text.split())

            # Language detection (simple heuristic)
            result.language = self._detect_language(result.text[:1000])

            result.success = True
            logger.info(
                f"Extracted PDF: {result.page_count} pages, "
                f"{result.word_count} words from {file_path}"
            )

        except Exception as e:
            result.error = f"Error saat ekstraksi: {str(e)}"
            logger.error(f"PDF extraction error: {e}", exc_info=True)

        finally:
            doc.close()

        return result

    def _detect_language(self, text: str) -> str:
        """
        Simple language detection by checking common words.
        Returns ISO 639-1 code.
        """
        text_lower = text.lower()

        indonesian_markers = ["yang", "dan", "di", "ini", "itu", "untuk", "dengan", "tidak"]
        english_markers = ["the", "and", "is", "are", "was", "were", "for", "with"]

        id_count = sum(1 for w in indonesian_markers if f" {w} " in text_lower)
        en_count = sum(1 for w in english_markers if f" {w} " in text_lower)

        if id_count > en_count:
            return "id"
        elif en_count > 0:
            return "en"
        return "unknown"

    def get_text_preview(self, text: str, max_chars: int = 500) -> str:
        """Get a clean preview of extracted text."""
        if not text:
            return ""
        preview = text[:max_chars].strip()
        if len(text) > max_chars:
            preview += "..."
        return preview

    def chunk_text(self, text: str, chunk_size: int = 3000, overlap: int = 200) -> list[str]:
        """
        Split text into overlapping chunks for large documents.
        Useful when text exceeds AI context window.
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind(". ")
                if last_period > chunk_size // 2:
                    chunk = chunk[:last_period + 1]
                    end = start + last_period + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    async def delete_file(self, file_path: str) -> bool:
        """Soft delete: remove physical file from disk."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False


# Singleton instance
pdf_extractor = PDFExtractorService()