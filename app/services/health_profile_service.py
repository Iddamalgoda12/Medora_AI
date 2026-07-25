"""
Single-responsibility service-load, update, and persist the patient health
profile stored in ``data/health_profile.json``.
"""

from __future__ import annotations
from datetime import date
import json
import logging
import re
from pathlib import Path
from app.llms.llm import ask_llm

logger = logging.getLogger(__name__)

PROFILE_PATH: Path = (
    Path(__file__).resolve().parent.parent.parent / "data" / "health_profile.json"
)

_REQUIRED_KEYS: frozenset[str] = frozenset(
    {"conditions", "medicines", "allergies", "last_updated"}
)

_DEFAULT_PROFILE: dict = {
    "status": "🟢 Stable",
    "conditions": [],
    "medicines": [],
    "allergies": [],
    "last_updated": "Never",
    "notes": "",    
}


def load_health_profile() -> dict:
    """Return the current health profile.

    If the file is missing or contains invalid JSON it is treated as empty and
    the default skeleton is returned without overwriting the file.
    """
    if not PROFILE_PATH.exists() or PROFILE_PATH.stat().st_size == 0:
        logger.info("Health profile not found or empty – returning default.")
        return dict(_DEFAULT_PROFILE)

    try:
        with PROFILE_PATH.open("r", encoding="utf-8") as fh:
            profile = json.load(fh)
        if not isinstance(profile, dict):
            raise ValueError("Health profile must be a JSON object.")
        return profile
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Could not parse health profile (%s) – returning default.", exc)
        return dict(_DEFAULT_PROFILE)


def save_health_profile(profile: dict) -> None:
    """updates health profile.json file

    Args:
        profile: The updated health-profile dictionary.

    Raises:
        ValueError: If *profile* is not a dict or is missing required keys.
    """
    if not isinstance(profile, dict):
        raise ValueError(f"Profile must be a dict, got {type(profile).__name__}.")

    missing = _REQUIRED_KEYS - profile.keys()
    if missing:
        raise ValueError(
            f"Profile is missing required keys: {', '.join(sorted(missing))}."
        )

    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write to a sibling temp file then rename for atomicity.
    tmp = PROFILE_PATH.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(profile, fh, indent=2, ensure_ascii=False)
        tmp.replace(PROFILE_PATH)
        logger.info("Health profile saved → %s", PROFILE_PATH)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Gemini-powered update
# ---------------------------------------------------------------------------

def _extract_json_block(text: str) -> str:
    """Strip markdown fences and leading/trailing whitespace from LLM output."""
    """ llm output eke hriyata awshya kella ganimata"""
    # Try ```json ... ``` first, then bare ```...```
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if match:
        return match.group(1).strip()
    return text.strip()


async def update_profile_from_report(report_text: str) -> dict:
    """Ask Gemini to merge *report_text* into the current health profile.

    Workflow:
    1. Load the existing profile from disk.
    2. Send both the profile and the extracted report text to Gemini.
    3. Parse and validate the returned JSON.
    4. Save the updated profile to disk.

    Args:
        report_text: Full text extracted from one or more PDF medical reports.

    Returns:
        The updated health-profile dictionary.

    Raises:
        json.JSONDecodeError: If Gemini returns malformed JSON after cleanup.
        ValueError: If the returned object fails validation.
    """
    existing_profile = load_health_profile()
    # Get today's date from Python
    today = date.today().isoformat()

    prompt = f"""You are a medical AI assistant. Your job is to update a patient's
    health profile based on a newly uploaded medical report.

    ## Existing Health Profile (JSON)
    {json.dumps(existing_profile, indent=2)}

    ## Newly Uploaded Medical Report Text
    {report_text}

    ## Instructions
    1. Carefully read the report and extract all medically relevant information.
    2. Merge it with the existing profile.  Never remove previously recorded data
    unless the report explicitly contradicts it.
    3. Populate / extend the following fields:
    - - "status": Set the patient's overall status as one of: "🟢 Stable", "🟡 Monitor", or "🔴 Critical", based only on the medical evidence in the reports.
    - "conditions"   : list of diagnosed conditions or diseases (strings)
    - "medicines"    : list of prescribed or mentioned medications (strings)
    - "allergies"    : list of recorded allergies (strings)
    - "notes"        : any other clinically relevant observations (string)
    - You may add additional top-level keys if they capture important data
        (e.g. "lab_results", "vitals").
    4. Do NOT include a "last_updated" field – it is set by the system automatically.
    5. Return ONLY a single valid JSON object – no markdown, no explanation.
    """

    raw_response = ask_llm(prompt)
    clean_json = _extract_json_block(raw_response)

    updated_profile: dict = json.loads(clean_json)
    updated_profile["last_updated"] = today

    # Ensure required keys are present after merge.
    for key in _REQUIRED_KEYS:
        if key not in updated_profile:
            updated_profile[key] = existing_profile.get(key, _DEFAULT_PROFILE[key])

    save_health_profile(updated_profile)
    logger.info("Health profile updated successfully.")
    return updated_profile


# ---------------------------------------------------------------------------
# Chainlit sidebar helper
# ---------------------------------------------------------------------------

def format_profile_for_sidebar(profile: dict) -> str:
    """json file eka chainlit ui eke sidebar eke display karanna markdown format ekata convert karana function ekak"""
    status = profile.get("status", "⚪ Need more info")
    conditions = profile.get("conditions") or []
    medicines = profile.get("medicines") or []
    allergies = profile.get("allergies") or []
    last_updated = profile.get("last_updated", "Never")
    notes = profile.get("notes", "")

    def _bullet_list(items: list, empty_msg: str = "None") -> str:
        if not items:
            return f"- {empty_msg}"
        return "\n".join(f"- {item}" for item in items)

    markdown = f"""# 🩺 Your Health Profile

    **Status:** {status}

    ## Conditions
    {_bullet_list(conditions)}

    ## Medicines
    {_bullet_list(medicines)}

    ## Allergies
    {_bullet_list(allergies)}
    """

    if notes:
        markdown += f"\n## Notes\n{notes}\n"

    # Append any extra keys (e.g. lab_results, vitals).
    known_keys = {"status", "conditions", "medicines", "allergies", "last_updated", "notes"}
    extra = {k: v for k, v in profile.items() if k not in known_keys}
    for key, value in extra.items():
        title = key.replace("_", " ").title()
        if isinstance(value, list):
            markdown += f"\n## {title}\n{_bullet_list(value)}\n"
        else:
            markdown += f"\n## {title}\n{value}\n"

    markdown += f"\n## Last Updated\n{last_updated}"
    return markdown
