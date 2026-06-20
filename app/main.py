import asyncio

from app.llms.gemini import get_llm

                                                                                       
async def main():
    llm = get_llm()

    response = await llm.ainvoke("Say hello and tell me you are working.")

    print("\n===== RESPONSE =====\n")
    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())