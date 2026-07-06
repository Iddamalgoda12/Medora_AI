from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

# Connect to your local Qdrant instance
client = QdrantClient("http://localhost:6333")

try:
    # Create the collection (bge-m3 uses size 1024)
    client.create_collection(
        collection_name="documents",
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )
    print("✅ Collection 'documents' created successfully!")
except Exception as e:
    print(f"⚠️ Collection might already exist or error occurred: {e}")
