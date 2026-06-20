from pathlib import Path

import pyarrow as pa

if not hasattr(pa, "PyExtensionType"):
    pa.PyExtensionType = pa.ExtensionType

from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

MODEL_PATH = BASE_DIR / "AI_MODELS" / "embeddings" / "bge-m3"

embedding_model = SentenceTransformer(
    str(MODEL_PATH),
    device="cuda",
)


def embed_texts(texts: list[str]):
    return embedding_model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )