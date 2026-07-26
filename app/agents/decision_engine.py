from pydantic import BaseModel, Field

from app.llms.llm import get_llm
from app.memory.conversation import last_exchange_context

llm = get_llm(0.1)


def enforce_explicit_service_intents(query, scores):
    """Protect clear multi-service requests from inconsistent LLM scoring."""
    normalized_query = query.lower()
    appointment_terms = ("doctor", "appointment", "specialist", "hospital")
    pharmacy_terms = ("pharmacy", "chemist", "medicine", "medication", "drug")

    if any(term in normalized_query for term in appointment_terms):
        scores["appointment_agent"] = max(scores["appointment_agent"], 8)
    if any(term in normalized_query for term in pharmacy_terms):
        scores["pharmacy_agent"] = max(scores["pharmacy_agent"], 8)

    return scores


class DecisionOutput(BaseModel):

    appointment_agent: int = Field(
        ge=0,
        le=10
    )

    pharmacy_agent: int = Field(
        ge=0,
        le=10
    )

    RAG_agent: int = Field(
        ge=0,
        le=10
    )

    emergency_agent: int = Field(
        ge=0,
        le=10
    )

    clarifier_agent: int = Field(
        ge=0,
        le=10
    )

    direct_answer: int = Field(
        ge=0,
        le=10
    )


async def decision_engine(state):

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
            "pending_tasks": pending_tasks[1:],
            "completed_tasks": [
                *completed_tasks,
                next_task,
            ],
            "execution_trace": [
                *state["execution_trace"],
                f"decision->{next_task}"
            ]
        }

    query = state["query"]
    conversation_context = last_exchange_context(state.get("chat_history", []))

    structured_llm = llm.with_structured_output(
        DecisionOutput
    )

    result = await structured_llm.ainvoke(
        f"""
    You are the task planning engine of MedoraAI.

    Score each task from 0-10 based on the user's primary intent.

    appointment_agent:
    - doctors
    - specialists
    - hospitals
    - appointments

    pharmacy_agent:
    - medicines
    - pharmacies
    - medicine availability
    - medicine ordering

    RAG_agent:
    - questions about uploaded PDF medical reports or lab documents
    - blood reports, lab results, scan reports, clinical documents
    - interpreting values or findings from stored medical documents
    - "what does my report say", "explain my test results from the document"

    emergency_agent:
    - chest pain
    - breathing difficulty
    - stroke symptoms
    - severe bleeding
    - life-threatening emergencies

    clarifier_agent:
    - vague or incomplete health concerns
    - symptom statements that need follow-up before advice can be useful
    - unclear requests where the user has not provided enough detail to choose the right service
    - examples like "I'm not feeling too well" when the user has not said what symptoms they have
    - Use clarifier_agent ONLY when the user's request is healthcare-related and additional information is required before a safe or useful response can be given.
    - Never choose clarifier_agent for greetings, identity questions, capability questions, or general conversation.

    direct_answer:
    - disease explanations
    - medicine explanations
    - health education
    - prevention tips
    - lifestyle advice
    - general medical knowledge
    - informational questions not tied to a specific uploaded report
    - questions about MedoraAI or the assistant itself
    - greetings, introductions, capabilities, and general conversation

    Rules:
    - Give the highest score to the task that best matches the user's main intent.
    - If the user asks about their report, lab PDF, or document content, give RAG_agent the highest score.
    - If the user only wants general information or an explanation, give direct_answer the highest score and keep other agents low (0-2).
    - If the user only says they feel unwell or not well without enough symptom detail, give clarifier_agent the highest score.
    - Only give high scores to appointment_agent, pharmacy_agent, RAG_agent, or emergency_agent when the user needs that service.
    - Multiple agents may receive high scores if clearly needed.
    - Use clarifier_agent when more information is needed before giving a safe or useful next step.
    - Give every explicitly requested service a score of at least 8, even when the
    same request contains another service. For example, asking to see a doctor
    and visit a pharmacy must score both appointment_agent and pharmacy_agent highly.

    User Request:
    {query}

    Previous Exchange (use it to resolve follow-up wording and references):
    {conversation_context}

    Return only the scores.
    """
    )

    scores = DecisionOutput.model_validate(
        result
    ).model_dump()

    scores = enforce_explicit_service_intents(query, scores)

    max_score = max(
        scores.values()
    )

    # ----------------------------------
    # Direct answer route. A concrete service request takes precedence even
    # when direct_answer receives the same score.
    # ----------------------------------

    service_scores = {                                #takes without direct_answer and clarifier_agent
        task: score
        for task, score in scores.items()
        if task not in {"direct_answer", "clarifier_agent"}
    }
    task_order = [
        "emergency_agent",
        "appointment_agent",
        "pharmacy_agent",
        "RAG_agent",
    ]
    requested_services = [                           #tkakes only >5 from service_scores
        task
        for task in task_order
        if service_scores[task] >= 5
    ]

    if scores["clarifier_agent"] >= max_score and scores["clarifier_agent"] >= 5:
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

    if not requested_services and scores["direct_answer"] >= max_score:

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
        return {
            **state,

            "pending_tasks":
                [],

            "next_task":
                "emergency_agent",

            "completed_tasks":
                completed_tasks,

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

    pending_tasks = requested_services[:3]

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
            pending_tasks[1:],

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
