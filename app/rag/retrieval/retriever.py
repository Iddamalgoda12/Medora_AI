from typing import List
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field
from app.rag.retrieval.retrieval import retrieve
from app.rag.retrieval.reranker import rerank


class QdrantDocumentRetriever(BaseRetriever):
    """LangChain retriever backed by the local Qdrant vector store."""

    retrieve_limit: int = Field(default=50)
    rerank_limit: int = Field(default=5)
    use_reranker: bool = Field(default=True)

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        points = retrieve(query=query, limit=self.retrieve_limit)

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

        if not self.use_reranker:
            return documents[: self.rerank_limit]

        ranked = rerank(
            query=query,
            documents=[
                {
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                }
                for doc in documents
            ],
            top_k=self.rerank_limit,
        )

        return [
            Document(
                page_content=doc["text"],
                metadata=doc.get("metadata", {}),
            )
            for doc in ranked
        ]


def get_document_retriever(
    retrieve_limit: int = 50,
    rerank_limit: int = 5,
) -> QdrantDocumentRetriever:
    return QdrantDocumentRetriever(
        retrieve_limit=retrieve_limit,
        rerank_limit=rerank_limit,
    )
