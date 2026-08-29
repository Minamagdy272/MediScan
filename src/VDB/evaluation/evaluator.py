"""
evaluator.py - Comprehensive 4-Way Retrieval Benchmark Framework.

Calculates:
  - Precision@1, Precision@3, Precision@5
  - Recall@3, Recall@5
  - MRR (Mean Reciprocal Rank)
  - nDCG@5 (Graded relevance: 0=irrelevant, 1=weak, 2=relevant, 3=direct evidence)
  - Latency: Avg, P50, P95 (ms)
  - Sufficiency Pass Rate (%)
  - Source Diversity and Candidate Counts

Exports results to:
  - data/evaluation/retrieval_benchmark_results.csv
  - data/evaluation/retrieval_case_results.csv
"""

import csv
import math
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from VDB.config import PROJECT_ROOT
from VDB.schema import RetrievalResult, RetrievalMode, EvidenceRecord, RetrievalFilters
from VDB.evaluation.test_queries import BENCHMARK_CASES


def compute_graded_relevance(
    evidence: EvidenceRecord,
    case: Dict[str, Any]
) -> int:
    """Compute deterministic graded relevance (0, 1, 2, 3) for a retrieved evidence item."""
    score = 0
    content_lower = evidence.content.lower()
    cond_lower = evidence.condition.lower()
    
    expected_conds = [c.lower().replace("_", " ") for c in case.get("expected_conditions", [])]
    keywords = [kw.lower() for kw in case.get("keywords", [])]
    acceptable_sources = case.get("acceptable_source_ids", [])
    acceptable_domains = case.get("acceptable_knowledge_domains", [])

    # 1. Condition match
    cond_match = any(ec in cond_lower or ec in content_lower for ec in expected_conds)
    if cond_match:
        score += 1

    # 2. Keywords match
    matched_kws = sum(1 for kw in keywords if kw in content_lower)
    if matched_kws >= 2:
        score += 1
    elif matched_kws == 1 and score == 0:
        score += 1

    # 3. Source ID or Domain direct match bonus
    if evidence.source_id in acceptable_sources or evidence.knowledge_domain in acceptable_domains:
        if matched_kws >= 2 and cond_match:
            score = 3
        elif score >= 1:
            score = max(score, 2)

    return min(score, 3)


def compute_dcg_at_k(relevances: List[int], k: int = 5) -> float:
    """Discounted Cumulative Gain at K."""
    dcg = 0.0
    for i, rel in enumerate(relevances[:k], 1):
        dcg += (2**rel - 1) / math.log2(i + 1)
    return dcg


def compute_ndcg_at_k(relevances: List[int], k: int = 5) -> float:
    """Normalized Discounted Cumulative Gain at K."""
    actual_dcg = compute_dcg_at_k(relevances, k)
    ideal_relevances = sorted(relevances, reverse=True)
    ideal_dcg = compute_dcg_at_k(ideal_relevances, k)
    if ideal_dcg == 0.0:
        return 1.0 if actual_dcg == 0.0 else 0.0
    return actual_dcg / ideal_dcg


