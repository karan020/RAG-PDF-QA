import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

# Import modules
from modules.pdf_loader import PDFLoader
from modules.cleaner import TextCleaner
from modules.chunker import TextChunker
from modules.embeddings import EmbeddingModel
from modules.vector_db import VectorDatabase
from modules.retriever import Retriever
from modules.prompt import PromptBuilder
from modules.llm import GroqLLM
from modules.utils import Utils

# Create app
app = FastAPI(title="PDF RAG QA API", version="1.0")

# Add CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
Utils.create_directories()
pdf_loader = PDFLoader()
text_cleaner = TextCleaner()
text_chunker = TextChunker()
embedding_model = EmbeddingModel()
vector_db = VectorDatabase()
retriever = Retriever(embedding_model, vector_db)
prompt_builder = PromptBuilder()

# Initialize LLM
try:
    llm = GroqLLM()
    print("✅ LLM initialized successfully")
except Exception as e:
    print(f"⚠️ LLM initialization failed: {e}")
    print("Please set GROQ_API_KEY in .env file")
    llm = None

class QuestionRequest(BaseModel):
    question: str
    top_k: Optional[int] = 4

@app.get("/")
async def root():
    return {"message": "PDF RAG QA API", "status": "running"}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file."""
    try:
        print(f"📄 Received file: {file.filename}")
        
        # Validate
        if not Utils.allowed_file(file.filename):
            return JSONResponse(
                status_code=400,
                content={"error": "Only PDF files are supported."}
            )
        
        # Save
        contents = await file.read()
        file_path = pdf_loader.save_uploaded_bytes(file.filename or "uploaded.pdf", contents)
        print(f"💾 Saved to: {file_path}")
        
        # Extract text
        pages = pdf_loader.extract_text(file_path)
        print(f"📝 Extracted {len(pages)} pages")
        
        if not pages:
            return JSONResponse(
                status_code=400,
                content={"error": "No text could be extracted from the PDF."}
            )
        
        # Clean
        cleaned_pages = text_cleaner.clean_pages(pages)
        print(f"🧹 Cleaned {len(cleaned_pages)} pages")
        
        # Chunk
        chunks = text_chunker.chunk_pages(cleaned_pages)
        print(f"🧩 Created {len(chunks)} chunks")
        
        if not chunks:
            return JSONResponse(
                status_code=400,
                content={"error": "No chunks could be created."}
            )
        
        # Embed
        embeddings = embedding_model.embed_documents(chunks)
        print(f"🔢 Generated {embeddings.shape[0]} embeddings")
        
        # Store in vector DB
        vector_db.add_documents(embeddings, chunks)
        vector_db.save()
        print(f"💾 Saved to vector database")
        
        # Return success response with all fields
        return {
            "message": f"Successfully processed {file.filename}",
            "chunks_created": len(chunks),
            "vectors_stored": vector_db.total_vectors(),
            "pages_processed": len(pages)
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question about the uploaded PDFs."""
    try:
        question = request.question.strip()
        print(f"❓ Question: {question}")
        
        if not question:
            return JSONResponse(
                status_code=400,
                content={"error": "Question cannot be empty."}
            )
        
        if vector_db.total_vectors() == 0:
            return JSONResponse(
                status_code=400,
                content={"error": "No documents uploaded. Please upload a PDF first."}
            )
        
        if llm is None:
            return JSONResponse(
                status_code=500,
                content={"error": "LLM not initialized. Check GROQ_API_KEY in .env file."}
            )
        
        # Retrieve context
        retrieval_result = retriever.retrieve_context(question, request.top_k)
        print(f"📚 Retrieved {len(retrieval_result['chunks'])} chunks")
        
        # Build prompt
        prompt = prompt_builder.build_prompt(question, retrieval_result["context"])
        
        # Generate answer
        answer = llm.generate_answer(prompt)
        print(f"✅ Generated answer")
        
        return {
            "question": question,
            "answer": answer,
            "sources": retrieval_result["sources"],
            "chunks_used": len(retrieval_result["chunks"])
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.delete("/reset")
async def reset_application():
    """Reset the application (clear uploads and vector DB)."""
    try:
        Utils.reset_application()
        return {"message": "Application reset successfully"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/status")
async def get_status():
    """Get system status."""
    try:
        return {
            "status": "running",
            "vectors_stored": vector_db.total_vectors(),
            "metadata_count": len(vector_db.metadata),
            "llm_available": llm is not None,
            "uploads_folder_exists": os.path.exists("uploads"),
            "vector_store_exists": os.path.exists("vector_store")
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)