from __future__ import annotations
import logging
import chainlit as cl
from main import create_initial_state, run_agent
from home import show_home
from health_profile import show_health_profile
from app.agents.emergency_agent import emergency_agent
from app.services.upload_service import save_uploaded_pdfs
from app.services.rag_service import extract_text_from_pdfs, ingest_pdfs_async
from app.services.health_profile_service import update_profile_from_report

logger = logging.getLogger(__name__)

def _filter_pdfs(elements: list) -> list:
    """Return only the PDF attachments from a Chainlit message element list."""
    return [
        el for el in elements
        if getattr(el, "mime", "") == "application/pdf"
        or (getattr(el, "name", "").lower().endswith(".pdf"))
    ]

async def _handle_pdf_uploads(pdf_elements: list) -> None:

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

    # ── Step 1: Save PDFs ─────────────────────────────────────────────────
    try:
        saved_paths = save_uploaded_pdfs(pdf_elements)
    except Exception as exc:
        logger.exception("Failed to save uploaded PDFs.")
        await cl.Message(
            content=f"❌ Could not save the uploaded file(s): `{exc}`"
        ).send()
        return

    if not saved_paths:
        await cl.Message(
            content="❌ No PDF files could be saved. Please try again."
        ).send()
        return

    # ── Step 2: Extract text ──────────────────────────────────────────────
    try:
        report_text = extract_text_from_pdfs(saved_paths)
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

    # ── Step 3: Update health profile via Gemini ──────────────────────────
    try:
        await cl.Message(content="🧠 Updating your health profile…").send()
        updated_profile = await update_profile_from_report(report_text)
    except Exception as exc:
        logger.exception("Health profile update failed.")
        await cl.Message(
            content=(
                f"⚠️ Could not update your health profile: `{exc}`\n\n"
                "Embeddings will still be ingested so you can query the report."
            )
        ).send()
        updated_profile = None

    # ── Step 4: Ingest embeddings into Qdrant ─────────────────────────────
    try:
        await cl.Message(
            content="🔍 Generating embeddings and inserting into the knowledge base…"
        ).send()
        ingested_count = await ingest_pdfs_async(saved_paths)
    except Exception as exc:
        logger.exception("Qdrant ingestion failed.")
        await cl.Message(
            content=f"❌ Embedding ingestion failed: `{exc}`"
        ).send()
        return

    # ── Step 5: Refresh sidebar ───────────────────────────────────────────
    try:
        await show_health_profile()
    except Exception as exc:
        logger.warning("Could not refresh health profile sidebar: %s", exc)

    # ── Final confirmation ────────────────────────────────────────────────
    profile_note = (
        "\n✅ Your **Health Profile** in the sidebar has been updated."
        if updated_profile
        else ""
    )
    await cl.Message(
        content=(
            f"✅ Successfully processed **{ingested_count}** of "
            f"**{len(saved_paths)}** report{plural}.\n"
            f"{profile_note}\n\n"
            "You can now ask questions about your report — for example:\n"
            '> *"What do my latest blood test results say?"*'
        )
    ).send()


# ---------------------------------------------------------------------------
# Chainlit lifecycle handlers
# ---------------------------------------------------------------------------

@cl.on_chat_start
async def on_chat_start() -> None:
    """Initialise per-session state and render the welcome screen."""
    state = create_initial_state()
    cl.user_session.set("state", state)
    cl.user_session.set("iteration", 0)

    await show_home()
    await show_health_profile()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """Route incoming messages: PDF attachments → upload pipeline; text → agent."""

    # ── PDF upload path ───────────────────────────────────────────────────
    pdf_elements = _filter_pdfs(message.elements or [])
    if pdf_elements:
        await _handle_pdf_uploads(pdf_elements)

        # If the user also typed a question alongside the upload, process it
        # below; otherwise return early.
        if not message.content.strip():
            return

    # ── Normal chat path ──────────────────────────────────────────────────
    state = cl.user_session.get("state")
    iteration = cl.user_session.get("iteration", 0) + 1

    try:
        if state.get("emergency_confirmation_pending"):
            state["query"] = message.content
            state["iteration_count"] = iteration
            state = await emergency_agent(state)
        else:
            state = await run_agent(
                state=state,
                user_input=message.content,
                iteration=iteration,
            )
    except Exception as exc:
        logger.exception("Agent graph raised an exception.")
        await cl.Message(
            content=f"❌ An error occurred while processing your request: `{exc}`"
        ).send()
        return

    cl.user_session.set("state", state)
    cl.user_session.set("iteration", iteration)

    emergency_steps = state.get("emergency_steps") or []
    if emergency_steps:
        for step in emergency_steps:
            if step:
                await cl.Message(content=step).send()
        return

    response = state.get("response") or state.get("final_response", "")
    if response:
        await cl.Message(content=response).send()
    else:
        await cl.Message(
            content="🤔 I wasn't able to generate a response. Please rephrase your question."
        ).send()
