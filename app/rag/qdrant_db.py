from qdrant_client import QdrantClient
from qdrant_client.models import Distance
from qdrant_client.models import VectorParams

client = QdrantClient(
    url="http://localhost:6333"
)

COLLECTION_NAME = "documents"


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
            size=1024,
            distance=Distance.COSINE,
        ),
    )

    print(f"Collection '{COLLECTION_NAME}' created.")



def upload_points(points):
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )