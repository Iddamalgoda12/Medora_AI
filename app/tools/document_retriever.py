from langchain_core.tools import tool

from app.rag.retrieval.generator import generate_context


@tool
def search_medical_documents(query: str) -> str:
    """Search uploaded medical PDF documents for information relevant to the query."""
    context = generate_context(query)

    if not context.strip():
        return "No relevant documents found in the uploaded PDF knowledge base."

    return context
