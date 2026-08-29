"""
embeddings.py - NVIDIA NIM embedding provider with batching, retry, and validation.
"""

import os
import time
from typing import List
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

from VDB.config import NVIDIA_API_KEY, NVIDIA_BASE_URL, EMBEDDING_MODEL


def get_embedding_function(
    model: str = EMBEDDING_MODEL,
    api_key: str = NVIDIA_API_KEY,
    base_url: str = NVIDIA_BASE_URL,
) -> NVIDIAEmbeddings:
    """Create and validate NVIDIA NIM embedding instance."""
    if not api_key:
        raise ValueError("NVIDIA_API_KEY is not set in environment or config.")

    return NVIDIAEmbeddings(
        model=model,
        api_key=api_key,
        base_url=base_url,
    )


def embed_texts_with_retry(
    embeddings: NVIDIAEmbeddings,
    texts: List[str],
    batch_size: int = 100,
    max_retries: int = 3,
) -> List[List[float]]:
    """Embed texts in batches with exponential backoff retry."""
    all_vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        for attempt in range(max_retries):
            try:
                vectors = embeddings.embed_documents(batch)
                all_vectors.extend(vectors)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)

    return all_vectors
