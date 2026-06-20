from collections import Counter
from pathlib import Path

from app.rag.qdrant_db import COLLECTION_NAME, client


def _collection_exists(collection_name: str) -> bool:
    collections = client.get_collections()
    names = [collection.name for collection in collections.collections]
    return collection_name in names


def list_uploaded_files(collection_name: str = COLLECTION_NAME) -> Counter:
    """Return a mapping of filename -> number of stored chunks."""

    if not _collection_exists(collection_name):
        return Counter()

    file_counts = Counter()
    offset = None

    while True:
        points, offset = client.scroll(
            collection_name=collection_name,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        if not points:
            break

        for point in points:
            payload = point.payload or {}

            source = payload.get("source")

            if source:
                filename = Path(str(source)).name
                file_counts[filename] += 1

        if offset is None:
            break

    return file_counts


def print_uploaded_files(collection_name: str = COLLECTION_NAME) -> None:
    file_counts = list_uploaded_files(collection_name)

    if not file_counts:
        print(f"No uploaded files found in collection '{collection_name}'.")
        return

    print(f"\nUploaded files in collection '{collection_name}':")
    print("-" * 60)

    for index, (filename, chunks) in enumerate(
        sorted(file_counts.items()),
        start=1,
    ):
        print(f"{index}. {filename} ({chunks} chunks)")

    print("-" * 60)
    print(f"Total Files: {len(file_counts)}")
    print(f"Total Chunks: {sum(file_counts.values())}")


if __name__ == "__main__":
    print_uploaded_files()