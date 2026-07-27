from __future__ import annotations

import logging

import chainlit as cl

from app.rag.ingestion.ingestion import ingest_all_documents
from app.rag.ingestion.loader import load_all_documents
from app.ui.health_profile_sidebar import show_health_profile_sidebar
from app.ui.health_profile_manager import update_health_profile_from_report
from app.ui.pdf_saver import save_uploaded_pdfs

logger = logging.getLogger(__name__)


def filter_pdfs(elements: list) -> list:
    """Return only the PDFs from user uploaded files."""
    return [
        el for el in elements
        if getattr(el, "mime", "") == "application/pdf"
        or (getattr(el, "name", "").lower().endswith(".pdf"))
    ]


async def run_report_upload_workflow(elements: list) -> None:
    pdf_elements = filter_pdfs(elements)
    if not pdf_elements:
        await cl.Message(
            content="❌ No PDF files were attached. Please upload a PDF file."
        ).send()
        return

    file_names = [el.name for el in pdf_elements]
    plural = "s" if len(file_names) > 1 else ""

    status_msg = cl.Message(
        content=(
            f"📄 Received **{len(file_names)}** PDF{plural}: "
            f"{', '.join(f'`{n}`' for n in file_names)}\n\n"
            "⏳ Processing your report(s) – this may take a moment…"
        )
    )
    await status_msg.send()

    try:
        saved_paths, skipped_files = save_uploaded_pdfs(pdf_elements)
    except Exception as exc:
        logger.exception("Failed to save uploaded PDFs.")
        await cl.Message(
            content=f"❌ Could not save the uploaded file(s): `{exc}`"
        ).send()
        return

    if not saved_paths:
        if skipped_files:
            await cl.Message(
                content=(
                    "ℹ️ All uploaded PDF(s) are already saved in the folder:\n"
                    + "\n".join(f"- `{name}`" for name in skipped_files)
                )
            ).send()
        else:
            await cl.Message(
                content="❌ No PDF files could be saved. Please try again."
            ).send()
        return

    if skipped_files:
        await cl.Message(
            content=(
                "ℹ️ Already uploaded, skipped:\n"
                + "\n".join(f"- `{name}`" for name in skipped_files)
            )
        ).send()

    try:
        await cl.Message(content="📝 Extracting text from your report(s)…").send()
        loaded_documents_by_path = load_all_documents(saved_paths)
        report_text = "\n\n".join(
            doc.page_content
            for documents in loaded_documents_by_path.values()
            for doc in documents
        )
    except Exception as exc:
        logger.exception("Text extraction failed.")
        await cl.Message(
            content=f"❌ Could not extract text from the PDF(s): `{exc}`"
        ).send()
        return

    if not report_text.strip():
        await cl.Message(
            content=(
                "⚠️ No readable text was found in the uploaded PDF(s). "
                "Scanned images or encrypted PDFs are not supported yet."
            )
        ).send()
        return

    try:
        await cl.Message(content="🧠 Updating your health profile…").send()
        updated_profile = await update_health_profile_from_report(report_text)
    except Exception as exc:
        logger.exception("Health profile update failed.")
        await cl.Message(
            content=(
                f"⚠️ Could not update your health profile: `{exc}`\n\n"
                "Embeddings will still be ingested so you can query the report."
            )
        ).send()
        updated_profile = None

    try:
        await cl.Message(
            content="🔍 Generating embeddings and inserting into the knowledge base…"
        ).send()
        total_chunks, _ = await ingest_all_documents(loaded_documents_by_path)
    except Exception as exc:
        logger.exception("Qdrant ingestion failed.")
        await cl.Message(
            content=f"❌ Embedding ingestion failed: `{exc}`"
        ).send()
        return

    try:
        await show_health_profile_sidebar()
    except Exception as exc:
        logger.warning("Could not refresh health profile sidebar: %s", exc)

    profile_note = (
        "\n✅ Your **Health Profile** in the sidebar has been updated."
        if updated_profile
        else ""
    )
    await cl.Message(
        content=(
            f"✅ Successfully processed **{len(saved_paths)}** report{plural}.\n"
            f"➡️ **Total chunks created:** {total_chunks}\n"
            f"{profile_note}\n\n"
            "You can now ask questions about your report — for example:\n"
            '> *"What do my latest blood test results say?"*'
        )
    ).send()
