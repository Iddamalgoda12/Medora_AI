
from typing import Any

from mem0 import Memory
from app.config.settings import settings
from app.config.embeddings import (
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MODEL_PATH,
    MEM0_COLLECTION_NAME,
)


class MemoryService:
    def __init__(self):
        memory_config = self._build_config()
        self.memory = Memory.from_config(
            memory_config
        )

    def _build_config(self) -> dict[str, Any]:
        llm_provider = settings.LLM_PROVIDER.lower()

        if llm_provider == "gemini":
            llm_config = {
                "provider": "gemini",
                "config": {
                    "api_key": settings.GEMINI_API_KEY,
                    "model": settings.GEMINI_MODEL,
                },
            }
        elif llm_provider == "lmstudio":
            llm_config = {
                "provider": "lmstudio",
                "config": {
                    "model": settings.LMSTUDIO_MODEL,
                    "lmstudio_base_url": settings.LMSTUDIO_BASE_URL,
                },
            }
        elif llm_provider == "groq":
            llm_config = {
                "provider": "groq",
                "config": {
                    "api_key": settings.GROQ_API_KEY,
                    "model": settings.GROQ_MODEL,
                },
            }
        else:
            raise ValueError(f"Unsupported LLM provider for mem0: {settings.LLM_PROVIDER}")

        return {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": settings.QDRANT_URL or "localhost",
                    "port": settings.QDRANT_PORT or 6333,
                    "collection_name": MEM0_COLLECTION_NAME,
                    "embedding_model_dims": EMBEDDING_DIMENSION,
                },
            },
            "llm": llm_config,
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": str(EMBEDDING_MODEL_PATH) if EMBEDDING_MODEL_PATH.exists() else EMBEDDING_MODEL_NAME,
                    "embedding_dims": EMBEDDING_DIMENSION,
                    "model_kwargs": {
                        "device": "cpu",
                    },
                },
            },
            "memory": {
                "custom_prompt": """
                Extract only long-term useful facts.

                Rules:
                - Maximum 25 words.
                - Ignore temporary discussions.
                - Ignore explanations.
                - Store only preferences, goals, skills, projects, profile information.
                - Return concise facts only.
                """.strip(),
            },
        }


memory_service = MemoryService()
