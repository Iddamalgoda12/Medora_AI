from pathlib import Path
from sentence_transformers import CrossEncoder

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_PATH = BASE_DIR / "AI_MODELS" / "rerankers"
FALLBACK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_reranker = None


def get_reranker() -> CrossEncoder:
    global _reranker

    if _reranker is None:
        model_name = str(MODEL_PATH) if MODEL_PATH.exists() else FALLBACK_MODEL
        _reranker = CrossEncoder(
            model_name,
            trust_remote_code=True,
            device="cpu",
        )

    return _reranker


def rerank(
    query: str,
    documents: list[dict],
    top_k: int = 5,
) -> list[dict]:
    docs_with_text = [
        doc for doc in documents
        if doc.get("text")
    ]

    if not docs_with_text:
        return []

    pairs = [
        (query, doc["text"])
        for doc in docs_with_text
    ]

    reranker = get_reranker()
    scores = reranker.predict(pairs)

    scored_docs = []
    for doc, score in zip(docs_with_text, scores):
        scored_doc = {**doc, "rerank_score": float(score)}
        scored_docs.append(scored_doc)

    scored_docs.sort(
        key=lambda item: item["rerank_score"],
        reverse=True,
    )

    return scored_docs[:top_k]
