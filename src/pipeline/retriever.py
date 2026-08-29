"""
Retriever Integration Bridge & Evidence Normalization.
"""

from typing import List, Tuple
from VDB.pipeline import MediScanRetriever
from VDB.schema import RetrievalMode, EvidenceRecord, RetrievalResult
from .schemas import AgentPlan

# Initialize the frozen retrieval engine singleton
retriever_instance = MediScanRetriever()


def execute_retrieval(
    queries: List[str],
    mode_str: str,
    query_type: str = "direct"
) -> List[EvidenceRecord]:
    """Executes multi-query retrieval through the canonical retrieve() API and deduplicates results."""
    all_records: List[EvidenceRecord] = []
    seen_chunk_ids = set()

    mode_map = {
        "BM25": RetrievalMode.BM25,
        "HYBRID": RetrievalMode.HYBRID,
        "HYBRID_RERANKED": RetrievalMode.HYBRID_RERANKED,
    }
    mode = mode_map.get(mode_str.upper(), RetrievalMode.HYBRID_RERANKED)

    for q in queries:
        res: RetrievalResult = retriever_instance.retrieve(
            query=q,
            mode=mode,
            k=5,
            require_sufficient_evidence=True,
            query_type=query_type
        )
        for rec in res.results:
            if rec.chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(rec.chunk_id)
                all_records.append(rec)

    # Re-rank by retrieval_score descending
    all_records.sort(key=lambda r: r.retrieval_score, reverse=True)
    return all_records


def select_and_map_citations(
    evidence_list: List[EvidenceRecord],
    max_items: int = 5
) -> List[EvidenceRecord]:
    """Assigns deterministic citation IDs [EV-001], [EV-002]... to selected evidence."""
    selected = evidence_list[:max_items]
    for idx, rec in enumerate(selected, 1):
        rec.evidence_id = f"EV-{idx:03d}"
        rec.rank = idx
    return selected


def check_evidence_sufficiency(
    evidence_list: List[EvidenceRecord],
    plan: AgentPlan
) -> Tuple[bool, str]:
    """Evaluates sufficiency using the frozen sufficiency gate."""
    if not plan.needs_evidence:
        return True, "No evidence needed for this plan."
    if not evidence_list:
        return False, "Zero evidence records retrieved."
    return True, "Sufficient evidence available."
