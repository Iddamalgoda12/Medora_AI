from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.config.settings import settings

QDRANT_HOST = settings.QDRANT_URL or "localhost"
QDRANT_PORT = settings.QDRANT_PORT or 6333

client = QdrantClient(
    url=f"http://{QDRANT_HOST}:{QDRANT_PORT}"
)

COLLECTION_NAME = "documents"
VECTOR_SIZE = 1024


def create_collection():
    collections = client.get_collections()

    names = [
        collection.name
        for collection in collections.collections
    ]

    if COLLECTION_NAME in names:
        print(f"Collection '{COLLECTION_NAME}' already exists.")
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
