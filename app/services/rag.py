from functools import lru_cache

from google import genai
from google.genai import types

from app.core.config import settings
from app.models.server import McpServer

GENERATION_MODEL = "gemini-3.5-flash"

SYSTEM_PROMPT = (
    "You are a discovery assistant for an internal MCP server registry. "
    "Answer the user's query using ONLY the candidate servers listed below. "
    "If none of them are a good fit, say so plainly instead of guessing. "
    "Be concise - 2-3 sentences."
)


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def _format_candidates(servers: list[McpServer]) -> str:
    blocks = []

    for s in servers:
        blocks.append(
            f"- name: {s.name}\n"
            f"  description: {s.description}\n"
            f"  tags: {', '.join(s.tags)}\n"
            f"  endpoint_url: {s.endpoint_url}\n"
            f"  connectivity_status: {s.connectivity_status}"
        )

    return "\n".join(blocks)


def generate_discovery_answer(query: str, servers: list[McpServer]) -> str:
    if not servers:
        return "No matching servers were found in the registry for this query."

    candidates = _format_candidates(servers)

    user_message = f"User query: {query}\n\nCandidate servers: {candidates}"

    response = _get_client().models.generate_content(
        model=GENERATION_MODEL,
        contents=user_message,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )

    return response.text or ""
