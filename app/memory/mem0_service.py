# app/memory/mem0_service.py

from mem0 import Memory
from app.config.settings import settings


class MemoryService:
    def __init__(self):
        self.memory = Memory.from_config(
            {
                "llm": {
                    "provider": "gemini",
                    "config": {
                        "api_key": settings.GEMINI_API_KEY,
                        "model": "gemini-2.5-flash",
                    },
                },
                "embedder": {
                    "provider": "huggingface",
                    "config": {
                        "model": "/home/iddamalgoda/Desktop/AI_MODELS/embeddings/bge-m3",
                        "model_kwargs": {
                            "device": "cpu"
                        }
                    },
                },

                # Add memory configuration here
                "memory": {
                    "custom_prompt": """
                    Extract only long-term useful facts.

                    Rules:
                    - Maximum 1 sentence per memory.
                    - Maximum 20 words.
                    - Ignore temporary discussions.
                    - Ignore explanations.
                    - Store only preferences, goals, skills, projects, profile information.
                    - Return concise facts only.
                    """
                },
            }
        )


memory_service = MemoryService()