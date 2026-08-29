"""
pdf_loader.py - PDF document text extractor.
"""

from pathlib import Path
from typing import Optional
from langchain_community.document_loaders import PyPDFLoader


def load_pdf_text(pdf_path: Path) -> str:
    """Extract full text from a PDF file using PyPDFLoader."""
    if not Path(pdf_path).is_file():
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()
    return "\n\n".join(d.page_content for d in docs)
