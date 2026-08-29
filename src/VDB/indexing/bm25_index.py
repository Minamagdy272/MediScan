"""
bm25_index.py - Sparse BM25 lexical keyword index with persistence and filtering.
"""

import pickle
import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from rank_bm25 import BM25Okapi

from VDB.config import BM25_INDEX_PATH
from VDB.schema import MedicalChunk, RetrievalFilter


def tokenize_medical_text(text: str) -> List[str]:
    """Tokenize medical text into lowercased terms and clinical acronyms."""
    tokens = re.findall(r"\b[A-Za-z0-9\-_]{2,}\b", text.lower())
    return tokens


class BM25Index:
    """Manages BM25 lexical keyword index for exact medical terms and acronym matching."""

    def __init__(self, index_path: Optional[Path] = None):
        self.index_path = index_path if index_path else BM25_INDEX_PATH
        self.chunks: List[MedicalChunk] = []
        self.bm25: Optional[BM25Okapi] = None

    def build_index(self, chunks: List[MedicalChunk]) -> None:
        """Build the BM25 index from a collection of MedicalChunk objects."""
        self.chunks = chunks
        corpus = [tokenize_medical_text(c.content) for c in chunks]
        self.bm25 = BM25Okapi(corpus)
        self.save()
        print(f"Built and saved BM25 index with {len(chunks)} chunks.")

    def save(self, path: Optional[Path] = None) -> None:
        """Serialize index and chunks to disk."""
        target = path if path else self.index_path
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as f:
            pickle.dump({"chunks": self.chunks, "bm25": self.bm25}, f)

    def load(self, path: Optional[Path] = None) -> bool:
        """Load persisted index and chunks from disk."""
        target = path if path else self.index_path
        if not target.is_file():
            return False
        with open(target, "rb") as f:
            data = pickle.load(f)
            self.chunks = data.get("chunks", [])
            self.bm25 = data.get("bm25", None)
        return self.bm25 is not None

    def search(
        self,
        query: str,
        k: int = 10,
        filter_obj: Optional[RetrievalFilter] = None,
    ) -> List[Tuple[MedicalChunk, float]]:
        """Run BM25 search with metadata filtering."""
        if not self.bm25 or not self.chunks:
            if not self.load():
                return []

        tokens = tokenize_medical_text(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        
        # Pair with chunks and apply metadata filters
        scored_pairs = []
        for idx, score in enumerate(scores):
            if score <= 0:
                continue
            chunk = self.chunks[idx]
            if filter_obj and not filter_obj.matches(chunk):
                continue
            scored_pairs.append((chunk, float(score)))

        # Sort descending by BM25 score
        scored_pairs.sort(key=lambda x: x[1], reverse=True)
        return scored_pairs[:k]
