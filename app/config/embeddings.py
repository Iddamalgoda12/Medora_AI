from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

# Single source of truth for every embedding-backed workflow in the app.
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
EMBEDDING_MODEL_PATH = BASE_DIR / "AI_MODELS" / "embeddings" / "bge-m3"
EMBEDDING_DIMENSION = 1024
MEM0_COLLECTION_NAME = "mem0_memory_bge_m3_1024"
RAG_COLLECTION_NAME = "documents_bge_m3_1024"
