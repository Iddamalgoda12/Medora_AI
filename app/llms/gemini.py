from langchain_google_genai import ChatGoogleGenerativeAI
from app.config.settings import settings

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.5,
)


def get_llm(temperature=0.5):
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=temperature,
    )


def ask_gemini(prompt: str) -> str:
    response = llm.invoke(prompt)
    return response.content


async def ask_gemini_async(prompt: str) -> str:
    response = await llm.ainvoke(prompt)
    return response.content