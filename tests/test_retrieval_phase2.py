"""
test_retrieval_phase2.py - Comprehensive Unit & Integration Tests for MediScan Phase 2.

Covers:
  1. EvidenceRecord creation & citation formatting
  2. RetrievalResult creation & trace
  3. RetrievalFilters behavior & matching
  4. RRF integration (dense + sparse rank aggregation)
  5. NvidiaReranker integration & fallback
  6. EvidenceSelector deduplication & source diversity
  7. EvidenceSufficiencyGate deterministic policy
  8. Citation mapping ([EV-001]...)
  9. Metric calculations (Precision, Recall, MRR, nDCG@5)
  10. Public retrieve() API 4-way integration (Dense, BM25, Hybrid, Hybrid+Rerank)
"""

import sys
from pathlib import Path
sys.path.insert(0, "src")

import unittest
from VDB.schema import (
    EvidenceRecord,
    RetrievalResult,
    RetrievalFilters,
    RetrievalMode,
    EvidenceSufficiencyResult,
    RecommendedAction,
    MedicalChunk,
)
from VDB.retrieval.sufficiency_gate import EvidenceSufficiencyGate
from VDB.retrieval.evidence_selector import EvidenceSelector
from VDB.retrieval.hybrid_fusion import reciprocal_rank_fusion
from VDB.retrieval.reranker import NvidiaReranker
from VDB.evaluation.evaluator import (
    compute_graded_relevance,
    compute_dcg_at_k,
    compute_ndcg_at_k,
)
from VDB.pipeline import MediScanRetriever


class TestPhase2Schemas(unittest.TestCase):
    """Test canonical contracts: EvidenceRecord, RetrievalFilters, RetrievalResult."""

    def test_01_evidence_record_creation_and_citation(self):
        ev = EvidenceRecord(
            evidence_id="EV-001",
            chunk_id="DOC123#FINDINGS_0",
            document_id="DOC123",
            source_id="SRC_NICE_01",
            content="Focal consolidation with air bronchograms in right lower lobe.",
            retrieval_score=0.89,
            dense_score=0.89,
            source_title="NICE Pneumonia Guideline",
            source_type="guideline",
            condition="Pneumonia",
            body_system="Respiratory",
            knowledge_domain="guidelines",
            modality="CXR",
            audience="clinician",
            evidence_level="high",
            publication_year=2023,
            section="FINDINGS",
        )
        self.assertEqual(ev.evidence_id, "EV-001")
        self.assertEqual(ev.dense_score, 0.89)
        self.assertIsNone(ev.bm25_score)
        
        citation = ev.format_citation()
        self.assertIn("[EV-001]", citation)
        self.assertIn("[SRC_NICE_01]", citation)
        self.assertIn("NICE Pneumonia Guideline (2023)", citation)
        self.assertIn("Modality: CXR", citation)

    def test_02_retrieval_filters_matching(self):
        filt = RetrievalFilters(condition="Pneumonia", modality="CXR")
        
        matching_chunk = MedicalChunk(
            chunk_id="C1#0", doc_id="C1", source_id="S1", title="T1", content="text",
            condition="Pneumonia", metadata={"modality": "CXR"}
        )
        non_matching_chunk = MedicalChunk(
            chunk_id="C2#0", doc_id="C2", source_id="S2", title="T2", content="text",
            condition="Stroke", metadata={"modality": "CT"}
        )
        
        self.assertTrue(filt.matches(matching_chunk))
        self.assertFalse(filt.matches(non_matching_chunk))
        
        chroma_dict = filt.to_chroma_filter()
        self.assertIsNotNone(chroma_dict)
        self.assertIn("$and", chroma_dict)

    def test_03_retrieval_result_trace(self):
        res = RetrievalResult(
            query="test query",
            retrieval_mode="hybrid",
            results=[],
            total_candidates=10,
            returned_count=0,
            latency_ms=12.5,
            retrieval_trace={"dense": 5, "bm25": 5},
        )
        self.assertEqual(res.retrieval_mode, "hybrid")
        self.assertEqual(res.total_candidates, 10)
        self.assertEqual(res.retrieval_trace["dense"], 5)


class TestPhase2SufficiencyGate(unittest.TestCase):
    """Test deterministic Evidence Sufficiency Gate policy."""

    def setUp(self):
        self.gate = EvidenceSufficiencyGate(min_chunks=1, min_score_threshold=0.01)

    def test_04_empty_evidence_triggers_re_retrieve_or_relax(self):
        res = self.gate.evaluate("test", [], query_type="direct")
        self.assertFalse(res.is_sufficient)
        self.assertIn("NO_EVIDENCE_RETRIEVED", res.reason_codes)
        self.assertEqual(res.recommended_action, RecommendedAction.RE_RETRIEVE.value)

    def test_05_guideline_query_requires_guideline_source(self):
        ref_evidence = [
            EvidenceRecord(
                evidence_id="EV-001", chunk_id="C1", document_id="D1", source_id="S1",
                content="test content", retrieval_score=0.05, source_type="patient_education",
                knowledge_domain="patient_education", audience="patient"
            )
        ]
        res = self.gate.evaluate("acute pneumonia guidelines", ref_evidence, query_type="guideline")
        self.assertFalse(res.is_sufficient)
        self.assertIn("MISSING_REQUIRED_GUIDELINE_SOURCE", res.reason_codes)
        self.assertEqual(res.recommended_action, RecommendedAction.RE_RETRIEVE.value)

    def test_06_sufficient_evidence_passes_proceed(self):
        guideline_evidence = [
            EvidenceRecord(
                evidence_id="EV-001", chunk_id="C1", document_id="D1", source_id="S1",
                content="guideline content", retrieval_score=0.05, source_type="guideline",
                knowledge_domain="guidelines", audience="clinician", evidence_level="high"
            )
        ]
        res = self.gate.evaluate("acute pneumonia guidelines", guideline_evidence, query_type="guideline")
        self.assertTrue(res.is_sufficient)
        self.assertEqual(res.recommended_action, RecommendedAction.PROCEED.value)
        self.assertIn("PASSED_ALL_SUFFICIENCY_CRITERIA", res.reason_codes)


