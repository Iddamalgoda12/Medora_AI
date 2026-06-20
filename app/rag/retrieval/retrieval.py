from app.rag.ingestion.embeddings import embed_texts
from app.rag.qdrant_db import client, COLLECTION_NAME


def retrieve(query: str, limit: int = 50):
    query_vector = embed_texts([query])[0]

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    return results.points