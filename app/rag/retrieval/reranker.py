from pathlib import Path
from sentence_transformers import CrossEncoder

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

MODEL_PATH = BASE_DIR / "AI_MODELS" / "rerankers"

reranker = CrossEncoder(
    str(MODEL_PATH),
    trust_remote_code=True,
    device="cpu",
)


def rerank(
    query: str,
    documents: list[dict],
    top_k: int = 5
) -> list[dict]:

    pairs = [
        (query, doc["text"])
        for doc in documents
    ]

    scores = reranker.predict(pairs)

    for doc, score in zip(documents, scores):
        doc["rerank_score"] = float(score)

    documents.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return documents[:top_k]