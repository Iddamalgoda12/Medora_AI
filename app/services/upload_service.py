"""
Single-responsibility-accept raw Chainlit attachment objects and
persist them to the canonical PDF store directory.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)
PDF_DIR: Path = (
    Path(__file__).resolve().parent.parent / "rag" / "data" / "pdfs"
)


def ensure_pdf_dir() -> None:
    """Create the PDF storage directory if it does not already exist."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)


def save_uploaded_pdf(file_name: str, source_path: str) -> Path:
    """Copy a Chainlit-uploaded PDF from its temp location to ``PDF_DIR``.

    Args:
        file_name:   Original filename supplied by the user (e.g. ``report.pdf``).
        source_path: Absolute path to the temp file created by Chainlit.

    Returns:
        The final :class:`~pathlib.Path` of the saved PDF inside ``PDF_DIR``.

    Raises:
        ValueError: If the uploaded file is not a PDF.
        FileNotFoundError: If the source temp file does not exist.
    """
    ensure_pdf_dir()

    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(
            f"Uploaded temp file not found: {source_path}"
        )

    if Path(file_name).suffix.lower() != ".pdf":
        raise ValueError(
            f"Only PDF files are supported. Received: {file_name!r}"
        )

    destination = PDF_DIR / file_name
    shutil.copy2(source, destination)

    logger.info("Saved uploaded PDF → %s", destination)
    return destination


def save_uploaded_pdfs(elements: list) -> list[Path]:
    """Persist multiple Chainlit attachment objects to the PDF directory.

    Args:
        elements: List of Chainlit ``Element`` objects.  Each must expose
                  ``.name`` (original filename) and ``.path`` (temp file path).

    Returns:
        List of :class:`~pathlib.Path` objects for all successfully saved PDFs.
        Files that fail are logged and skipped rather than raising.
    """
    saved: list[Path] = []
    for element in elements:
        try:
            path = save_uploaded_pdf(
                file_name=element.name,
                source_path=element.path,
            )
            saved.append(path)
        except Exception as exc:
            logger.error("Failed to save %s: %s", element.name, exc)
    return saved
