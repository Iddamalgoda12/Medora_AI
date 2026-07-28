from pathlib import Path
import fitz
from langchain_core.documents import Document

def load_document(file_path: str):
    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        documents = []

        with fitz.open(file_path) as pdf:
            for page_number, page in enumerate(pdf):
                text = page.get_text().strip()

                if not text:
                    continue

                documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": file_path,
                            "page": page_number + 1,
                        },
                    )
                )

        return documents

    with open(file_path, "r", encoding="utf-8") as file_handle:
        return [
                Document(
                    page_content=file_handle.read(),
                    metadata={"source": file_path},
                )
        ]


def load_all_documents(file_paths: list[Path]) -> dict[Path, list[Document]]:
    """Load documents for each file path and return them keyed by path."""
    return {
        path: load_document(str(path))
        for path in file_paths
    }
