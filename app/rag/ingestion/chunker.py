from langchain_core.documents import Document


def chunk_documents(documents):
    chunk_size = 100
    chunk_overlap = 25
    chunks = []

    for document in documents:
        text = document.page_content

        if not text:
            continue

        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    Document(
                        page_content=chunk_text,
                        metadata=document.metadata,
                    )
                )

            if end >= len(text):
                break

            start = max(end - chunk_overlap, start + 1)

    return chunks