from app.graphs.state import State
from app.llms.gemini import ask_gemini_async
from app.memory.conversation import last_exchange_context


async def direct_answer_agent(state: State):
    """
    Direct answer agent handles general medical questions and health education.
    """
    query = state["query"]
    conversation_context = last_exchange_context(state.get("chat_history", []))
    
    answer_prompt = f"""
You are a knowledgeable medical information assistant.

Answer the user's medical question or health inquiry with clear, accurate information.

Provide:
1. Direct answer to their question
2. Key facts and explanations
3. When professional medical consultation is needed
4. Credible sources if applicable

User Query:
{query}

Previous Exchange:
{conversation_context}

Use the previous exchange only when relevant to the current query.

Be informative but remind them this is not a substitute for professional medical advice.
"""

    response = await ask_gemini_async(answer_prompt)

    return {
        **state,
        "response": response,
        "execution_trace": [
            *state["execution_trace"],
            "direct_answer_agent"
        ]
    }