class RetrievalBenchmarkRunner:
    """Executes benchmark evaluation across Dense, BM25, Hybrid, and Hybrid+Reranker."""

    def __init__(self, retriever):
        self.retriever = retriever
        self.output_dir = PROJECT_ROOT / "data" / "evaluation"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_mode(
        self,
        mode: Union[RetrievalMode, str],
        cases: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Run benchmark for a single retrieval mode."""
        if cases is None:
            cases = BENCHMARK_CASES

        mode_str = mode.value if isinstance(mode, RetrievalMode) else str(mode).lower()
        print(f"\nEvaluating Retrieval Mode: [{mode_str.upper()}] across {len(cases)} cases...")

        p1_list, p3_list, p5_list = [], [], []
        r3_list, r5_list = [], []
        rr_list, ndcg5_list = [], []
        latencies = []
        candidates_counts = []
        final_counts = []
        sufficiency_passes = 0
        case_records: List[Dict[str, Any]] = []

        for case in cases:
            cid = case["case_id"]
            query = case["query"]

            # Optional filter by modality if query specifies CXR/CT
            filt = None
            if case.get("modality"):
                filt = RetrievalFilters(modality=case["modality"])

            # Execute single retrieval call
            t_start = time.perf_counter()
            res: RetrievalResult = self.retriever.retrieve(
                query=query,
                mode=mode_str,
                k=top_k,
                filters=filt,
                require_sufficient_evidence=True,
            )
            lat = res.latency_ms if res.latency_ms > 0 else (time.perf_counter() - t_start) * 1000
            latencies.append(lat)
            candidates_counts.append(res.total_candidates)
            final_counts.append(res.returned_count)

            if res.sufficiency and res.sufficiency.is_sufficient:
                sufficiency_passes += 1

            # Grade relevance for top-K results
            relevances = [compute_graded_relevance(item, case) for item in res.results]
            while len(relevances) < top_k:
                relevances.append(0)

            # Record detailed per-case metrics
            for rank, (item, rel) in enumerate(zip(res.results, relevances), 1):
                case_records.append({
                    "case_id": cid,
                    "mode": mode_str,
                    "rank": rank,
                    "evidence_id": item.evidence_id,
                    "chunk_id": item.chunk_id,
                    "source_id": item.source_id,
                    "source_type": item.source_type,
                    "condition": item.condition,
                    "retrieval_score": round(item.retrieval_score, 4),
                    "rerank_score": round(item.rerank_score, 4) if item.rerank_score is not None else "N/A",
                    "relevant_label": rel,
                })

            # Precision@K
            p1 = 1.0 if relevances[0] >= 2 else 0.0
            p3 = sum(1 for r in relevances[:3] if r >= 2) / 3.0
            p5 = sum(1 for r in relevances[:5] if r >= 2) / 5.0
            p1_list.append(p1)
            p3_list.append(p3)
            p5_list.append(p5)

            # Recall@K (assuming 1 primary expected relevant piece in top-K)
            r3 = 1.0 if any(r >= 2 for r in relevances[:3]) else 0.0
            r5 = 1.0 if any(r >= 2 for r in relevances[:5]) else 0.0
            r3_list.append(r3)
            r5_list.append(r5)

            # MRR
            first_rel_rank = 0
            for rank, r in enumerate(relevances, 1):
                if r >= 2:
                    first_rel_rank = rank
                    break
            rr = (1.0 / first_rel_rank) if first_rel_rank > 0 else 0.0
            rr_list.append(rr)

            # nDCG@5
            ndcg5 = compute_ndcg_at_k(relevances, k=5)
            ndcg5_list.append(ndcg5)

        summary = {
            "mode": mode_str,
            "precision_at_1": round(float(np.mean(p1_list)), 4),
            "precision_at_3": round(float(np.mean(p3_list)), 4),
            "precision_at_5": round(float(np.mean(p5_list)), 4),
            "recall_at_3": round(float(np.mean(r3_list)), 4),
            "recall_at_5": round(float(np.mean(r5_list)), 4),
            "mrr": round(float(np.mean(rr_list)), 4),
            "ndcg_at_5": round(float(np.mean(ndcg5_list)), 4),
            "avg_latency_ms": round(float(np.mean(latencies)), 2),
            "p50_latency_ms": round(float(np.percentile(latencies, 50)), 2),
            "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
            "sufficiency_pass_rate": round(sufficiency_passes / len(cases), 4),
            "avg_candidates": round(float(np.mean(candidates_counts)), 1),
            "avg_final_results": round(float(np.mean(final_counts)), 1),
        }

        return summary, case_records

    def run_full_4way_benchmark(self) -> List[Dict[str, Any]]:
        """Run the complete 4-way comparative ablation study."""
        print("=" * 80)
        print("    MEDISCAN PHASE 2 - 4-WAY RETRIEVAL ABLATION BENCHMARK")
        print("=" * 80)

        modes = [
            RetrievalMode.DENSE,
            RetrievalMode.BM25,
            RetrievalMode.HYBRID,
            RetrievalMode.HYBRID_RERANKED,
        ]

        all_summaries: List[Dict[str, Any]] = []
        all_case_records: List[Dict[str, Any]] = []

        for mode in modes:
            summary, case_recs = self.evaluate_mode(mode)
            all_summaries.append(summary)
            all_case_records.extend(case_recs)

        # 1. Save summary CSV
        summary_csv_path = self.output_dir / "retrieval_benchmark_results.csv"
        fieldnames = list(all_summaries[0].keys())
        with open(summary_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_summaries)
        print(f"\nSaved 4-way benchmark summary to: {summary_csv_path}")

        # 2. Save case-level CSV
        case_csv_path = self.output_dir / "retrieval_case_results.csv"
        if all_case_records:
            case_fields = list(all_case_records[0].keys())
            with open(case_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=case_fields)
                writer.writeheader()
                writer.writerows(all_case_records)
            print(f"Saved case-level results ({len(all_case_records)} rows) to: {case_csv_path}")

        # Print Markdown Table
        print("\n" + "=" * 105)
        print("                             4-WAY BENCHMARK SUMMARY TABLE")
        print("=" * 105)
        header = f"{'Mode':<18} | {'P@1':<6} | {'P@3':<6} | {'P@5':<6} | {'R@3':<6} | {'R@5':<6} | {'MRR':<6} | {'nDCG@5':<7} | {'Avg Lat(ms)':<11} | {'Suff Rate':<9}"
        print(header)
        print("-" * len(header))
        for s in all_summaries:
            print(
                f"{s['mode']:<18} | "
                f"{s['precision_at_1']:<6.3f} | "
                f"{s['precision_at_3']:<6.3f} | "
                f"{s['precision_at_5']:<6.3f} | "
                f"{s['recall_at_3']:<6.3f} | "
                f"{s['recall_at_5']:<6.3f} | "
                f"{s['mrr']:<6.3f} | "
                f"{s['ndcg_at_5']:<7.3f} | "
                f"{s['avg_latency_ms']:<11.1f} | "
                f"{s['sufficiency_pass_rate']*100:<8.1f}%"
            )
        print("=" * 105 + "\n")

        return all_summaries


if __name__ == "__main__":
    from VDB.pipeline import MediScanRetriever
    runner = RetrievalBenchmarkRunner(MediScanRetriever())
    runner.run_full_4way_benchmark()
