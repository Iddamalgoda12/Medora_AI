import asyncio

from app.graphs.agent_graph import build_graph

graph = build_graph()


async def main():

    print("🏥 MedoraAI")
    print("Type exit to quit")

    state = {
        "query": "",
        "response": "",

        "specialty": None,
        "location": None,

        "needs_user_input": False,
        "followup_question": None,

        "doctor_results": [],

        "route": None,
        "routes": [],

        "execution_trace": [],

        "retrieved_docs": [],
        "rag_result": "",
        "memory_result": "",
        "web_result": "",
    }

    while True:

        user_input = input("\nYou: ").strip()

        if user_input.lower() == "exit":
            break

        state["query"] = user_input

        try:

            result = await graph.ainvoke(state)

            print("\n====================")
            print("GRAPH RESULT")
            print("====================")
            print(result)

            state = result

            print("\nMedoraAI:")
            print(repr(state.get("response")))

        except Exception as e:
            print("\nERROR:")
            print(e)


if __name__ == "__main__":
    asyncio.run(main())