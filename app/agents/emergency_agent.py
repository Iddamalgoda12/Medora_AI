from app.graphs.state import State
from app.llms.gemini import ask_gemini_async

# For emergency situations.
def build_emergency_actions(emergency_number: str = "112") -> str:
    """Return quick-action links for calling or messaging emergency services."""
    return (
        "\n\n🚨 If this is life-threatening, act immediately:\n"
        f"- Call emergency services: [Call {emergency_number}](tel:{emergency_number})\n"
        f"- Send a quick message: [Message {emergency_number}](sms:{emergency_number}?body=Emergency%20help%20needed)"
    )
#Emergency

async def emergency_agent(state: State):
    """
    Emergency agent handles critical health situations.
    """
    query = state["query"]

    emergency_prompt = f"""
You are a medical emergency response assistant.

The user has described a potentially CRITICAL SITUATION.

Respond with:
1. An immediate safety assessment (if dangerous, suggest calling emergency services)
2. First aid guidance if applicable
3. When to seek emergency care

User Query:
{query}

Respond in a clear, structured, and calming manner.
"""

    response = await ask_gemini_async(emergency_prompt)
    #Emergency Situation
    response = f"{response}{build_emergency_actions()}"

    return {
        **state,
        "emergency_flag": True,
        "response": response,
        "execution_trace": [
            *state["execution_trace"],
            "emergency_agent"
        ]
    }
