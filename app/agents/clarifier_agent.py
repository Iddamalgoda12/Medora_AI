from app.graphs.state import AgentState
from app.llms.gemini import ask_gemini


async def clarifier_agent(state: AgentState):

    missing = state.get("missing_fields", [])

    if len(missing) == 1:

        field = missing[0]

        if field == "specialty":
            question = "What type of specialist would you like to see?"

        elif field == "location":
            question = "Which city would you like the appointment in?"

        else:
            question = f"Please provide your {field}."

    else:

        prompt = f"""
You are a healthcare appointment assistant.

Missing information:
{missing}

Ask ONE short question to collect all missing information.
"""

        question = ask_gemini(prompt)

    return {
        **state,

        "needs_user_input": True,

        "followup_question": question,

        "execution_trace": [
            *state["execution_trace"],
            "clarifier_agent"
        ]
    }