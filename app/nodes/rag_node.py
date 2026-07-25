import logging

from app.graphs.state import State
from app.llms.llm import ask_llm_async
from app.memory.conversation import last_exchange_context
from app.rag.retrieval.retriever import get_document_retriever

logger = logging.getLogger(__name__)


async def rag_retrieve_node(state: State) -> State:
    """Retrieve and rerank relevant chunks from uploaded PDFs."""
    query = state["query"]
    retrieved_docs = []

    try:
        retriever = get_document_retriever()
        documents = retriever.invoke(query)
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

    return {
        **state,
        "retrieved_docs": retrieved_docs,
        "execution_trace": [
            *state["execution_trace"],
            "rag_retrieve",
        ],
    }


async def rag_format_node(state: State) -> State:
    """Build a context string from retrieved document chunks."""
    retrieved_docs = state.get("retrieved_docs", [])

    rag_result = ""
    if retrieved_docs:
        context_blocks = [
            f"[Source: {doc.get('source', 'unknown')}]\n{doc['text']}"
            for doc in retrieved_docs
            if doc.get("text")
        ]
        rag_result = "\n\n".join(context_blocks)

    return {
        **state,
        "rag_result": rag_result,
        "execution_trace": [
            *state["execution_trace"],
            "rag_format",
        ],
    }


async def rag_generate_node(state: State) -> State:
    """Generate an answer grounded in retrieved PDF context."""
    query = state["query"]
    rag_result = state.get("rag_result", "")
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
        "report_uploaded": bool(rag_result.strip()),
        "response": response,
        "execution_trace": [
            *state["execution_trace"],
            "rag_generate",
        ],
    }
