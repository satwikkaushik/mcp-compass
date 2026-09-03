from functools import lru_cache

from google import genai
from google.genai import types

from app.core.config import settings

EMBEDDING_MODEL_NAME = "gemini-embedding-001"
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def _embed(text: str) -> list[float]:
    response = _get_client().models.embed_content(
        model=EMBEDDING_MODEL_NAME,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
    )
    return response.embeddings[0].values


def embed_server(
    name: str,
    description: str,
    tags: list[str],
) -> list[float]:
    document = f"{name} {description} {' '.join(tags)}"
    return _embed(document)


def embed_text(text: str) -> list[float]:
    return _embed(text)
