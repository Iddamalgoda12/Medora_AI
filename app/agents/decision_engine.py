from pydantic import BaseModel, Field

from app.llms.gemini import get_llm

llm = get_llm()


class DecisionOutput(BaseModel):

    doctor_agent: int = Field(
        ge=0,
        le=10
    )

    pharmacy_agent: int = Field(
        ge=0,
        le=10
    )

    report_agent: int = Field(
        ge=0,
        le=10
    )

    emergency_agent: int = Field(
        ge=0,
        le=10
    )

    direct_answer: int = Field(
        ge=0,
        le=10
    )


def decision_engine(state):

    pending_tasks = state.get(
        "pending_tasks",
        []
    )

    completed_tasks = state.get(
        "completed_tasks",
        []
    )

    if pending_tasks:

        next_task = pending_tasks[0]

        return {
            **state,
            "next_task": next_task,
            "execution_trace": [
                *state["execution_trace"],
                f"decision->{next_task}"
            ]
        }

    query = state["query"]

    structured_llm = llm.with_structured_output(
        DecisionOutput
    )

    result = structured_llm.invoke(
        f"""
You are the task planning engine of MedoraAI.

Score each task from 0-10 based on the user's primary intent.

doctor_agent:
- doctors
- specialists
- hospitals
- appointments

pharmacy_agent:
- medicines
- pharmacies
- medicine availability
- medicine ordering

report_agent:
- blood reports
- lab reports
- scans
- medical documents

emergency_agent:
- chest pain
- breathing difficulty
- stroke symptoms
- severe bleeding
- life-threatening emergencies

direct_answer:
- disease explanations
- medicine explanations
- health education
- prevention tips
- lifestyle advice
- general medical knowledge
- informational questions

Rules:
- Give the highest score to the task that best matches the user's main intent.
- If the user only wants information or an explanation, give direct_answer the highest score and keep other agents low (0-2).
- Only give high scores to doctor_agent, pharmacy_agent, report_agent, or emergency_agent when the user needs that service.
- Multiple agents may receive high scores if clearly needed.

User Request:
{query}

Return only the scores.
"""
    )

    scores = DecisionOutput.model_validate(
        result
    ).model_dump()

    max_score = max(
        scores.values()
    )

    # ----------------------------------
    # Direct answer route
    # ----------------------------------

    if scores["direct_answer"] >= max_score:

        return {
            **state,

            "pending_tasks": [],

            "next_task":
                "direct_answer",

            "decision_scores":
                scores,

            "execution_trace": [
                *state["execution_trace"],
                "decision->direct_answer"
            ]
        }

    # ----------------------------------
    # Clarification needed
    # ----------------------------------

    if max_score < 3:

        return {
            **state,

            "next_task":
                "clarifier_agent",

            "pending_tasks":
                [],

            "decision_scores":
                scores,

            "execution_trace": [
                *state["execution_trace"],
                "decision->clarifier_agent"
            ]
        }

    # ----------------------------------
    # Emergency override
    # ----------------------------------

    if scores["emergency_agent"] >= 8:

        pending_tasks = [
            "emergency_agent",
            "doctor_agent"
        ]

        return {
            **state,

            "pending_tasks":
                pending_tasks,

            "next_task":
                "emergency_agent",

            "decision_scores":
                scores,

            "execution_trace": [
                *state["execution_trace"],
                "decision->emergency_agent"
            ]
        }

    # ----------------------------------
    # Normal planning
    # ----------------------------------

    pending_tasks = [
        task
        for task, score in scores.items()
        if (
            task != "direct_answer"
            and score >= max_score - 1
        )
    ][:3]

    if not pending_tasks:

        return {
            **state,

            "next_task":
                "clarifier_agent",

            "pending_tasks":
                [],

            "decision_scores":
                scores,

            "execution_trace": [
                *state["execution_trace"],
                "decision->clarifier_agent"
            ]
        }

    next_task = pending_tasks[0]

    return {
        **state,

        "pending_tasks":
            pending_tasks,

        "completed_tasks":
            completed_tasks,

        "next_task":
            next_task,

        "decision_scores":
            scores,

        "execution_trace": [
            *state["execution_trace"],
            f"decision->{next_task}"
        ]
    }