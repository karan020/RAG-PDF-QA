from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter

class TextChunker:
    """Splits cleaned text into smaller chunks while preserving metadata."""

    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 150):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ".",
                "!",
                "?",
                " ",
                "",
            ]
        )

    def chunk_pages(self, pages: list) -> List[Dict]:
        """Chunk all pages into smaller text chunks"""
        chunks = []
        global_chunk_id = 0

        for page in pages:
            split_text = self.splitter.split_text(page["text"])
            for local_chunk_id, chunk in enumerate(split_text):
                chunk = chunk.strip()
                if not chunk:
                    continue

                chunks.append({
                    "document": page["document"],
                    "page": page["page"],
                    "chunk_id": global_chunk_id,
                    "page_chunk": local_chunk_id,
                    "text": chunk,
                })
                global_chunk_id += 1

        return chunks

    def print_statistics(self, chunks: List[Dict]) -> None:
        """Print Chunk Statistics."""
        print(f"Total Chunks: {len(chunks)}")
        if chunks:
            avg_length = sum(len(c["text"]) for c in chunks) / len(chunks)
            print(f"Average length: {avg_length:.2f} characters")
