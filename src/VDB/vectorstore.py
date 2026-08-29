"""
vectorstore.py - Build and persist the ChromaDB vector store.

Creates a Chroma collection from chunked documents + embeddings
and saves it to disk at `<project_root>/vectorstore/chroma_db`.
"""

from pathlib import Path
from langchain_chroma import Chroma
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def create_vectorstore(
    chunks: list,
    embeddings: NVIDIAEmbeddings,
    persist_dir: Path | None = None,
    collection_name: str = "mediscan_rag",
) -> Chroma:
    """Build a ChromaDB vector store from document chunks.

    Parameters
    ----------
    chunks : list
        Chunked LangChain Document objects.
    embeddings : NVIDIAEmbeddings
        Embedding model instance.
    persist_dir : Path, optional
        Where to save the Chroma DB on disk.
        Defaults to `<project_root>/vectorstore/chroma_db`.
    collection_name : str
        Name of the Chroma collection.

    Returns
    -------
    Chroma
        The created (and persisted) vector store.
    """
    if persist_dir is None:
        persist_dir = get_project_root() / "vectorstore" / "chroma_db"

    persist_dir.mkdir(parents=True, exist_ok=True)
    print(f"Vector DB path: {persist_dir}")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(persist_dir),
        collection_name=collection_name,
    )

    count = vectorstore._collection.count()
    print(f"ChromaDB created successfully!")
    print(f"Stored chunks: {count}")
    return vectorstore


def load_vectorstore(
    embeddings: NVIDIAEmbeddings,
    persist_dir: Path | None = None,
    collection_name: str = "mediscan_rag",
) -> Chroma:
    """Load an existing ChromaDB vector store from disk.

    Parameters
    ----------
    embeddings : NVIDIAEmbeddings
        Embedding model instance (needed for queries).
    persist_dir : Path, optional
        Location of the persisted Chroma DB.
    collection_name : str
        Name of the Chroma collection.

    Returns
    -------
    Chroma
        The loaded vector store.
    """
    if persist_dir is None:
        persist_dir = get_project_root() / "vectorstore" / "chroma_db"

    vectorstore = Chroma(
        persist_directory=str(persist_dir),
        embedding_function=embeddings,
        collection_name=collection_name,
    )

    count = vectorstore._collection.count()
    print(f"Loaded ChromaDB from {persist_dir}")
    print(f"Number of documents: {count}")
    return vectorstore