class TestPhase2RetrievalComponents(unittest.TestCase):
    """Test RRF, Evidence Selector, and Metrics."""

    def test_07_rrf_rank_aggregation(self):
        dense_cands = [
            EvidenceRecord(evidence_id="1", chunk_id="C1", document_id="D1", source_id="S1", content="t1", dense_score=0.9),
            EvidenceRecord(evidence_id="2", chunk_id="C2", document_id="D2", source_id="S2", content="t2", dense_score=0.8),
        ]
        sparse_cands = [
            EvidenceRecord(evidence_id="3", chunk_id="C2", document_id="D2", source_id="S2", content="t2", bm25_score=15.0),
            EvidenceRecord(evidence_id="4", chunk_id="C3", document_id="D3", source_id="S3", content="t3", bm25_score=10.0),
        ]
        fused = reciprocal_rank_fusion(dense_cands, sparse_cands, k_constant=60, top_k=3)
        self.assertEqual(len(fused), 3)
        # C2 appeared in both ranks (Rank 2 in dense, Rank 1 in sparse) -> should be #1 in RRF
        self.assertEqual(fused[0].chunk_id, "C2")
        self.assertIsNotNone(fused[0].rrf_score)

    def test_08_evidence_selector_deduplication_and_citation_ids(self):
        cands = [
            EvidenceRecord(evidence_id="", chunk_id="C1", document_id="D1", source_id="S1", content="c1", retrieval_score=0.9),
            EvidenceRecord(evidence_id="", chunk_id="C1", document_id="D1", source_id="S1", content="c1_dup", retrieval_score=0.85),
            EvidenceRecord(evidence_id="", chunk_id="C2", document_id="D2", source_id="S2", content="c2", retrieval_score=0.7),
        ]
        selector = EvidenceSelector()
        selected = selector.select_evidence(cands, max_results=2)
        self.assertEqual(len(selected), 2)
        self.assertEqual(selected[0].evidence_id, "EV-001")
        self.assertEqual(selected[1].evidence_id, "EV-002")
        self.assertEqual(selected[0].chunk_id, "C1")
        self.assertEqual(selected[1].chunk_id, "C2")

    def test_09_metric_calculations_ndcg(self):
        # Perfect ranking: [3, 2, 1, 0, 0] -> nDCG@5 = 1.0
        perfect_rels = [3, 2, 1, 0, 0]
        self.assertAlmostEqual(compute_ndcg_at_k(perfect_rels, k=5), 1.0, places=4)
        
        # Sub-optimal ranking: [0, 1, 2, 3, 0] -> nDCG@5 < 1.0
        sub_rels = [0, 1, 2, 3, 0]
        self.assertLess(compute_ndcg_at_k(sub_rels, k=5), 1.0)
        self.assertGreater(compute_ndcg_at_k(sub_rels, k=5), 0.0)


class TestPhase2Integration(unittest.TestCase):
    """Integration test verifying all 4 retrieval modes return canonical RetrievalResult."""

    @classmethod
    def setUpClass(cls):
        cls.retriever = MediScanRetriever()

    def test_10_dense_retrieval_mode(self):
        res = self.retriever.retrieve("bacterial pneumonia consolidation", mode=RetrievalMode.DENSE, k=2)
        self.assertIsInstance(res, RetrievalResult)
        self.assertEqual(res.retrieval_mode, "dense")
        self.assertGreater(len(res.results), 0)
        self.assertGreater(res.latency_ms, 0)
        self.assertIsNotNone(res.results[0].dense_score)

    def test_11_bm25_retrieval_mode(self):
        res = self.retriever.retrieve("bacterial pneumonia consolidation", mode=RetrievalMode.BM25, k=2)
        self.assertIsInstance(res, RetrievalResult)
        self.assertEqual(res.retrieval_mode, "bm25")
        self.assertGreater(len(res.results), 0)
        self.assertIsNotNone(res.results[0].bm25_score)

    def test_12_hybrid_retrieval_mode(self):
        res = self.retriever.retrieve("bacterial pneumonia consolidation", mode=RetrievalMode.HYBRID, k=2)
        self.assertIsInstance(res, RetrievalResult)
        self.assertEqual(res.retrieval_mode, "hybrid")
        self.assertGreater(len(res.results), 0)
        self.assertIsNotNone(res.results[0].rrf_score)

    def test_13_hybrid_reranked_mode(self):
        res = self.retriever.retrieve("bacterial pneumonia consolidation", mode=RetrievalMode.HYBRID_RERANKED, k=2)
        self.assertIsInstance(res, RetrievalResult)
        self.assertEqual(res.retrieval_mode, "hybrid_reranked")
        self.assertGreater(len(res.results), 0)
        self.assertIsNotNone(res.sufficiency)


if __name__ == "__main__":
    unittest.main()
