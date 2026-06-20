from .retrieval import retrieve
from .reranker import rerank


def generate_context(
    query: str,
    retrieve_limit: int = 50,
    rerank_limit: int = 5
) -> str:

    points = retrieve(
        query=query,
        limit=retrieve_limit
    )

    documents = [
    {
        "id": point.id,
        "score": point.score,
        "text": point.payload.get("text", "") if point.payload else "",
        "metadata": point.payload or {},
    }
    for point in points
    ]   

    top_docs = rerank(
        query=query,
        documents=documents,
        top_k=rerank_limit
    )

    return "\n\n".join(
        doc["text"]
        for doc in top_docs
    )