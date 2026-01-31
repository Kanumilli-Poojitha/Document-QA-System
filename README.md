# Document Question Answering System using Batched Gemini API (RAG)

## 📌 Overview
This project is a containerized Document Question Answering (Q&A) system built using **FastAPI**, **Streamlit**, and **Google Gemini API (Vertex AI)**.  
It allows users to upload documents (PDF, TXT, DOCX), ask questions about their content, and receive accurate answers grounded in the document text using **Retrieval-Augmented Generation (RAG)**.

To improve efficiency and reduce API cost, the system uses **batched Gemini API calls**, processes documents asynchronously, maintains conversational history, tracks token usage, and allows exporting conversations as a PDF.

---

## 🚀 Features
- 📤 Upload documents (PDF, TXT, DOCX)
- 🔎 Automatic text extraction and chunking
- 💬 Chat-based Q&A using Gemini API
- 📚 Source attribution (shows document chunks used for answers)
- 🧠 Conversational session memory
- 📊 Token usage tracking (prompt, response, total tokens)
- ⚡ Batched Gemini API requests for cost efficiency
- 📄 Export conversation history as PDF
- 🐳 Fully containerized with Docker & Docker Compose
- 🖥️ Streamlit-based user interface

---

## 🏗️ Architecture
The system is composed of two services:

### Backend (FastAPI)
- Handles document upload and processing
- Extracts and chunks document text
- Retrieves relevant chunks using keyword matching
- Sends batched prompts to Gemini API
- Maintains session history
- Tracks token usage
- Exposes REST API endpoints

### Frontend (Streamlit)
- Upload documents
- Ask questions
- Display answers with source chunks
- Show token usage
- Export conversation as PDF

Frontend communicates with backend via HTTP APIs.

---

## 📂 Project Structure
├── backend/
│ ├── main.py
│ ├── Dockerfile
│ └── requirements.txt
├── frontend/
│ ├── app.py
│ ├── Dockerfile
│ └── requirements.txt
├── docker-compose.yml
├── .env.example
├── README.md
└── tests/ (optional)

## ⚙️ Environment Variables
Create a `.env` file using the template below:

### `.env.example`
```env
GEMINI_API_KEY="your_gemini_api_key_here"
API_PORT=8000
UI_PORT=8501

🐳 Docker Setup
Build and Run the Application
docker-compose up --build

Access the Services

Backend API: http://localhost:8000

Frontend UI: http://localhost:8501

API Health Check: http://localhost:8000/health

🔗 API Endpoints
Health Check
GET /health


Response:

{ "status": "ok" }

Upload Document
POST /upload


Request: multipart/form-data with file

Response:

{
  "document_id": "string",
  "filename": "string",
  "message": "Document accepted for processing."
}

Document Status
GET /documents/{document_id}/status


Response:

{
  "document_id": "string",
  "status": "processing | completed | failed"
}

Retrieve Chunks
GET /documents/{document_id}/chunks


Response:

{
  "document_id": "string",
  "chunks": [
    { "chunk_id": 0, "text": "..." }
  ]
}

Ask Question (Batched Gemini API)
POST /ask


Request:

{
  "session_id": "string",
  "document_ids": ["string"],
  "question": "string"
}


Response:

{
  "answer": "string",
  "session_id": "string",
  "source_chunks": [
    {
      "document_id": "string",
      "chunk_id": 0,
      "text": "string"
    }
  ],
  "batch_size": 3,
  "tokens_used": {
    "prompt_tokens": 120,
    "candidates_tokens": 80,
    "total_tokens": 200
  }
}

Conversation History
GET /session/{session_id}

Export Conversation as PDF
GET /session/{session_id}/export


Returns:

Content-Type: application/pdf
Downloadable PDF file

🧠 Batching Strategy

Relevant document chunks are grouped into batches and sent together in a single Gemini API call along with the user question.
This reduces:

API round trips
Latency
Cost per query

Each response includes a batch_size field for verification.

📊 Token Usage Tracking

Each /ask request returns:

prompt_tokens
candidates_tokens
total_tokens

This helps monitor API usage and cost per session.

🖥️ Frontend UI

The Streamlit UI allows users to:
Upload documents
Ask questions in a chat interface
View answers with source chunks
See token usage
Export conversation to PDF

🧪 Testing (Optional)

A tests/ directory can be used for API endpoint testing and validation using Pytest or Postman.

🔐 Security Notes

API key is loaded from environment variables
.env file is excluded from version control
.env.example documents required variables only

📈 Future Improvements

Add vector database (FAISS / Pinecone) for semantic search
Improve chunk ranking with embeddings
Add user authentication
Support more document formats
UI enhancements (session selector, dark mode)

Demo video

https://youtu.be/oYoeA4Cdq4E


commands used in demo:

docker-compose up --build

http://localhost:8000/health

curl.exe -X POST "http://localhost:8000/upload" -F "file=@sample.txt"

GET http://localhost:8000/documents/{document_id}/status

GET http://localhost:8000/documents/{document_id}/chunks

POST http://localhost:8000/ask

{
  "session_id": null,
  "document_ids": ["49e5972b-b378-4290-9935-912e2111b50e"],
  "question": "What is the capital of India?"
}


GET http://localhost:8000/session/session-uuid

GET /session/{session_id}/export



http://localhost:8501

👩‍💻 Author

Kanumilli Poojitha

Document Question Answering System using Batched Gemini API (RAG)