from io import BytesIO
from fastapi import HTTPException

MAX_BYTES = 8 * 1024 * 1024

def extract_document(filename: str, content: bytes) -> str:
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "File exceeds the 8 MB limit.")
    suffix = (filename or "").lower().rsplit(".", 1)[-1]
    try:
        if suffix == "pdf":
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            if doc.is_encrypted:
                raise HTTPException(422, "Encrypted PDFs are not supported.")
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
        elif suffix == "docx":
            from docx import Document
            text = "\n".join(p.text for p in Document(BytesIO(content)).paragraphs)
        elif suffix in {"txt", "md"}:
            text = content.decode("utf-8-sig")
        else:
            raise HTTPException(415, "Unsupported file type. Upload PDF, DOCX, or TXT.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(422, f"Could not read document: {exc.__class__.__name__}.")
    if not text.strip():
        raise HTTPException(422, "The document contains no extractable text.")
    return text.strip()
