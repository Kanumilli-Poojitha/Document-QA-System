import streamlit as st
import requests

API_URL = "http://api:8000"

st.set_page_config(page_title="📄 Document QA System", layout="wide")
st.title("📄 Document Question Answering System (Gemini RAG)")

# -----------------------------
# Backend Health Check
# -----------------------------
st.sidebar.title("System Status")

try:
    r = requests.get(f"{API_URL}/health", timeout=5)
    if r.status_code == 200:
        st.sidebar.success("Backend is healthy ✅")
    else:
        st.sidebar.error("Backend unhealthy ❌")
except Exception:
    st.sidebar.error("Backend not reachable ❌")

st.sidebar.markdown("---")

# -----------------------------
# Session State
# -----------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "document_ids" not in st.session_state:
    st.session_state.document_ids = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------
# Upload Section
# -----------------------------
st.header("📤 Upload Document")

uploaded_file = st.file_uploader(
    "Upload a document (PDF, TXT, DOCX)",
    type=["pdf", "txt", "docx"]
)

if uploaded_file:
    with st.spinner("Uploading document..."):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        try:
            r = requests.post(f"{API_URL}/upload", files=files)
            if r.status_code == 202:
                data = r.json()
                doc_id = data["document_id"]
                st.success(f"Uploaded: {uploaded_file.name}")
                st.write(f"Document ID: `{doc_id}`")
                st.session_state.document_ids = [doc_id]
            else:
                st.error(r.json().get("detail", "Upload failed"))
        except Exception as e:
            st.error(f"Upload error: {e}")

st.markdown("---")

# -----------------------------
# Chat Section
# -----------------------------
st.header("💬 Ask Questions")

question = st.text_input("Enter your question")

if st.button("Ask Gemini"):
    if not st.session_state.document_ids:
        st.warning("Please upload a document first.")
    elif not question.strip():
        st.warning("Please enter a question.")
    else:
        payload = {
            "session_id": st.session_state.session_id,
            "document_ids": st.session_state.document_ids,
            "question": question
        }

        with st.spinner("Gemini is thinking..."):
            try:
                r = requests.post(f"{API_URL}/ask", json=payload)
                if r.status_code == 200:
                    data = r.json()

                    answer = data["answer"]
                    session_id = data["session_id"]
                    source_chunks = data.get("source_chunks", [])
                    tokens_used = data.get("tokens_used", {})
                    batch_size = data.get("batch_size", 0)

                    st.session_state.session_id = session_id

                    st.session_state.chat_history.append(
                        {"role": "user", "content": question}
                    )
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": answer}
                    )

                    st.subheader("🤖 Answer")
                    st.write(answer)

                    st.subheader("📚 Source Chunks")
                    for src in source_chunks:
                        st.info(
                            f"Document: {src['document_id']} | Chunk {src['chunk_id']}\n\n{src['text']}"
                        )

                    st.subheader("📊 Token Usage")
                    st.json(tokens_used)

                    st.write(f"Batch size: {batch_size}")

                else:
                    st.error(r.json().get("detail", "Question failed"))

            except Exception as e:
                st.error(f"Error calling API: {e}")

st.markdown("---")

# -----------------------------
# Conversation History
# -----------------------------
st.header("🧾 Conversation History")

if st.session_state.session_id:
    try:
        r = requests.get(f"{API_URL}/session/{st.session_state.session_id}")
        if r.status_code == 200:
            history = r.json().get("messages", [])
            for msg in history:
                role = msg["role"].capitalize()
                st.markdown(f"**{role}:** {msg['content']}")
        else:
            st.error("Could not fetch session history")
    except Exception as e:
        st.error(f"Error fetching history: {e}")
else:
    st.info("No active session yet.")

st.markdown("---")

# -----------------------------
# Export PDF
# -----------------------------
st.header("📄 Export Conversation")

if st.session_state.session_id:
    if st.button("Export Conversation as PDF"):
        try:
            r = requests.get(f"{API_URL}/session/{st.session_state.session_id}/export")
            if r.status_code == 200:
                st.download_button(
                    label="Download PDF",
                    data=r.content,
                    file_name=f"session_{st.session_state.session_id}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Failed to export PDF")
        except Exception as e:
            st.error(f"Export error: {e}")
else:
    st.warning("No session available to export.")