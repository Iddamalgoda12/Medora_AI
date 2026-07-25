from app.graphs.state import State
from app.llms.llm import ask_llm_async
from app.rag.retrieval.generator import generate_context


async def report_agent(state: State):
    """
    Report agent handles medical reports and document questions.
    Retrieves context from uploaded PDFs before generating an answer.
    """
    query = state["query"]
    rag_result = state.get("rag_result") or generate_context(query)

    if rag_result.strip():
        report_prompt = f"""
You are a medical report analysis assistant.

Answer the user's question using the retrieved document excerpts below.
If the excerpts do not contain enough information, say so clearly.

Retrieved Document Context:
{rag_result}

User Query:
{query}

Provide:
1. A direct answer based on the documents when possible
2. Simple explanation of what the test or finding measures
3. What normal or abnormal values may mean
4. When to consult a doctor

Be clear, empathetic, and non-alarming while being accurate.
"""
    else:
        report_prompt = f"""
You are a medical report analysis assistant.

No matching content was found in the uploaded PDF knowledge base for this question.
Provide helpful general guidance and note that no uploaded report content matched.

User Query:
{query}

Be clear, empathetic, and non-alarming while being accurate.
"""

    response = await ask_llm_async(report_prompt)

    return {
        **state,
        "rag_result": rag_result,
        "report_uploaded": bool(rag_result.strip()),
        "response": response,
        "execution_trace": [
            *state["execution_trace"],
            "report_agent",
        ],
    }
