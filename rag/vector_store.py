
import json
from pathlib import Path

import faiss
import numpy as np

from rag.embeddings import embed_texts, embed_query


VECTOR_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "vector_store"
)

INDEX_PATH = VECTOR_DIR / "study_notes.index"
METADATA_PATH = VECTOR_DIR / "study_notes.json"


def _ensure_directory():
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)


def build_vector_store(chunks):
    """
    Build a FAISS index from text chunks and save it.

    Each chunk must contain:
    text, source, page, chunk_id
    """

    if not chunks:
        raise ValueError("No chunks provided for indexing.")

    texts = [chunk["text"] for chunk in chunks]
    vectors = embed_texts(texts)

    vectors = np.asarray(vectors, dtype=np.float32)

    if vectors.ndim != 2 or len(vectors) != len(chunks):
        raise ValueError("Embedding dimensions or count are invalid.")

    # Vectors are normalized, so inner product gives cosine similarity.
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    _ensure_directory()

    # Save index and metadata in matching order.
    faiss.write_index(index, str(INDEX_PATH))

    with METADATA_PATH.open("w", encoding="utf-8") as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)

    return len(chunks)


def load_vector_store():
    """Load the saved FAISS index and its metadata."""

    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError(
            "Vector store not found. Upload and index a PDF first."
        )

    index = faiss.read_index(str(INDEX_PATH))

    with METADATA_PATH.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    if index.ntotal != len(metadata):
        raise ValueError(
            "Index and metadata do not match. Rebuild the vector store."
        )

    return index, metadata


def search_vectors(query, top_k=4):
    """
    Return the most similar document chunks for a question.

    Each result contains source text and similarity score.
    """

    if not query or not query.strip():
        raise ValueError("The search query cannot be empty.")

    if top_k <= 0:
        raise ValueError("top_k must be positive.")

    index, metadata = load_vector_store()

    if index.ntotal == 0:
        return []

    query_vector = np.asarray(
        embed_query(query),
        dtype=np.float32
    )

    k = min(top_k, index.ntotal)
    scores, indices = index.search(query_vector, k)

    results = []

    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue

        result = dict(metadata[int(idx)])
        result["score"] = float(score)
        results.append(result)

    return results
