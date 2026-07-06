from app.graphs.state import State
from app.llms.gemini import ask_gemini_async


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

    return {
        **state,
        "emergency_flag": True,
        "response": response,
        "execution_trace": [
            *state["execution_trace"],
            "emergency_agent"
        ]
    }
