
def split_documents(
    documents,
    chunk_size=800,
    chunk_overlap=150
):
    """
    Split page-level documents into smaller text chunks.

    chunk_size and chunk_overlap are measured in characters,
    not tokens.

    Each chunk retains its original source and page number.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be non-negative "
            "and smaller than chunk_size."
        )

    chunks = []
    step = chunk_size - chunk_overlap

    for document in documents:
        text = document["text"].strip()

        if not text:
            continue

        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Prefer ending at a word boundary when possible.
            if end < len(text):
                boundary = text.rfind(" ", start, end)

                if boundary > start:
                    end = boundary

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "source": document["source"],
                    "page": document["page"],
                    "chunk_id": len(chunks)
                })

            if end >= len(text):
                break

            # Maintain overlap between adjacent chunks.
            start = max(start + 1, end - chunk_overlap)

    return chunks
