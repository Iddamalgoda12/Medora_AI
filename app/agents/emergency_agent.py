from pydantic import BaseModel, Field

from app.graphs.state import State
from app.llms.llm import ask_llm_async


class EmergencyDecision(BaseModel):
    is_emergency: bool = Field(description="True if the situation is a medical emergency.")
    is_uncertain: bool = Field(description="True if the model cannot confidently decide.")
    assessment: str = Field(description="Short explanation of why it is or is not an emergency.")
    immediate_advice: str = Field(description="Critical advice for the current situation.")
    should_call_emergency_services: bool = Field(description="Whether the user should call emergency services now.")
    call_script: str = Field(description="A short prototype emergency call script if needed, otherwise empty.")
    emergency_call_summary: str = Field(description="A short dispatcher-style summary if the situation is confirmed as an emergency.")
    clarification_question: str = Field(description="A targeted follow-up question when the model is uncertain.")


def _is_affirmative(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {
        "yes",
        "y",
        "yeah",
        "yep",
        "confirm",
        "confirmed",
        "ok",
        "okay",
        "please do",
        "call",
        "call it",
        "do it",
        "call emergency services",
        "yes please",
    }


def _is_negative(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in {
        "no",
        "n",
        "nope",
        "not now",
        "don't",
        "do not",
        "no thanks",
        "not yet",
        "stop",
    }


async def emergency_agent(state: State):
    """
    Emergency agent handles critical health situations.
    """
    query = state["query"]

    if state.get("emergency_confirmation_pending"):
        if _is_affirmative(query):
            confirmed_steps = [
                state.get("emergency_assessment", "This appears to be a medical emergency."),
                "Calling emergency services now.",
                "Prototype emergency call: Dispatcher, I am having a medical emergency and need immediate help. My address is [Your Address].",
                "Prototype dispatcher summary: Patient consented to emergency escalation. Immediate assistance requested.",
            ]

            return {
                **state,
                "emergency_confirmation_pending": False,
                "emergency_flag": True,
                "emergency_steps": confirmed_steps,
                "emergency_call_prototype": {
                    "should_call_emergency_services": True,
                    "call_script": (
                        "Dispatcher, I am having a medical emergency and need immediate help. "
                        "My address is [Your Address]."
                    ),
                    "emergency_call_summary": (
                        "Patient consented to emergency escalation. Immediate assistance requested."
                    ),
                },
                "response": "\n\n".join(confirmed_steps),
                "final_response": "\n\n".join(confirmed_steps),
                "execution_trace": [
                    *state["execution_trace"],
                    "emergency_agent",
                ],
            }

        if _is_negative(query):
            decline_steps = [
                state.get("emergency_assessment", "This could still be serious."),
                "Emergency call not placed.",
                "If symptoms worsen or you change your mind, call emergency services immediately.",
            ]

            return {
                **state,
                "emergency_confirmation_pending": False,
                "emergency_flag": False,
                "emergency_steps": decline_steps,
                "emergency_call_prototype": {
                    "should_call_emergency_services": False,
                    "call_script": "",
                    "emergency_call_summary": "",
                },
                "response": "\n\n".join(decline_steps),
                "final_response": "\n\n".join(decline_steps),
                "execution_trace": [
                    *state["execution_trace"],
                    "emergency_agent",
                ],
            }

    emergency_prompt = f"""
You are a medical emergency triage assistant.

Analyze the user's message and decide whether this sounds like a true emergency.

Rules:
- If it is likely an emergency, set is_emergency to true and should_call_emergency_services to true.
- If it does not sound like an emergency, set is_emergency to false and should_call_emergency_services to false.
- If the message is ambiguous or missing important details, set is_uncertain to true and ask one focused clarification question.
- In either case, give practical, immediate health guidance.
- If it is an emergency, also create a short prototype emergency call script that the user could read to a dispatcher.
- If it is an emergency, also create a short dispatcher-style summary that can be used as a prototype call message.
- Keep the assessment concise and serious.

Return only JSON with this schema:
{{
  "is_emergency": true,
  "is_uncertain": false,
  "assessment": "",
  "immediate_advice": "",
  "should_call_emergency_services": true,
  "call_script": "",
  "emergency_call_summary": "",
  "clarification_question": ""
}}

User Query:
{query}
"""

    raw_response = await ask_llm_async(emergency_prompt)

    try:
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        decision = EmergencyDecision.model_validate_json(cleaned)
    except Exception:
        decision = EmergencyDecision(
            is_emergency=True,
            is_uncertain=False,
            assessment="The situation may require urgent medical attention.",
            immediate_advice=(
                "Move to a safe place, do not drive yourself if you feel faint, and "
                "seek urgent medical help right away."
            ),
            should_call_emergency_services=True,
            call_script=(
                "Hello, I need emergency medical help. The patient may be in a "
                "critical condition and needs immediate assistance."
            ),
            emergency_call_summary=(
                "This is a medical emergency. The patient needs immediate help."
            ),
            clarification_question="",
        )

    if decision.is_uncertain:
        followup_question = (
            decision.clarification_question
            or "Can you tell me the main symptom and how severe it is right now?"
        )
        emergency_steps = [
            decision.assessment,
            followup_question,
            "If the situation becomes severe, call emergency services immediately.",
        ]

        return {
            **state,
            "emergency_flag": False,
            "emergency_assessment": decision.assessment,
            "emergency_call_prototype": {
                "should_call_emergency_services": False,
                "call_script": "",
                "emergency_call_summary": "",
            },
            "emergency_steps": emergency_steps,
            "needs_user_input": True,
            "followup_question": followup_question,
            "final_response": "\n\n".join(emergency_steps),
            "response": "\n\n".join(emergency_steps),
            "execution_trace": [
                *state["execution_trace"],
                "emergency_agent"
            ]
        }

    if decision.is_emergency and decision.should_call_emergency_services:
        emergency_steps = [
            decision.assessment,
            decision.immediate_advice,
            "Do you want me to call emergency services now?",
        ]
        call_summary = (
            decision.emergency_call_summary
            or "This is a medical emergency. Please send help immediately."
        )
    else:
        emergency_steps = [
            decision.assessment,
            decision.immediate_advice,
            "If symptoms worsen or new danger signs appear, call emergency services immediately.",
        ]

    return {
        **state,
        "emergency_flag": decision.is_emergency,
        "emergency_assessment": decision.assessment,
        "emergency_call_prototype": {
            "should_call_emergency_services": decision.should_call_emergency_services,
            "call_script": decision.call_script if decision.is_emergency else "",
            "emergency_call_summary": (
                decision.emergency_call_summary if decision.is_emergency else ""
            ),
        },
        "emergency_steps": emergency_steps,
        "emergency_confirmation_pending": bool(
            decision.is_emergency and decision.should_call_emergency_services
        ),
        "emergency_pending_call": {
            "call_script": decision.call_script if decision.is_emergency else "",
            "emergency_call_summary": (
                decision.emergency_call_summary if decision.is_emergency else ""
            ),
        },
        "response": "\n\n".join(emergency_steps),
        "final_response": "\n\n".join(emergency_steps),
        "execution_trace": [
            *state["execution_trace"],
            "emergency_agent"
        ]
    }
