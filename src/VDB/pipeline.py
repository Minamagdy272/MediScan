"""
pipeline.py - Unified MediScan Retrieval Engine & Public API (Phase 2 Frozen Contract).

Provides the single canonical retrieval entrypoint `retrieve()` and specialized tool bridges:
  - MedicalRAGTool
  - ClinicalGuidelineTool
  - PatientHistoryTool
  - SimilarCaseTool
  - RiskAssessmentTool
  - ReportGeneratorTool
"""

import argparse
import sys
import time
import logging
from typing import List, Optional, Dict, Any, Union

from VDB.schema import (
    EvidenceRecord,
    RetrievalFilters,
    RetrievalResult,
    RetrievalMode,
    EvidenceSufficiencyResult,
    RecommendedAction,
)
from VDB.indexing.vector_index import ChromaVectorIndex
from VDB.indexing.bm25_index import BM25Index
from VDB.indexing.index_builder import build_complete_knowledge_index
from VDB.retrieval.dense_retriever import DenseRetriever
from VDB.retrieval.sparse_retriever import SparseRetriever
from VDB.retrieval.hybrid_fusion import HybridRetriever
from VDB.retrieval.reranker import NvidiaReranker
from VDB.retrieval.evidence_selector import EvidenceSelector
from VDB.retrieval.sufficiency_gate import EvidenceSufficiencyGate

# Safe diagnostic logging without secrets
logger = logging.getLogger("MediScan.Retrieval")
logger.setLevel(logging.INFO)


