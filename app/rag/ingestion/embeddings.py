from pathlib import Path

import pyarrow as pa

if not hasattr(pa, "PyExtensionType"):
    pa.PyExtensionType = pa.ExtensionType

import torch
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_PATH = BASE_DIR / "AI_MODELS" / "embeddings" / "bge-m3"
FALLBACK_MODEL = "BAAI/bge-m3"

_embedding_model = None


def _resolve_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model

    if _embedding_model is None:
        device = _resolve_device()
        model_name = str(MODEL_PATH) if MODEL_PATH.exists() else FALLBACK_MODEL
        _embedding_model = SentenceTransformer(model_name, device=device)

    return _embedding_model


def embed_texts(texts: list[str]):
    if not texts:
        return []

    model = get_embedding_model()
    return model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
