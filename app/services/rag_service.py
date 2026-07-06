"""
rag_service.py
--------------
Single-responsibility service: extract text from PDFs and ingest them into
the Qdrant vector store via the existing ``ingest_document`` pipeline.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import fitz  # PyMuPDF – already used by loader.py

from app.rag.ingestion.ingestion import ingest_document

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from *pdf_path* as a single string.

    Pages with no extractable text are silently skipped.

    Args:
        pdf_path: Absolute path to the PDF file.

    Returns:
        Concatenated text of all pages, separated by newlines.

    Raises:
        FileNotFoundError: If *pdf_path* does not exist.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages: list[str] = []
    with fitz.open(str(pdf_path)) as doc:
        for page in doc:
            text = page.get_text().strip()
            if text:
                pages.append(text)

    full_text = "\n\n".join(pages)
    logger.info("Extracted %d chars from %s", len(full_text), pdf_path.name)
    return full_text


def extract_text_from_pdfs(pdf_paths: list[Path]) -> str:
    """Extract and concatenate text from multiple PDFs.

    Args:
        pdf_paths: List of absolute paths to PDF files.

    Returns:
        All extracted text joined by a separator line.
    """
    sections: list[str] = []
    for path in pdf_paths:
        try:
            text = extract_text_from_pdf(path)
            if text:
                sections.append(f"=== {path.name} ===\n{text}")
        except Exception as exc:
            logger.error("Could not extract text from %s: %s", path.name, exc)

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

async def ingest_pdfs_async(pdf_paths: list[Path]) -> int:
    """Generate embeddings and insert them into Qdrant for every PDF in *pdf_paths*.

    Each call to :func:`~app.rag.ingestion.ingestion.ingest_document` is
    blocking (CPU-bound embedding model), so it is offloaded to a thread pool
    to avoid blocking the async event loop.

    Args:
        pdf_paths: List of absolute paths to PDF files to ingest.

    Returns:
        Number of PDFs successfully ingested.
    """
    loop = asyncio.get_event_loop()
    ingested = 0

    for path in pdf_paths:
        try:
            logger.info("Ingesting %s into Qdrant …", path.name)
            await loop.run_in_executor(None, ingest_document, str(path))
            ingested += 1
            logger.info("Ingested %s successfully.", path.name)
        except Exception as exc:
            logger.error("Ingestion failed for %s: %s", path.name, exc)

    return ingested
