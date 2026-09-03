from functools import lru_cache

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_server(
    name: str,
    description: str,
    tags: list[str],
) -> list[float]:
    document = f"{name} {description} {' '.join(tags)}"
    vector = _get_model().encode(document)

    return vector.tolist()
