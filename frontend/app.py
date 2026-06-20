import anyio.to_thread

async def mock_run_sync(func, *args, **kwargs):
    import asyncio
    kwargs.pop('cancellable', None)
    kwargs.pop('abandon_on_cancel', None)
    kwargs.pop('limiter', None)
    if func.__name__ == 'open' and len(args) > 8:
        args = args[:8]
    return await asyncio.to_thread(func, *args, **kwargs)

anyio.to_thread.run_sync = mock_run_sync

import chainlit as cl
import asyncio

@cl.on_chat_start
async def on_chat_start():
    # Send a welcome message
    await cl.Message(
        content="Welcome to the Medical Booking Agentic Platform! How can I assist you with your healthcare needs today?"
    ).send()

    # Define some initial settings or actions
    actions = [
        cl.Action(name="Book Appointment", value="book", description="Book a new medical appointment"),
        cl.Action(name="Check Symptoms", value="symptoms", description="Check your symptoms with our AI agent"),
        cl.Action(name="View Records", value="records", description="View your medical records")
    ]

    await cl.Message(
        content="Please select an option below:",
        actions=actions
    ).send()

@cl.action_callback("Book Appointment")
async def on_action_book(action: cl.Action):
    await cl.Message(content="Okay, let's book an appointment. What specialty are you looking for? (e.g., Cardiology, General Practice, Dermatology)").send()

@cl.action_callback("Check Symptoms")
async def on_action_symptoms(action: cl.Action):
    await cl.Message(content="I can help you check your symptoms. Could you please describe what you are experiencing?").send()

@cl.action_callback("View Records")
async def on_action_records(action: cl.Action):
    await cl.Message(content="To view your records, I will need to verify your identity. Please enter your patient ID.").send()

@cl.on_message
async def on_message(message: cl.Message):
    msg = cl.Message(content="")
    await msg.send()
    
    # Simulate thinking/typing delay
    await cl.sleep(1)
    
    msg.content = f"I received your message: '{message.content}'. As an AI agent, I will process this request and get back to you with the next steps."
    await msg.update()
