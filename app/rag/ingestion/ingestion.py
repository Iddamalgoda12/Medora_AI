""" takes pdfs as inputs and ingest them in to vector database"""

from uuid import uuid4
from pathlib import Path
from qdrant_client.models import PointStruct
from langchain_core.documents import Document
from app.rag.ingestion.chunker import chunk_documents
from app.rag.ingestion.embeddings import embed_texts
from app.rag.qdrant_db import create_collection, upload_points

import chainlit as cl

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PDF_DIR = BASE_DIR / "app" / "rag" / "data" / "pdfs"


async def ingest_document(file_path: str, documents: list[Document]) -> int:
    """Ingest one document and return the number of chunks created."""

    await cl.Message(
        content=f"📄 Processing **{Path(file_path).name}**..."
    ).send()

    chunks = chunk_documents(documents)
    chunk_count = len(chunks)

    await cl.Message(
        content=(
            f"✂️ Created **{chunk_count}** chunk"
            f"{'s' if chunk_count != 1 else ''} from **{Path(file_path).name}**."
        )
    ).send()

    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    if not texts:
        print(f"No text extracted from {file_path}")
        return 0

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

    upload_points(points)                                            #uploading to Qdrant happens here
    print(f"Ingested {len(points)} chunks from {file_path}")
    return len(points)


async def ingest_all_documents(
    documents_by_path: dict[Path, list[Document]],
) -> tuple[int, dict[Path, int]]:
    """Ingest all loaded documents and return total/per-file chunk counts."""

    create_collection()

    if not documents_by_path:
        print(f"No PDF files found in {PDF_DIR}")
        return 0, {}

    total_chunks = 0
    chunks_by_path: dict[Path, int] = {}
    for pdf_path, documents in documents_by_path.items():
        chunk_count = await ingest_document(str(pdf_path), documents)
        chunks_by_path[pdf_path] = chunk_count
        total_chunks += chunk_count

    await cl.Message(content="✅ All PDFs ingested successfully!").send()
    return total_chunks, chunks_by_path
