from __future__ import annotations

import logging
from uuid import uuid4

import chainlit as cl

from main import create_initial_state, run_agent
from app.ui.home import show_home
from app.ui.health_profile_sidebar import show_health_profile_sidebar
from app.ui.report_upload_workflow import run_report_upload_workflow

logger = logging.getLogger(__name__)


@cl.on_chat_start
async def on_chat_start() -> None:
    state = create_initial_state()
    cl.user_session.set("state", state)
    cl.user_session.set("thread_id", f"doctor-{uuid4()}")
    await show_health_profile_sidebar()
    await show_home()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    state = cl.user_session.get("state") or create_initial_state()
    thread_id = cl.user_session.get("thread_id")

    try:
        state = await run_agent(state=state, user_input=message.content, thread_id=thread_id)
    except Exception as exc:
        logger.exception("Doctor agent failed.")
        await cl.Message(content=f"❌ An error occurred while processing your request: `{exc}`").send()
        return

    cl.user_session.set("state", state)

    response = state.get("response", "")
    if response:
        await cl.Message(content=response).send()
    else:
        await cl.Message(content="I couldn't generate a response. Please try rephrasing your question.").send()


@cl.action_callback("upload_health_records")
async def on_upload_health_records(action: cl.Action) -> None:
    try:
        files = await cl.AskFileMessage(
            content="Upload your medical report PDF(s).",
            accept=["application/pdf"],
            max_files=10,
            max_size_mb=100,
        ).send()
        if not files:
            await cl.Message(content="No PDF files were selected.").send()
            return

        await run_report_upload_workflow(files)
    except Exception as exc:
        logger.exception("Report upload workflow failed.")
        await cl.Message(content=f"❌ Could not process the uploaded report(s): `{exc}`").send()
