from typing import List

from langchain_core.documents import Document

from app.rag.retrieval.retrieval import retrieve
from app.rag.retrieval.reranker import rerank


def _get_relevant_documents(
    query: str,
    retrieve_limit: int = 10,
    rerank_limit: int = 5,
    use_reranker: bool = True,
) -> List[Document]:
    points = retrieve(query=query, limit=retrieve_limit)

    if not points:
        return []

    documents = [
        Document(
            page_content=(point.payload or {}).get("text", ""),
            metadata={
                "source": (point.payload or {}).get("source", ""),
                "chunk_index": (point.payload or {}).get("chunk_index"),
                "score": point.score,
            },
        )
        for point in points
        if (point.payload or {}).get("text")
    ]

    if not documents:
        return []

    if not use_reranker:
        return documents[:rerank_limit]

    ranked = rerank(
        query=query,
        documents=[
            {
                "text": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in documents
        ],
        top_k=rerank_limit,
    )

    return [
        Document(
            page_content=doc["text"],
            metadata=doc.get("metadata", {}),
        )
        for doc in ranked
    ]


def get_relevant_documents(
    query: str,
    retrieve_limit: int = 10,
    rerank_limit: int = 5,
    use_reranker: bool = True,
) -> List[Document]:
    return _get_relevant_documents(
        query=query,
        retrieve_limit=retrieve_limit,
        rerank_limit=rerank_limit,
        use_reranker=use_reranker,
    )
