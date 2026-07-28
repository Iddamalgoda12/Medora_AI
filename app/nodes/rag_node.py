import logging

from app.graphs.state import State
from app.llms.llm import ask_llm_async
from app.memory.conversation import last_exchange_context
from app.rag.retrieval.retriever import get_relevant_documents

logger = logging.getLogger(__name__)


async def rag_node(state: State) -> State:
    """Retrieve, format, and answer from uploaded PDFs in one node."""
    query = state["query"]
    retrieved_docs = []
    rag_result = ""

    try:
        documents = get_relevant_documents(query)
        retrieved_docs = [
            {
                "text": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "chunk_index": doc.metadata.get("chunk_index"),
                "score": doc.metadata.get("score"),
            }
            for doc in documents
        ]
    except Exception as exc:
        logger.warning("RAG retrieval failed: %s", exc)

    if retrieved_docs:
        context_blocks = [
            f"[Source: {doc.get('source', 'unknown')}]\n{doc['text']}"
            for doc in retrieved_docs
            if doc.get("text")
        ]
        rag_result = "\n\n".join(context_blocks)

    conversation_context = last_exchange_context(state.get("chat_history", []))

    if rag_result.strip():
        report_prompt = f"""
    You are a medical report analysis assistant.

    Answer the user's question using ONLY the retrieved document excerpts below.
    If the excerpts do not contain enough information, say so clearly and provide
    general guidance without inventing specific values from the documents.

    Retrieved Document Context:
    {rag_result}

    User Question:
    {query}

    Previous Exchange:
    {conversation_context}

    Provide:
    1. A direct answer based on the retrieved documents
    2. Simple explanation of relevant medical terms
    3. What the values or findings may mean
    4. When the user should consult a doctor

    Be clear, empathetic, and non-alarming while staying accurate.
    """
    else:
        report_prompt = f"""
    You are a medical report analysis assistant.

    No uploaded PDF documents matched this question in the knowledge base.
    Answer using general medical knowledge, and clearly state that no matching
    uploaded report content was found.

    User Question:
    {query}

    Previous Exchange:
    {conversation_context}

    Be clear, empathetic, and non-alarming while being accurate.
    """

    response = await ask_llm_async(report_prompt)

    return {
        **state,
        "retrieved_docs": retrieved_docs,
        "rag_result": rag_result,
        "report_uploaded": bool(rag_result.strip()),
        "response": response,
        "execution_trace": [
            *state["execution_trace"],
            "rag_node",
        ],
    }
