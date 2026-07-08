import asyncio
import logging
from app.graphs.agent_graph import build_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

graph = build_graph()


def create_initial_state():
    return {
        # Core fields
        "query": "",
        "response": "",

        # Appointment/Doctor Search specific
        "specialty": None,
        "location": None,
        "needs_user_input": False,
        "followup_question": None,
        "doctor_results": [],

        # Routing and execution
        "routes": [],
        "execution_trace": [],
        "next_task": None,
        "pending_tasks": [],
        "completed_tasks": [],

        # Results
        "retrieved_docs": [],
        "rag_result": "",
        "memory_result": "",
        "web_result": "",
        "tool_result": "",
        "chat_result": "",

        # Medical context
        "symptoms": [],
        "current_goal": "",
        "urgency": "",
        "report_uploaded": False,
        "medicine_request": False,
        "medicine_names": [],
        "user_location": None,
        "appointment_request": False,
        "emergency_flag": False,
        "doctor_recommendation": "",
        "pharmacy_recommendation": "",
        "appointment_recommendation": "",
        "patient_analysis": "",
        "emergency_assessment": "",
        "emergency_call_prototype": {},
        "emergency_steps": [],
        "emergency_confirmation_pending": False,
        "emergency_pending_call": {},

        # Metadata
        "iteration_count": 0,
        "final_answer": "",
        "agent_results": [],
        "decision_scores": {},
        "clarification_done": False,
        "user_context": {},
        "metadata": {},
        "chat_history": [],
        "final_response": "",
        "route": None,
    }


async def run_agent(state, user_input, iteration):
    state["query"] = user_input
    state["iteration_count"] = iteration
    state["response"] = ""
    state["final_response"] = ""
    state["needs_user_input"] = False
    state["execution_trace"] = []
    state["decision_scores"] = {}

    result = await graph.ainvoke(state)
    log_agent_run(result)

    return result


def log_agent_run(state):
    """Print a compact routing summary to the backend terminal."""
    decision_scores = state.get("decision_scores", {})
    chosen_task = state.get("next_task")
    completed_tasks = state.get("completed_tasks", [])
    pending_tasks = state.get("pending_tasks", [])
    execution_trace = state.get("execution_trace", [])
    response = state.get("response") or state.get("final_response", "")

    if decision_scores:
        logger.info("Decision scores: %s", decision_scores)

    logger.info(
        "Decision outcome | chosen=%s | completed=%s | pending=%s",
        chosen_task or "unknown",
        completed_tasks or [],
        pending_tasks or [],
    )

    if execution_trace:
        logger.info("Execution trace: %s", " -> ".join(execution_trace))

    if response:
        preview = response.strip().replace("\n", " ")
        logger.info("Response preview: %s", preview[:200])


async def main():

    print("🏥 MedoraAI - Intelligent Medical Assistant")
    print("=" * 50)
    print("Type 'exit' to quit")
    print("=" * 50)

    state = create_initial_state()

    iteration = 0

    while True:
        iteration += 1

        user_input = input("\n📝 You: ").strip()

        if user_input.lower() == "exit":
            print("\n👋 Thank you for using MedoraAI. Stay healthy!")
            break

        try:
            print("\n⏳ Processing your request...")
            print("-" * 50)

            state = await run_agent(
                state,
                user_input,
                iteration,
            )

            # Display execution trace
            if state.get("execution_trace"):
                print(f"\n📋 Execution Trace: {' → '.join(state['execution_trace'])}")

            # Display decision scores if available
            if state.get("decision_scores"):
                print(f"\n📊 Decision Scores: {state['decision_scores']}")

            # Display response
            print("\n🤖 MedoraAI:")
            print("-" * 50)

            response = state.get("response") or state.get("final_response", "")

            if response:
                print(response)
            else:
                print("(No response generated)")

            print("-" * 50)

        except Exception as e:
            print("\n❌ ERROR:")
            print(f"   {str(e)}")

            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
