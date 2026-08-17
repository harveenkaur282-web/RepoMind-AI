from __future__ import annotations

# Strategy templates dict mapping strategy name to system prompt content
PROMPT_STRATEGIES = {
    "concise_grounded": (
        "Answer the user's question using only the provided repository context. "
        "Be concise and do not invent information."
    ),
    "detailed_grounded": (
        "Answer using only the provided repository context, with enough technical explanation "
        "to be useful to a developer. Explicitly say when the context is insufficient."
    ),
    "developer_assistant": (
        "Act as a senior developer helping understand the repository. Give a clear answer, "
        "reference relevant file paths when available, distinguish retrieved evidence from "
        "inference, and avoid unsupported claims."
    ),
}


def get_system_prompt(strategy: str) -> str:
    """Return the system prompt for the configured strategy name."""
    if strategy not in PROMPT_STRATEGIES:
        raise ValueError(
            f"Invalid prompt strategy: '{strategy}'. "
            f"Must be one of: {list(PROMPT_STRATEGIES.keys())}"
        )
    return PROMPT_STRATEGIES[strategy]
