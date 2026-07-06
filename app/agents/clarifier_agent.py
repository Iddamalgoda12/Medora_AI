from app.graphs.state import State


def clarifier_agent(
    state: State,
):

    return {
        **state,

        "final_response":
            "Could you tell me a little more about your request? For example:\n\n"
            "• What health concern or symptom do you have?\n"
            "• Are you looking for a doctor or an appointment?\n"
            "• Do you want to check medicine availability?\n"
            "• Do you need help understanding a medical report?\n\n"
            "The more details you provide, the better I can assist you.",

        "clarification_done":
            True,

        "next_task":
            None,

        "pending_tasks":
            [],

        "execution_trace": [
            *state["execution_trace"],
            "clarifier_agent"
        ]
    }