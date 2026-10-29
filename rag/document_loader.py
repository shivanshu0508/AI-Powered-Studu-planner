
from pathlib import Path
from pypdf import PdfReader


def load_pdf(file_path):
    """
    Extract text from a PDF.

    Returns a list of dictionaries, one per page:
    {
        "text": "...",
        "source": "dbms_notes.pdf",
        "page": 1
    }
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    reader = PdfReader(str(path))

    if reader.is_encrypted:
        raise ValueError(
            "This PDF is encrypted. Upload an accessible PDF."
        )

    documents = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = " ".join(text.split())

        if text:
            documents.append({
                "text": text,
                "source": path.name,
                "page": page_number
            })

    if not documents:
        raise ValueError(
            "No extractable text found. "
            "The PDF may be scanned or image-only."
        )

    return documents
