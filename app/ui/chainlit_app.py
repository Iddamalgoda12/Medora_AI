from __future__ import annotations
import logging
import chainlit as cl
from main import create_initial_state, run_agent
from home import show_home
from health_profile import show_health_profile
from app.agents.emergency_agent import emergency_agent
from app.ui.pdf_upload_handler import handle_pdf_uploads

logger = logging.getLogger(__name__)

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
    if message.elements:
        await handle_pdf_uploads(message.elements)

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
