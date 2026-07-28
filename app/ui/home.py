import chainlit as cl


async def show_home():
    await cl.Message(
        content="""
# 🏥 MedoraAI

### Your Intelligent Healthcare Agent

Describe your health concern naturally.

### Example questions

- I have had a fever for three days.
- Can you explain my blood report?
- My medicine isn't available.
- I have chest pain.
- Find me a dermatologist.

📄 Have new medical reports? Upload them here to ask questions,
receive personalized insights, and keep your Health Summary up to date. 💙
""",
        actions=[
            cl.Action(
                name="upload_health_records",
                label="📂 Upload Health Records",
                payload={}
            )
        ]
    ).send()
