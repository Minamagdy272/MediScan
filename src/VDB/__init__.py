"""
MediScan VDB & Retrieval Package.

Modular, evidence-grounded medical RAG retrieval engine.
"""

from VDB.schema import MedicalDocument, MedicalChunk, RetrievalFilter, SearchResult
from VDB.pipeline import MediScanRetriever
from VDB.indexing.vector_index import ChromaVectorIndex
from VDB.indexing.bm25_index import BM25Index
from VDB.retrieval.dense_retriever import DenseRetriever
from VDB.retrieval.sparse_retriever import SparseRetriever
from VDB.retrieval.hybrid_fusion import HybridRetriever, reciprocal_rank_fusion
from VDB.retrieval.reranker import NvidiaReranker
from VDB.retrieval.evidence_selector import EvidenceSelector

__all__ = [
    "MedicalDocument",
    "MedicalChunk",
    "RetrievalFilter",
    "SearchResult",
    "MediScanRetriever",
    "ChromaVectorIndex",
    "BM25Index",
    "DenseRetriever",
    "SparseRetriever",
    "HybridRetriever",
    "reciprocal_rank_fusion",
    "NvidiaReranker",
    "EvidenceSelector",
]
