"""
chunking.py - Load cleaned documents and split them into chunks.

Wraps LangChain's DirectoryLoader and RecursiveCharacterTextSplitter
with the same parameters used in the original notebook.
"""

from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_cleaned_documents(
    data_path: Path | None = None,
) -> list:
    """Load all cleaned .txt documents from the data/cleaned directory.

    Parameters
    ----------
    data_path : Path, optional
        Root directory of cleaned text files.
        Defaults to `<project_root>/data/cleaned`.

    Returns
    -------
    list
        LangChain Document objects.
    """
    if data_path is None:
        data_path = get_project_root() / "data" / "cleaned"

    loader = DirectoryLoader(
        str(data_path),
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )

    docs = loader.load()
    print(f"Loaded documents: {len(docs)}")
    return docs


def chunk_documents(
    docs: list,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list:
    """Split documents into chunks using RecursiveCharacterTextSplitter.

    Parameters
    ----------
    docs : list
        LangChain Document objects.
    chunk_size : int
        Maximum characters per chunk.
    chunk_overlap : int
        Overlap between consecutive chunks.

    Returns
    -------
    list
        Chunked LangChain Document objects.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = text_splitter.split_documents(docs)

    print(f"Original documents: {len(docs)}")
    print(f"Created chunks: {len(chunks)}")
    return chunks


def print_chunk_stats(chunks: list) -> None:
    """Print min/max/avg chunk size statistics."""
    sizes = [len(c.page_content.strip()) for c in chunks]
    print(f"Total chunks: {len(chunks)}")
    print(f"Min size: {min(sizes)}")
    print(f"Max size: {max(sizes)}")
    print(f"Average size: {sum(sizes) / len(sizes):.2f}")


if __name__ == "__main__":
    docs = load_cleaned_documents()
    chunks = chunk_documents(docs)
    print_chunk_stats(chunks)
