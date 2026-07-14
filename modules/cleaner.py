import re
from typing import List, Dict

class TextCleaner:
    """Cleans extracted PDF text before chunking"""

    def __init__(self):
        pass

    def remove_extra_whitespace(self, text: str) -> str:
        """Remove unnecessary spaces and tabs"""
        text = re.sub(r"[\t]+", " ", text)
        return text.strip()

    def remove_blank_lines(self, text: str) -> str:
        """Remove repeated empty lines"""
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text

    def remove_page_numbers(self, text: str) -> str:
        """Remove page numbers that appear on a line by themselves"""
        lines = text.split("\n")
        cleaned = []

        for line in lines:
            line = line.strip()
            if re.fullmatch(r"\d+", line):
                continue
            if re.fullmatch(r"(?i)page\s+\d+", line):
                continue
            cleaned.append(line)

        return "\n".join(cleaned)

    def normalize_newlines(self, text: str) -> str:
        """Normalize line endings"""
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def remove_headers_footers(self, text: str, headers: List[str] = None, footers: List[str] = None) -> str:
        """Optionally remove repeated headers and footers"""
        if headers is None:
            headers = []
        if footers is None:
            footers = []

        lines = text.split("\n")
        cleaned = []

        for line in lines:
            current = line.strip()
            if current in headers:
                continue
            if current in footers:
                continue
            cleaned.append(line)

        return "\n".join(cleaned)

    def clean_text(self, text: str) -> str:
        """Complete Cleaning Pipeline"""
        text = self.normalize_newlines(text)
        text = self.remove_page_numbers(text)
        text = self.remove_extra_whitespace(text)
        text = self.remove_blank_lines(text)
        return text.strip()

    def clean_pages(self, pages: List[Dict]) -> List[Dict]:
        """Clean every extracted page while preserving metadata"""
        cleaned_pages = []
        for page in pages:
            cleaned_pages.append({
                "document": page["document"],
                "page": page["page"],
                "text": self.clean_text(page["text"]),
            })
        return cleaned_pages
