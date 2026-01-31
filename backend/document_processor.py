from PyPDF2 import PdfReader
from docx import Document
import io

documents_store = {}

CHUNK_SIZE = 500  # characters (simple chunking)


def extract_text(file, filename):
    if filename.endswith(".txt"):
        return file.file.read().decode("utf-8")

    elif filename.endswith(".pdf"):
        reader = PdfReader(file.file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    elif filename.endswith(".docx"):
        doc = Document(file.file)
        return "\n".join([p.text for p in doc.paragraphs])


def chunk_text(text):
    chunks = []
    for i in range(0, len(text), CHUNK_SIZE):
        chunk = text[i:i + CHUNK_SIZE]
        chunks.append(chunk)
    return chunks


def process_document(document_id: str, file):
    try:
        text = extract_text(file, file.filename.lower())
        chunks = chunk_text(text)

        documents_store[document_id]["chunks"] = [
            {"chunk_id": i, "text": chunk}
            for i, chunk in enumerate(chunks)
        ]
        documents_store[document_id]["status"] = "completed"

    except Exception as e:
        documents_store[document_id]["status"] = "failed"