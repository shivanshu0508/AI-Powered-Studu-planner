
from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load the embedding model once per Python process."""
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts):
    """Convert a list of text strings into embeddings."""

    if not texts:
        return []

    model = get_embedding_model()

    vectors = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    return vectors


def embed_query(query):
    """Convert one question into a normalized embedding."""

    if not query or not query.strip():
        raise ValueError("The query cannot be empty.")

    model = get_embedding_model()

    vector = model.encode(
        [query.strip()],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    return vector
