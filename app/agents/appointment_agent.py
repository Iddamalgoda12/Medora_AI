import json

from app.graphs.state import AgentState
from app.llms.gemini import ask_gemini
from app.tools.doctor_search import search_doctors


async def extract_appointment_info(query: str):

    prompt = f"""
You are a healthcare assistant.

Extract the following information.

Return ONLY JSON.

Schema:

{{
    "specialty": "",
    "location": ""
}}

Query:
{query}
"""

    response = ask_gemini(prompt)

    try:

        cleaned = response.strip()

        if cleaned.startswith("```json"):
            cleaned = (
                cleaned
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

        return json.loads(cleaned)

    except Exception:

        return {
            "specialty": "",
            "location": ""
        }


async def rank_doctors(results):

    recommendations = []

    for item in results[:3]:

        recommendations.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "summary": item.get("content", "")
        })

    return recommendations

async def appointment_agent(state: AgentState):

    query = state["query"]

    extracted = await extract_appointment_info(
        query
    )

    specialty = state.get("specialty") or extracted.get(
        "specialty",
        ""
    )

    location = state.get("location") or extracted.get(
        "location",
        ""
    )

    if not specialty and not location:
        question = "Which specialist would you like to see and in which city?"
        return {
            **state,
            "specialty": specialty,
            "location": location,
            "needs_user_input": True,
            "followup_question": question,
            "response": question,
            "execution_trace": [
                *state["execution_trace"],
                "appointment_agent"
            ]
        }

    if not specialty:
        question = "What type of specialist would you like to see?"
        return {
            **state,
            "specialty": specialty,
            "location": location,
            "needs_user_input": True,
            "followup_question": question,
            "response": question,
            "execution_trace": [
                *state["execution_trace"],
                "appointment_agent"
            ]
        }

    if not location:
        question = "Which city would you like the appointment in?"
        return {
            **state,
            "specialty": specialty,
            "location": location,
            "needs_user_input": True,
            "followup_question": question,
            "response": question,
            "execution_trace": [
                *state["execution_trace"],
                "appointment_agent"
            ]
        }

    search_results = await search_doctors(
        specialty=specialty,
        location=location
    )

    recommendations = await rank_doctors(
        search_results
    )

    response_text = f"Here are some recommended {specialty} doctors in {location}:\n\n"
    for i, rec in enumerate(recommendations, 1):
        response_text += f"{i}. **{rec['title']}**\n   {rec['summary']}\n   [Link]({rec['url']})\n\n"

    return {
        **state,
        "specialty": specialty,
        "location": location,
        "needs_user_input": False,
        "doctor_results": recommendations,
        "response": response_text.strip(),
        "execution_trace": [
            *state["execution_trace"],
            "appointment_agent"
        ]
    }