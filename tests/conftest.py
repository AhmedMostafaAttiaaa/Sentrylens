import pytest


@pytest.fixture
def sample_text() -> str:
    return (
        "Enterprise search platforms combine retrieval and generation. "
        "They index documents, embed chunks, and answer questions. "
        "Guardrails protect against prompt injection and data leakage. "
        "The system should degrade gracefully when a provider is unavailable."
    )
