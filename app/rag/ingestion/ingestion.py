from pathlib import Path
from uuid import uuid4

from qdrant_client.models import PointStruct

from app.rag.ingestion.loader import load_document
from app.rag.ingestion.chunker import chunk_documents
from app.rag.ingestion.embeddings import embed_texts
from app.rag.qdrant_db import create_collection, upload_points

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PDF_DIR = BASE_DIR / "app" / "rag" / "data" / "pdfs"


def ingest_document(file_path: str):
    print(f"\nProcessing: {file_path}")

    documents = load_document(file_path)
    chunks = chunk_documents(documents)

    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    if not texts:
        print(f"No text extracted from {file_path}")
        return

    vectors = embed_texts(texts)

    points = []

    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
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

    upload_points(points)
    print(f"Ingested {len(points)} chunks from {file_path}")


def ingest_all_documents():
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {PDF_DIR}")
        return

    for pdf_file in pdf_files:
        ingest_document(str(pdf_file))

    print("\nAll PDFs ingested successfully")


if __name__ == "__main__":
    create_collection()
    ingest_all_documents()
