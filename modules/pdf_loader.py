import os
import fitz  # PyMuPDF


class PDFLoader:
    # Handles PDF validation, saving, and text extraction

    def __init__(self, upload_folder: str = "uploads"):
        self.upload_folder = upload_folder
        os.makedirs(self.upload_folder, exist_ok=True)

    def is_valid_pdf(self, filename: str) -> bool:
        # Check if the uploaded file is a PDF
        return filename.lower().endswith(".pdf")

    def _resolve_filename(self, uploaded_file, fallback: str = "uploaded.pdf") -> str:
        if hasattr(uploaded_file, "filename"):
            return uploaded_file.filename
        if hasattr(uploaded_file, "name"):
            return uploaded_file.name
        return fallback

    def save_uploaded_bytes(self, filename: str, content: bytes) -> str:
        if not self.is_valid_pdf(filename):
            raise ValueError("Only PDF files are supported.")

        safe_name = os.path.basename(filename)
        file_path = os.path.join(self.upload_folder, safe_name)

        with open(file_path, "wb") as f:
            f.write(content)

        return file_path

    def save_uploaded_file(self, uploaded_file) -> str:
        # Save uploaded file to uploads folder.
        # Works with Streamlit's UploadedFile object and similar file-like objects.
        filename = self._resolve_filename(uploaded_file)
        if not self.is_valid_pdf(filename):
            raise ValueError("Only PDF files are supported.")

        if hasattr(uploaded_file, "getbuffer"):
            content = uploaded_file.getbuffer()
        elif hasattr(uploaded_file, "read"):
            content = uploaded_file.read()
            # Check if read returned a coroutine (async file object)
            if hasattr(content, '__await__'):
                import asyncio
                content = asyncio.run(content)
        else:
            raise TypeError("Unsupported upload object")

        return self.save_uploaded_bytes(filename, content)

    def extract_text(self, pdf_path: str):
        """
        Extract text page by page.
        Returns:
        [
           {
               "document": "policy.pdf",
               "page": 1,
               "text": "..."
           },
           ...
        ]
        """
        pages = []

        try:
            document = fitz.open(pdf_path)

            for page_number in range(len(document)):
                page = document.load_page(page_number)
                text = page.get_text("text").strip()

                if not text:
                    continue

                pages.append(
                    {
                        "document": os.path.basename(pdf_path),
                        "page": page_number + 1,
                        "text": text,
                    }
                )

            document.close()

        except Exception as e:
            raise RuntimeError(f"Failed to read PDF: {e}") from e

        return pages

    def load_pdf(self, uploaded_file):
        # Complete pipeline: Upload -> save PDF -> extract text
        # Returns extracted page-wise text.
        pdf_path = self.save_uploaded_file(uploaded_file)
        return self.extract_text(pdf_path)