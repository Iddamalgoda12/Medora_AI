import logging

from app.rag.ingestion.embeddings import embed_texts
from app.rag.qdrant_db import COLLECTION_NAME, client

logger = logging.getLogger(__name__)


def retrieve(query: str, limit: int = 10):
    if not query.strip():
        return []

    try:
        query_vector = embed_texts([query])[0]

        results = client.query_points(         #takes output as text ,not vectors.
            collection_name=COLLECTION_NAME,
            query=query_vector.tolist(),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        return results.points
    except Exception as exc:
        logger.warning("Document retrieval failed: %s", exc)
        return []
