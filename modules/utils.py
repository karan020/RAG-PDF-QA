import os
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class Utils:
    """Common utility functions used across the RAG project."""

    @staticmethod
    def create_directories():
        """Create required project directories."""
        folders = ["uploads", "vector_store"]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)

    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Check whether uploaded file is a PDF."""
        return filename.lower().endswith(".pdf")

    @staticmethod
    def get_env(key: str, default=None):
        """Read environment variable."""
        return os.getenv(key, default)

    @staticmethod
    def save_json(data, filename):
        """Save dictionary/list as JSON."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def load_json(filename):
        """Load JSON file."""
        if not os.path.exists(filename):
            return None
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def current_time():
        """Current timestamp."""
        return datetime.now().strftime("%Y-%m-%d-%H:%M:%S")

    @staticmethod
    def format_sources(sources):
        """Format retrieved sources."""
        if not sources:
            return "No sources found."
        output = []
        for source in sources:
            output.append(f"{source['document']} (Page {source['page']})")
        return "\n".join(output)

    @staticmethod
    def print_banner():
        """Display startup banner."""
        print("    PDF RAG Question Answering System")

    @staticmethod
    def clear_uploads():
        """Delete uploaded PDFs."""
        folder = "uploads"
        if os.path.exists(folder):
            for file in os.listdir(folder):
                path = os.path.join(folder, file)
                if os.path.isfile(path):
                    os.remove(path)

    @staticmethod
    def clear_vector_store():
        """Delete FAISS database."""
        folder = "vector_store"
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

    @staticmethod
    def reset_application():
        """Reset upload and vector database."""
        Utils.clear_uploads()
        Utils.clear_vector_store()

    @staticmethod
    def validate_question(question: str):
        """Validate user question."""
        if question is None:
            raise ValueError("Question cannot be empty")
        if len(question.strip()) == 0:
            raise ValueError("Question cannot be empty")
        return question.strip()

    @staticmethod
    def statistics(chunks):
        """Print chunk statistics."""
        print("Chunk Statistics")
        print(f"Total Chunks: {len(chunks)}")
        if chunks:
            avg = sum(len(c["text"]) for c in chunks) / len(chunks)
            print(f"Average Length: {avg:.2f} characters")
