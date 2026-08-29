"""
evidence_selector.py - Selects, deduplicates, and formats canonical EvidenceRecords.

Applies source diversity, condition matching, duplicate suppression, and deterministic
citation mapping ([EV-001], [EV-002]...) to produce the final EvidenceRecord list.
"""

from typing import List, Optional, Set
from VDB.schema import EvidenceRecord, SearchResult, MedicalChunk


class EvidenceSelector:
    """Filters, deduplicates, and formats evidence records for downstream LLM/Agents."""

    def __init__(self, max_tokens_estimate: int = 3000):
        self.max_tokens_estimate = max_tokens_estimate

    def select_evidence(
        self,
        candidates: List[EvidenceRecord],
        max_results: int = 5,
        min_score: Optional[float] = None,
        prefer_diversity: bool = True,
    ) -> List[EvidenceRecord]:
        """Deduplicate, filter, and assign stable citation IDs [EV-001]... to top evidence."""
        if not candidates:
            return []

        seen_chunk_ids: Set[str] = set()
        seen_doc_ids: Set[str] = set()
        selected: List[EvidenceRecord] = []

        # Pass 1: Prioritize unique documents for source diversity
        for cand in candidates:
            if min_score is not None and cand.retrieval_score < min_score:
                continue

            if cand.chunk_id in seen_chunk_ids:
                continue

            # If diversity preferred, prioritize distinct documents first
            if prefer_diversity and cand.document_id in seen_doc_ids and len(selected) < max_results:
                continue

            seen_chunk_ids.add(cand.chunk_id)
            seen_doc_ids.add(cand.document_id)
            selected.append(cand)

            if len(selected) >= max_results:
                break

        # Pass 2: Fill remaining slots if diversity filter skipped good chunks
        if len(selected) < max_results:
            for cand in candidates:
                if min_score is not None and cand.retrieval_score < min_score:
                    continue
                if cand.chunk_id not in seen_chunk_ids:
                    seen_chunk_ids.add(cand.chunk_id)
                    selected.append(cand)
                    if len(selected) >= max_results:
                        break

        # Assign deterministic citation identifiers and ranks
        final_records: List[EvidenceRecord] = []
        for rank, item in enumerate(selected, 1):
            item.evidence_id = f"EV-{rank:03d}"
            item.rank = rank
            final_records.append(item)

        return final_records

    def format_grounded_context(self, evidence_list: List[EvidenceRecord]) -> str:
        """Format grounded evidence block with strict citations."""
        if not evidence_list:
            return "No relevant medical evidence found in knowledge base."

        formatted_blocks = []
        for res in evidence_list:
            formatted_blocks.append(
                f"--- EVIDENCE ITEM {res.evidence_id} ---\n"
                f"{res.format_citation()}"
            )

        return "\n\n".join(formatted_blocks)
