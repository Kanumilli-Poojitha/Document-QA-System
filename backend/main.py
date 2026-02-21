from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import os

from fastapi.responses import FileResponse
from fpdf import FPDF

from document_processor import process_document, documents_store
from gemini_client import ask_gemini_batched
from session_manager import get_session, add_message

app = FastAPI()


class AskRequest(BaseModel):
    session_id: str | None = None
    document_ids: list[str]
    question: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/upload", status_code=202)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    filename = file.filename.lower()

    if not (filename.endswith(".pdf") or filename.endswith(".txt") or filename.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    document_id = str(uuid.uuid4())
    documents_store[document_id] = {
        "filename": file.filename,
        "status": "processing",
        "chunks": []
    }

    background_tasks.add_task(process_document, document_id, file)

    return {
        "document_id": document_id,
        "filename": file.filename,
        "message": "Document accepted for processing."
    }


@app.get("/documents/{document_id}/status")
def get_document_status(document_id: str):
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": document_id,
        "status": documents_store[document_id]["status"]
    }


@app.get("/documents/{document_id}/chunks")
def get_document_chunks(document_id: str):
    doc = documents_store.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc["status"] != "completed":
        raise HTTPException(status_code=400, detail="Document not processed yet")

    return {
        "document_id": document_id,
        "chunks": doc["chunks"]
    }


@app.post("/ask")
def ask_question(request: AskRequest):
    session_id = request.session_id or str(uuid.uuid4())
    question = request.question.lower()

    relevant_chunks = []
    question_words = question.split()

    for doc_id in request.document_ids:
        doc = documents_store.get(doc_id)
        if not doc or doc["status"] != "completed":
            continue

        for chunk in doc["chunks"]:
            if any(word in chunk["text"].lower() for word in question_words):
                relevant_chunks.append({
                    "document_id": doc_id,
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"]
                })

    # fallback: include all chunks if no relevant match
    if not relevant_chunks:
        for doc_id in request.document_ids:
            doc = documents_store.get(doc_id)
            if not doc or doc["status"] != "completed":
                continue
            for chunk in doc["chunks"]:
                relevant_chunks.append({
                    "document_id": doc_id,
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"]
                })

    if not relevant_chunks:
        raise HTTPException(status_code=400, detail="No documents available to answer")

    answer, tokens_used, batch_size = ask_gemini_batched(request.question, relevant_chunks)

    add_message(session_id, "user", request.question)
    add_message(session_id, "assistant", answer)

    return {
        "answer": answer,
        "session_id": session_id,
        "source_chunks": relevant_chunks,
        "batch_size": batch_size,
        "tokens_used": tokens_used
    }


@app.get("/session/{session_id}")
def get_conversation(session_id: str):
    messages = get_session(session_id)
    # Return both `history` (as required by the spec) and `messages`
    # (kept for backward compatibility with the frontend).
    if messages is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "history": messages,
        "messages": messages
    }


EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

@app.get("/session/{session_id}/export")
def export_session_pdf(session_id: str):
    messages = get_session(session_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Session not found")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Load Unicode font
    font_path = "DejaVuSans.ttf"
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", size=12)

    pdf.cell(0, 10, f"Conversation Export - Session {session_id}", ln=True, align="C")
    pdf.ln(10)

    for msg in messages:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")

        text = f"{role}: {content}"
        pdf.multi_cell(0, 8, text)
        pdf.ln(2)

    export_path = os.path.join(EXPORT_DIR, f"session_{session_id}.pdf")
    pdf.output(export_path)

    return FileResponse(
        export_path,
        filename=f"session_{session_id}.pdf",
        media_type="application/pdf"
    )