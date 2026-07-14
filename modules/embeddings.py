import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    """Handles embedding generation for documents and user queries."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print("Embedding model loaded successfully")

    def embed_documents(self, chunks):
        """Generate embeddings for document chunks."""
        texts = [chunk["text"] for chunk in chunks]

        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embeddings.astype(np.float32)

    def embed_query(self, query: str):
        """Generate embedding for a user's question."""
        embedding = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return np.array([embedding], dtype=np.float32)

    def embedding_dimension(self):
        """Return embedding vector dimension."""
        return self.model.get_sentence_embedding_dimension()

    def print_model_info(self):
        """Display info about embedding model."""
        print(f"Model: {self.model}")
        print(f"Dimension: {self.embedding_dimension()}")
