import os
import pickle
import faiss
import numpy as np

class VectorDatabase:
    """Handles FAISS vector database operations."""

    def __init__(self, index_path="vector_store/faiss_index.bin", metadata_path="vector_store/metadata.pkl"):
        self.index_path = index_path
        self.metadata_path = metadata_path
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        self.index = None
        self.metadata = []

    def create_index(self, embedding_dimension: int):
        """Create a cosine similarity Faiss index."""
        self.index = faiss.IndexFlatIP(embedding_dimension)

    def add_documents(self, embeddings: np.ndarray, chunks: list):
        """Add embeddings and metadata."""
        if self.index is None:
            self.create_index(embeddings.shape[1])
        self.index.add(embeddings)
        self.metadata.extend(chunks)

    def save(self):
        """Save FAISS index and metadata."""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self):
        """Load FAISS index and metadata."""
        if not os.path.exists(self.index_path):
            raise FileNotFoundError("FAISS index not found. Upload PDFs first.")
        self.index = faiss.read_index(self.index_path)
        with open(self.metadata_path, "rb") as f:
            self.metadata = pickle.load(f)

    def search(self, query_embedding: np.ndarray, top_k: int = 4):
        """Retrieve the most relevant chunks."""
        if self.index is None:
            raise RuntimeError("Vector database is not loaded.")

        scores, indices = self.index.search(query_embedding, top_k)
        results = []

        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            chunk = self.metadata[idx].copy()
            chunk["score"] = float(score)
            results.append(chunk)

        return results

    def total_vectors(self):
        """Number of vectors stored."""
        return self.index.ntotal if self.index is not None else 0

    def clear(self):
        """Remove all vectors."""
        self.index = None
        self.metadata = []
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        if os.path.exists(self.metadata_path):
            os.remove(self.metadata_path)

    def print_statistics(self):
        """Display database info."""
        if self.index is None:
            print("Status: Empty")
        else:
            print(f"Vectors: {self.index.ntotal}")
            print(f"Metadata Entries: {len(self.metadata)}")
