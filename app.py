import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="PDF RAG QA System",
    page_icon="📄",
    layout="wide"
)

st.title("📄 PDF RAG Question Answering System")
st.markdown("Upload PDFs and ask questions about their content.")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    top_k = st.slider("Number of chunks to retrieve", 1, 10, 4)
    
    st.divider()
    st.header("Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file:
        if st.button("Process PDF"):
            with st.spinner("Processing PDF..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    response = requests.post(f"{API_URL}/upload", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ {data['message']}")
                        st.info(f"Created {data['chunks_created']} chunks")
                        st.info(f"Stored {data['vectors_stored']} vectors")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
    
    st.divider()
    if st.button("🗑️ Reset Application", type="secondary"):
        try:
            response = requests.delete(f"{API_URL}/reset")
            if response.status_code == 200:
                st.success("Application reset successfully")
                st.rerun()
            else:
                st.error(f"Error: {response.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")
    
    st.divider()
    st.caption("Built with Streamlit + FastAPI + FAISS")

# Main Area
st.header("Ask Questions")

question = st.text_area("Enter your question about the uploaded documents:", height=100)

if st.button("Ask Question", type="primary"):
    if not question:
        st.warning("Please enter a question.")
    else:
        with st.spinner("Generating answer..."):
            try:
                response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question, "top_k": top_k}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Display answer
                    st.markdown("### Answer")
                    st.markdown(data["answer"])
                    
                    # Display sources
                    if data["sources"]:
                        st.markdown("### 📚 Sources")
                        for source in data["sources"]:
                            st.markdown(f"- **{source['document']}** (Page {source['page']})")
                    else:
                        st.info("No sources found.")
                    
                    # Display chunk usage
                    st.caption(f"Used {data['chunks_used']} chunks for this answer")
                    
                else:
                    st.error(f"Error: {response.text}")
                    
            except Exception as e:
                st.error(f"Connection error: {e}")

# Status
with st.expander("System Status"):
    try:
        response = requests.get(f"{API_URL}/status")
        if response.status_code == 200:
            data = response.json()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Vectors Stored", data["vectors_stored"])
            with col2:
                st.metric("Metadata Entries", data["metadata_count"])
        else:
            st.warning("Could not fetch status")
    except Exception as e:
        st.warning(f"API server not running: {e}")