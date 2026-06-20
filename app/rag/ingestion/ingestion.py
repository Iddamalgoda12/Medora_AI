from pathlib import Path
from uuid import uuid4

from qdrant_client.models import PointStruct

from app.rag.ingestion.loader import load_document
from app.rag.ingestion.chunker import chunk_documents
from app.rag.ingestion.embeddings import embed_texts
from app.rag.qdrant_db import upload_points
from app.rag.qdrant_db import create_collection


PDF_DIR = Path("app/rag/data/pdfs")


def ingest_document(file_path: str):

    print(f"\nProcessing: {file_path}")

    # Load thee docs
    documents = load_document(file_path)

    # Chunk documents
    chunks = chunk_documents(documents)

    # Extract text from chunks
    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    # Generate embeddings
    vectors = embed_texts(texts)

    # Build Qdrant points
    points = []

    for idx, (chunk, vector) in enumerate(
        zip(chunks, vectors)
    ):
        payload = {
            "text": chunk.page_content,
            "source": file_path,
            "chunk_index": idx,
        }

        points.append(
            PointStruct(
                id=str(uuid4()),
                vector=vector.tolist(),
                payload=payload,
            )
        )

    # Upload to Qdrant
    upload_points(points)


def ingest_all_documents():

    pdf_files = PDF_DIR.glob("*.pdf")

    for pdf_file in pdf_files:
        ingest_document(str(pdf_file))

    print("\nAll PDFs ingested successfully")


if __name__ == "__main__":
    create_collection()
    ingest_all_documents()