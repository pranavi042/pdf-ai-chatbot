from pypdf import PdfReader

def extract_pages(pdf_path: str):
    """
    Returns a list of dicts:
    [
      {"page": 1, "text": "..."},
      {"page": 2, "text": "..."},
    ]
    """
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append({"page": i + 1, "text": text})
    return pages


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200):
    """
    Simple character-based chunker (reliable and dependency-free).
    """
    text = text.replace("\x00", " ").strip()
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap)

    return chunks
