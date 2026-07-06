import asyncio
from app.graphs.agent_graph import build_graph
graph = build_graph()


async def main():

    print("🏥 MedoraAI - Intelligent Medical Assistant")
    print("=" * 50)
    print("Type 'exit' to quit")
    print("=" * 50)

    state = {
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

    iteration = 0
    while True:
        iteration += 1
        user_input = input("\n📝 You: ").strip()

        if user_input.lower() == "exit":
            print("\n👋 Thank you for using MedoraAI. Stay healthy!")
            break

        state["query"] = user_input
        state["iteration_count"] = iteration
        state["response"] = ""
        state["final_response"] = ""
        state["needs_user_input"] = False
        state["execution_trace"] = []
        state["decision_scores"] = {}

        try:
            print("\n⏳ Processing your request...")
            print("-" * 50)

            result = await graph.ainvoke(state)

            state = result

            # Display execution trace
            if state.get("execution_trace"):
                print(f"\n📋 Execution Trace: {' → '.join(state['execution_trace'])}")

            # Display decision scores if available
            if state.get("decision_scores"):
                print(f"\n📊 Decision Scores: {state['decision_scores']}")

            # Display response
            print(f"\n🤖 MedoraAI:")
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
