from app.graphs.state import State


def clarifier_agent(
    state: State,
):

    return {
        **state,

        "final_response":
            "Could you provide a little more detail about your request?",

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