"""
embedding.py - Initialize the NVIDIA embedding model.

Loads credentials from a .env file and creates a LangChain
NVIDIAEmbeddings instance using the same configuration as the
original notebook.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def get_embeddings(env_path: Path | None = None) -> NVIDIAEmbeddings:
    """Create and return the NVIDIA embedding model.

    Parameters
    ----------
    env_path : Path, optional
        Path to the `.env` file.
        Defaults to `<project_root>/src/.env`.

    Returns
    -------
    NVIDIAEmbeddings
        Configured embedding model instance.

    Raises
    ------
    ValueError
        If required environment variables are missing.
    """
    if env_path is None:
        env_path = get_project_root() / "src" / ".env"

    load_dotenv(env_path)

    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL")
    model = os.getenv("EMBEDDING_MODEL")

    if not api_key:
        raise ValueError("NVIDIA_API_KEY is not set in .env")
    if not base_url:
        raise ValueError("NVIDIA_BASE_URL is not set in .env")
    if not model:
        raise ValueError("EMBEDDING_MODEL is not set in .env")

    embeddings = NVIDIAEmbeddings(
        model=model,
        api_key=api_key,
        base_url=base_url,
    )

    print(f"Embedding model loaded: {model}")
    return embeddings


def test_embedding(embeddings: NVIDIAEmbeddings) -> None:
    """Quick sanity check: embed a single test sentence."""
    test_text = [
        "Pleural effusion is an abnormal accumulation of fluid in the pleural space."
    ]
    result = embeddings.embed_documents(test_text)
    print(f"Number of embeddings: {len(result)}")
    print(f"Embedding dimension: {len(result[0])}")
    print(f"First 10 values: {result[0][:10]}")


if __name__ == "__main__":
    emb = get_embeddings()
    test_embedding(emb)
