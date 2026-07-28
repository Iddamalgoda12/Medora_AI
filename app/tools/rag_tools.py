from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from app.rag.retrieval.retriever import get_relevant_documents
from app.llms.llm import ask_llm


def _wrap(data: Any, success: bool = True, message: str | None = None, error: str | None = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data, "error": error}


@tool("search_documents")
def search_documents(query: str) -> dict[str, Any]:
    """Search the uploaded document index for relevant passages."""
    docs = get_relevant_documents(query)
    results = [
        {
            "text": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "chunk_index": doc.metadata.get("chunk_index"),
            "score": doc.metadata.get("score"),
        }
        for doc in docs
    ]
    return _wrap({"results": results, "total": len(results)}, message="Document search completed")


@tool("summarize_documents")
def summarize_documents(text: str) -> dict[str, Any]:
    """Summarize provided medical text using the shared LLM."""
    summary = ask_llm(f"Summarize the following medical text clearly and concisely:\n\n{text}")
    return _wrap({"summary": summary}, message="Document summary generated")


@tool("answer_from_documents")
def answer_from_documents(query: str, context: str) -> dict[str, Any]:
    """Answer a question using only the provided document context."""
    prompt = f"Answer the user's question using only the provided context.\n\nContext:\n{context}\n\nQuestion:\n{query}"
    answer = ask_llm(prompt)
    return _wrap({"answer": answer}, message="Document answer generated")
