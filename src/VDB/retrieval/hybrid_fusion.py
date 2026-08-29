"""
hybrid_fusion.py - Hybrid Retriever Fusion combining Dense and Sparse scores.

Implements Reciprocal Rank Fusion (RRF) and produces unified EvidenceRecords.
"""

from typing import List, Dict, Optional
from VDB.config import RRF_K_CONSTANT
from VDB.schema import EvidenceRecord, RetrievalFilters


def reciprocal_rank_fusion(
    dense_results: List[EvidenceRecord],
    sparse_results: List[EvidenceRecord],
    k_constant: int = RRF_K_CONSTANT,
    top_k: int = 15,
) -> List[EvidenceRecord]:
    """Fuse dense and sparse retrieval ranks using Reciprocal Rank Fusion (RRF).

    RRF_score(d) = sum_{m in models} 1 / (k_constant + rank_m(d))
    """
    rrf_scores: Dict[str, float] = {}
    evidence_map: Dict[str, EvidenceRecord] = {}

    # Accumulate Dense ranks
    for rank, item in enumerate(dense_results, 1):
        cid = item.chunk_id
        if cid not in evidence_map:
            evidence_map[cid] = item
        evidence_map[cid].dense_score = item.dense_score
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k_constant + rank))

    # Accumulate Sparse ranks
    for rank, item in enumerate(sparse_results, 1):
        cid = item.chunk_id
        if cid not in evidence_map:
            evidence_map[cid] = item
        evidence_map[cid].bm25_score = item.bm25_score
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k_constant + rank))

    # Sort descending by RRF score
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    fused_results: List[EvidenceRecord] = []
    for rank, (cid, score) in enumerate(sorted_items[:top_k], 1):
        rec = evidence_map[cid]
        rec.rrf_score = score
        rec.retrieval_score = score
        rec.rank = rank
        rec.evidence_id = f"EV-{rank:03d}"
        fused_results.append(rec)

    return fused_results


class HybridRetriever:
    """Orchestrates hybrid retrieval (Dense + Sparse + RRF)."""

    def __init__(self, dense_retriever, sparse_retriever):
        self.dense = dense_retriever
        self.sparse = sparse_retriever

    def retrieve(
        self,
        query: str,
        k: int = 10,
        filter_obj: Optional[RetrievalFilters] = None,
        dense_k: int = 20,
        sparse_k: int = 20,
    ) -> List[EvidenceRecord]:
        """Execute hybrid search combining Chroma vector similarity and BM25."""
        dense_res = self.dense.retrieve(query, k=dense_k, filter_obj=filter_obj)
        sparse_res = self.sparse.retrieve(query, k=sparse_k, filter_obj=filter_obj)
        return reciprocal_rank_fusion(dense_res, sparse_res, top_k=k)
