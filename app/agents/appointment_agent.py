import json

from app.graphs.state import State
from app.llms.llm import ask_llm_async
from app.tools.doctor_search import search_doctors
from app.agents.response_utils import append_agent_response


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

    response = await ask_llm_async(prompt)

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

async def appointment_agent(state: State):

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

    # Generic intent words are not usable booking details. Extraction models
    # may otherwise interpret "see a doctor and go to a pharmacy" as a
    # specialty/location pair and incorrectly finish this task.
    if str(specialty).strip().lower() in {
        "doctor", "a doctor", "physician", "specialist", "general",
        "none", "n/a", "unknown",
    }:
        specialty = ""
    if str(location).strip().lower() in {
        "pharmacy", "a pharmacy", "hospital", "clinic", "doctor",
        "none", "n/a", "unknown",
    }:
        location = ""

    if not specialty and not location:
        question = "Which specialist would you like to see and in which city?"
        return {
            **state,
            "specialty": specialty,
            "location": location,
            "needs_user_input": True,
            "pending_tasks": ["appointment_agent", *state.get("pending_tasks", [])],
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
            "pending_tasks": ["appointment_agent", *state.get("pending_tasks", [])],
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
            "pending_tasks": ["appointment_agent", *state.get("pending_tasks", [])],
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
        "response": append_agent_response(
            state.get("response", ""),
            response_text,
        ),
        "execution_trace": [
            *state["execution_trace"],
            "appointment_agent"
        ]
    }
