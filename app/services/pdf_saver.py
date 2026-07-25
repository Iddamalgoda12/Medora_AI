"""
2 functions. Saves uploaded PDfs to pc.
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
    takes filename and its path and saves it to the pdfs folder."""

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
    if destination.exists():
        raise FileExistsError(f"PDF already uploaded: {file_name}")

    shutil.copy2(source, destination)                   #Actual copying happens here.

    logger.info("Saved uploaded PDF → %s", destination)
    return destination


def save_uploaded_pdfs(elements: list) -> tuple[list[Path], list[str]]:
    """Save uploaded PDf files to data folder and return their paths.

    Args:
        elements: List of Chainlit ``Element`` objects.  Each must expose
                  ``.name`` (original filename) and ``.path`` (temp file path).

    Returns:
        A tuple of:
        - List of :class:`~pathlib.Path` objects for all successfully saved PDFs.
        - List of filenames that were already uploaded and therefore skipped.
    """
    saved: list[Path] = []
    skipped: list[str] = []
    for element in elements:
        try:
            path = save_uploaded_pdf(
                file_name=element.name,
                source_path=element.path,
            )
            saved.append(path)
        except FileExistsError:
            skipped.append(element.name)
            logger.info("Skipped already uploaded PDF: %s", element.name)
        except Exception as exc:
            logger.error("Failed to save %s: %s", element.name, exc)
    return saved, skipped
