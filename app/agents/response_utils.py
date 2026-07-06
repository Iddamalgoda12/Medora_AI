def append_agent_response(previous: str, current: str) -> str:
    """Preserve results when several agents run for one user request."""
    if not previous:
        return current.strip()
    if not current:
        return previous.strip()
    return f"{previous.strip()}\n\n---\n\n{current.strip()}"