class MediScanRetriever:
    """Production canonical retrieval engine for MediScan Evidence-Grounded Medical RAG."""

    def __init__(
        self,
        vector_index: Optional[ChromaVectorIndex] = None,
        bm25_index: Optional[BM25Index] = None,
        enable_reranker: bool = True,
    ):
        self.vector_index = vector_index if vector_index else ChromaVectorIndex()
        self.bm25_index = bm25_index if bm25_index else BM25Index()
        
        self.dense_retriever = DenseRetriever(self.vector_index)
        self.sparse_retriever = SparseRetriever(self.bm25_index)
        self.hybrid_retriever = HybridRetriever(self.dense_retriever, self.sparse_retriever)
        self.reranker = NvidiaReranker() if enable_reranker else None
        self.evidence_selector = EvidenceSelector()
        self.sufficiency_gate = EvidenceSufficiencyGate()

    def retrieve(
        self,
        query: str,
        *,
        mode: Union[RetrievalMode, str] = RetrievalMode.HYBRID_RERANKED,
        k: int = 5,
        filters: Optional[RetrievalFilters] = None,
        require_sufficient_evidence: bool = True,
        query_type: str = "direct",
    ) -> RetrievalResult:
        """Single public retrieval entrypoint for the MediScan platform.

        Parameters
        ----------
        query : str
            Clinical or patient query text.
        mode : RetrievalMode or str
            Retrieval mode: 'dense', 'bm25', 'hybrid', 'hybrid_reranked'.
        k : int
            Number of final evidence records to return.
        filters : RetrievalFilters, optional
            Typed metadata filter for condition, body system, domain, etc.
        require_sufficient_evidence : bool
            Whether to run the deterministic Evidence Sufficiency Gate.
        query_type : str
            Query clinical category: 'direct', 'guideline', 'patient', 'comparison', 'cases'.

        Returns
        -------
        RetrievalResult
            Canonical retrieval result containing evidence records, trace, latency, and sufficiency.
        """
        start_time = time.perf_counter()
        trace: Dict[str, Any] = {"query": query, "mode": str(mode)}
        
        mode_str = mode.value if isinstance(mode, RetrievalMode) else str(mode).lower()

        # Step 1: Candidate Generation
        candidate_k = max(k * 4, 20)
        t0 = time.perf_counter()

        if mode_str == RetrievalMode.DENSE.value:
            candidates = self.dense_retriever.retrieve(query, k=candidate_k, filter_obj=filters)
            trace["dense_candidates"] = len(candidates)
            trace["dense_time_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            rerank_applied = False

        elif mode_str == RetrievalMode.BM25.value:
            candidates = self.sparse_retriever.retrieve(query, k=candidate_k, filter_obj=filters)
            trace["bm25_candidates"] = len(candidates)
            trace["bm25_time_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            rerank_applied = False

        elif mode_str == RetrievalMode.HYBRID.value:
            dense_cand = self.dense_retriever.retrieve(query, k=candidate_k, filter_obj=filters)
            sparse_cand = self.sparse_retriever.retrieve(query, k=candidate_k, filter_obj=filters)
            from VDB.retrieval.hybrid_fusion import reciprocal_rank_fusion
            candidates = reciprocal_rank_fusion(dense_cand, sparse_cand, top_k=candidate_k)
            trace["dense_candidates"] = len(dense_cand)
            trace["bm25_candidates"] = len(sparse_cand)
            trace["hybrid_candidates"] = len(candidates)
            trace["hybrid_time_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            rerank_applied = False

        elif mode_str == RetrievalMode.HYBRID_RERANKED.value:
            dense_cand = self.dense_retriever.retrieve(query, k=candidate_k, filter_obj=filters)
            sparse_cand = self.sparse_retriever.retrieve(query, k=candidate_k, filter_obj=filters)
            from VDB.retrieval.hybrid_fusion import reciprocal_rank_fusion
            fused = reciprocal_rank_fusion(dense_cand, sparse_cand, top_k=candidate_k)
            trace["dense_candidates"] = len(dense_cand)
            trace["bm25_candidates"] = len(sparse_cand)
            trace["fused_candidates"] = len(fused)

            t_rerank = time.perf_counter()
            if self.reranker and fused:
                candidates = self.reranker.rerank(query, fused, top_k=k * 2)
                rerank_applied = True
            else:
                candidates = fused
                rerank_applied = False
            trace["rerank_candidates"] = len(candidates)
            trace["rerank_time_ms"] = round((time.perf_counter() - t_rerank) * 1000, 2)

        else:
            raise ValueError(f"Unsupported retrieval mode: '{mode_str}'. Choose from {list(RetrievalMode)}.")

        total_candidates_count = len(candidates)

        # Step 2: Evidence Selection & Diversity Formatting
        selected_evidence = self.evidence_selector.select_evidence(
            candidates=candidates,
            max_results=k,
            prefer_diversity=True,
        )
        trace["selected_evidence_count"] = len(selected_evidence)

        # Step 3: Evidence Sufficiency Gate
        sufficiency_result = None
        if require_sufficient_evidence:
            sufficiency_result = self.sufficiency_gate.evaluate(
                query=query,
                evidence_list=selected_evidence,
                filters=filters,
                query_type=query_type,
            )
            trace["sufficiency_passed"] = sufficiency_result.is_sufficient
            trace["recommended_action"] = sufficiency_result.recommended_action

        total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Construct Canonical RetrievalResult
        result = RetrievalResult(
            query=query,
            retrieval_mode=mode_str,
            results=selected_evidence,
            total_candidates=total_candidates_count,
            returned_count=len(selected_evidence),
            filters_applied=filters.to_dict() if filters else {},
            reranking_applied=rerank_applied,
            sufficiency=sufficiency_result,
            latency_ms=total_latency_ms,
            metadata={"query_type": query_type},
            retrieval_trace=trace,
        )

        return result

    # --- Pre-Wired Downstream Agent Tool Bridges ---

    def search_guidelines(
        self,
        query: str,
        condition: Optional[str] = None,
        k: int = 5,
        mode: Union[RetrievalMode, str] = RetrievalMode.HYBRID_RERANKED,
    ) -> List[EvidenceRecord]:
        """Tool Bridge: Search authoritative clinical guidelines (for ClinicalGuidelineTool)."""
        filt = RetrievalFilters(condition=condition, knowledge_domain="guidelines")
        res = self.retrieve(query, k=k, filters=filt, mode=mode, query_type="guideline")
        return res.results

    def search_cases(
        self,
        query: str,
        condition: Optional[str] = None,
        modality: Optional[str] = None,
        k: int = 5,
        mode: Union[RetrievalMode, str] = RetrievalMode.HYBRID_RERANKED,
    ) -> List[EvidenceRecord]:
        """Tool Bridge: Search clinical cases and radiology reports (for SimilarCaseTool)."""
        filt = RetrievalFilters(condition=condition, knowledge_domain="cases", modality=modality)
        res = self.retrieve(query, k=k, filters=filt, mode=mode, query_type="cases")
        return res.results

    def search_patient_education(
        self,
        query: str,
        condition: Optional[str] = None,
        k: int = 5,
        mode: Union[RetrievalMode, str] = RetrievalMode.HYBRID_RERANKED,
    ) -> List[EvidenceRecord]:
        """Tool Bridge: Search patient education guides (for PatientHistoryTool / ReportGeneratorTool)."""
        filt = RetrievalFilters(condition=condition, knowledge_domain="patient_education")
        res = self.retrieve(query, k=k, filters=filt, mode=mode, query_type="patient")
        return res.results

    def search_radiology(
        self,
        findings_query: str,
        k: int = 5,
        mode: Union[RetrievalMode, str] = RetrievalMode.HYBRID_RERANKED,
    ) -> List[EvidenceRecord]:
        """Tool Bridge: Match upstream CV findings against validated chest X-ray reports."""
        filt = RetrievalFilters(modality="CXR")
        res = self.retrieve(findings_query, k=k, filters=filt, mode=mode, query_type="cases")
        return res.results

    def get_grounded_context(
        self,
        query: str,
        k: int = 5,
        filters: Optional[RetrievalFilters] = None,
        mode: Union[RetrievalMode, str] = RetrievalMode.HYBRID_RERANKED,
        query_type: str = "direct",
    ) -> str:
        """Return formatted evidence string ready to inject into LLM prompts."""
        res = self.retrieve(query, k=k, filters=filters, mode=mode, query_type=query_type)
        return res.get_evidence_context()


def main():
    parser = argparse.ArgumentParser(description="MediScan Retrieval Engine CLI (Phase 2 Frozen API)")
    parser.add_argument("--build-index", action="store_true", help="Build full ChromaDB and BM25 indices")
    parser.add_argument("--max-openi", type=int, default=500, help="Max OpenI reports to index")
    parser.add_argument("--mode", type=str, default="hybrid_reranked", choices=["dense", "bm25", "hybrid", "hybrid_reranked"], help="Retrieval mode")
    parser.add_argument("--query", type=str, help="Execute a test search query")
    parser.add_argument("--k", type=int, default=3, help="Number of results to return")
    args = parser.parse_args()

    if args.build_index:
        build_complete_knowledge_index(max_openi_reports=args.max_openi)

    retriever = MediScanRetriever()

    if args.query:
        print(f"\nExecuting Retrieval [Mode: {args.mode.upper()}] for: '{args.query}' (k={args.k})")
        res = retriever.retrieve(args.query, mode=args.mode, k=args.k)
        print(f"Latency: {res.latency_ms} ms | Candidates: {res.total_candidates}")
        if res.sufficiency:
            print(f"Sufficiency: {'PASSED' if res.sufficiency.is_sufficient else 'REJECTED'} (Action: {res.sufficiency.recommended_action})")
            print(f"Reason Codes: {res.sufficiency.reason_codes}")
        print("\n--- GROUNDED EVIDENCE ---")
        print(res.get_evidence_context())


if __name__ == "__main__":
    main()
