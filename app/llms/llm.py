from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

from app.config.settings import settings


def get_llm(temperature=0.5):
    if settings.LLM_PROVIDER.lower() == "gemini":
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
        )

    elif settings.LLM_PROVIDER.lower() == "lmstudio":
        return ChatOpenAI(
            model=settings.LMSTUDIO_MODEL,
            base_url=settings.LMSTUDIO_BASE_URL,
            api_key=settings.LMSTUDIO_API_KEY,
            temperature=temperature,
        )
    elif settings.LLM_PROVIDER.lower() == "groq":
        return ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=temperature,
        )

    raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")


# Default LLM instance
llm = get_llm()


def ask_llm(prompt: str) -> str:
    response = llm.invoke(prompt)
    return response.content


async def ask_llm_async(prompt: str) -> str:
    response = await llm.ainvoke(prompt)
    return response.content