from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from app.config.settings import settings
from app.config.embeddings import EMBEDDING_DIMENSION, RAG_COLLECTION_NAME

QDRANT_HOST = settings.QDRANT_URL or "localhost"
QDRANT_PORT = settings.QDRANT_PORT or 6333

client = QdrantClient(
    url=f"http://{QDRANT_HOST}:{QDRANT_PORT}"
)

COLLECTION_NAME = RAG_COLLECTION_NAME
VECTOR_SIZE = EMBEDDING_DIMENSION


def create_collection():
    collections = client.get_collections()

    names = [
        collection.name
        for collection in collections.collections
    ]

    if COLLECTION_NAME in names:
        collection_info = client.get_collection(COLLECTION_NAME)
        vector_size = collection_info.config.params.vectors.size
        if vector_size != VECTOR_SIZE:
            raise ValueError(
                f"Qdrant collection '{COLLECTION_NAME}' uses vector size {vector_size}, "
                f"but the app now requires {VECTOR_SIZE}. "
                f"Create a new collection or reindex existing points with the shared embedding model."
            )
        print(f"Collection '{COLLECTION_NAME}' already exists with matching vector size.")
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )

    print(f"Collection '{COLLECTION_NAME}' created.")


def upload_points(points):
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )
