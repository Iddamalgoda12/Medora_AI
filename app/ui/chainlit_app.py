"""
chainlit_app.py
---------------
Entry point for the MedoraAI Chainlit UI.

PDF upload pipeline (triggered when the user attaches PDFs via the paperclip):
  1. Save PDFs  →  upload_service
  2. Extract text  →  rag_service
  3. Analyze for Proactive Response -> pharmacy_search
  4. Update health profile via Gemini  →  health_profile_service
  5. Ingest embeddings into Qdrant  →  rag_service
  6. Refresh sidebar  →  health_profile (UI helper)

Normal text messages are forwarded to the LangGraph agent graph.
"""

from __future__ import annotations

import logging

import chainlit as cl

from main import create_initial_state, run_agent
from home import show_home
from health_profile import show_health_profile
from app.services.upload_service import save_uploaded_pdfs
from app.services.rag_service import extract_text_from_pdfs, ingest_pdfs_async
from app.services.health_profile_service import update_profile_from_report

# Import our newly centralized proactive routing logic
from app.tools.pharmacy_search import analyze_proactive_document, execute_pharmacy_routing

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _filter_pdfs(elements: list) -> list:
    """Return only the PDF attachments from a Chainlit message element list."""
    return [
        el for el in elements
        if getattr(el, "mime", "") == "application/pdf"
        or (getattr(el, "name", "").lower().endswith(".pdf"))
    ]


# ---------------------------------------------------------------------------
# PDF upload pipeline
# ---------------------------------------------------------------------------

async def _handle_pdf_uploads(pdf_elements: list) -> None:
    """Execute the full PDF processing pipeline and keep the user informed."""
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
        await cl.Message(content=f"❌ Could not save the uploaded file(s): `{exc}`").send()
        return

    if not saved_paths:
        await cl.Message(content="❌ No PDF files could be saved. Please try again.").send()
        return

    # ── Step 2: Extract text ──────────────────────────────────────────────
    try:
        report_text = extract_text_from_pdfs(saved_paths)
    except Exception as exc:
        logger.exception("Text extraction failed.")
        await cl.Message(content=f"❌ Could not extract text from the PDF(s): `{exc}`").send()
        return

    if not report_text.strip():
        await cl.Message(
            content="⚠️ No readable text was found in the uploaded PDF(s). Scanned images are not supported yet."
        ).send()
        return

    # ── Step 3: Analyze for Proactive UI Response ─────────────────────────
    # Run our Gemini classification immediately to formulate a chat response
    proactive_data = None
    try:
        proactive_data = analyze_proactive_document(report_text)
    except Exception as exc:
        logger.warning(f"Proactive analysis failed: {exc}")

    # ── Step 4: Update health profile via Gemini ──────────────────────────
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

    # ── Step 5: Ingest embeddings into Qdrant ─────────────────────────────
    try:
        await cl.Message(content="🔍 Generating embeddings and inserting into the knowledge base…").send()
        ingested_count = await ingest_pdfs_async(saved_paths)
    except Exception as exc:
        logger.exception("Qdrant ingestion failed.")
        await cl.Message(content=f"❌ Embedding ingestion failed: `{exc}`").send()
        return

    # ── Step 6: Refresh sidebar ───────────────────────────────────────────
    try:
        await show_health_profile()
    except Exception as exc:
        logger.warning("Could not refresh health profile sidebar: %s", exc)

    # ── Final Proactive Confirmation ──────────────────────────────────────
    profile_note = "✅ Your **Health Profile** has been updated.\n\n" if updated_profile else ""
    
    if proactive_data:
        # If it's a prescription, store the drugs in memory waiting for a location
        if proactive_data.get("pending_drugs"):
            cl.user_session.set("pending_prescription_drugs", proactive_data["pending_drugs"])
            
        await cl.Message(
            content=f"{profile_note}{proactive_data['ui_message']}"
        ).send()
    else:
        # Fallback if the proactive engine fails
        await cl.Message(
            content=(
                f"✅ Successfully processed **{ingested_count}** report(s).\n"
                f"{profile_note}"
                "You can now ask questions about your document."
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
    """Route incoming messages: Intercept location -> PDF attachments -> text -> agent."""

    # ── 0. Intercept Location for Pending Prescription ────────────────────
    pending_drugs = cl.user_session.get("pending_prescription_drugs")
    pdf_elements = _filter_pdfs(message.elements or [])
    
    # If we are waiting for a location, no new PDFs were uploaded, and text exists
    if pending_drugs and not pdf_elements and message.content.strip():
        location = message.content.strip()
        cl.user_session.set("pending_prescription_drugs", None) # Clear state to prevent looping
        
        await cl.Message(content="🔄 Scanning local pharmacies for stock...").send()
        
        try:
            # Query DB and format response
            final_map = execute_pharmacy_routing(pending_drugs, location)
            await cl.Message(content=final_map).send()
        except Exception as e:
            await cl.Message(content=f"❌ Error during pharmacy routing: {e}").send()
        
        return # Halt execution here so it doesn't go to the main LLM agent

    # ── 1. PDF upload path ────────────────────────────────────────────────
    if pdf_elements:
        await _handle_pdf_uploads(pdf_elements)

        if not message.content.strip():
            return

    # ── 2. Normal chat path (LangGraph) ───────────────────────────────────
    state = cl.user_session.get("state")
    iteration = cl.user_session.get("iteration", 0) + 1

    try:
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

    response = state.get("response") or state.get("final_response", "")
    if response:
        await cl.Message(content=response).send()
    else:
        await cl.Message(
            content="🤔 I wasn't able to generate a response. Please rephrase your question."
        ).send()