from typing import List, Dict
from modules.embeddings import EmbeddingModel
from modules.vector_db import VectorDatabase

class Retriever:
    """Retrieves the most relevant document chunks from vector database."""

    def __init__(self, embedding_model: EmbeddingModel, vector_db: VectorDatabase):
        self.embedding_model = embedding_model
        self.vector_db = vector_db

    def retrieve(self, question: str, top_k: int = 4) -> List[Dict]:
        """Retrieve top-k most relevant chunks."""
        if not question.strip():
            raise ValueError("Question cannot be empty")
        
        query_embedding = self.embedding_model.embed_query(question)
        results = self.vector_db.search(query_embedding=query_embedding, top_k=top_k)
        return results

    def build_context(self, retrieved_chunks: List[Dict]) -> str:
        """Build context for LLM prompt."""
        if not retrieved_chunks:
            return " "
        
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, start=1):
            context_parts.append(
                f"""
Context {i}
Document: {chunk['document']}
Page: {chunk['page']}

Content:
{chunk['text']}
"""
            )
        return "\n" + ("\n" + "-" * 60 + "\n").join(context_parts)

    def get_sources(self, retrieved_chunks: List[Dict]) -> List[Dict]:
        """Return unique sources."""
        sources = []
        seen = set()
        for chunk in retrieved_chunks:
            key = (chunk["document"], chunk["page"])
            if key not in seen:
                sources.append({
                    "document": chunk["document"],
                    "page": chunk["page"],
                })
                seen.add(key)
        return sources

    def retrieve_context(self, question: str, top_k: int = 4):
        """Complete retrieval pipeline."""
        chunks = self.retrieve(question=question, top_k=top_k)
        context = self.build_context(chunks)
        sources = self.get_sources(chunks)
        return {
            "context": context,
            "chunks": chunks,
            "sources": sources,
        }
