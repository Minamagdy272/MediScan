"""
sufficiency_gate.py - Deterministic Evidence Sufficiency Gate for MediScan RAG.

Evaluates whether retrieved evidence is reliable, sufficient, and aligned with clinical intent
BEFORE downstream generation or agent consumption.

IMPORTANT: This gate is 100% deterministic and explainable in Python (NO runtime LLM).
"""

from typing import List, Optional, Dict, Any, Set
from VDB.schema import (
    EvidenceRecord,
    EvidenceSufficiencyResult,
    RetrievalFilters,
    RecommendedAction,
)


class EvidenceSufficiencyGate:
    """Deterministic, policy-driven evidence sufficiency evaluator."""

    def __init__(
        self,
        min_chunks: int = 1,
        min_score_threshold: float = 0.005,
        min_high_quality_count: int = 1,
        require_diversity_for_comparison: bool = True,
    ):
        self.min_chunks = min_chunks
        self.min_score_threshold = min_score_threshold
        self.min_high_quality_count = min_high_quality_count
        self.require_diversity_for_comparison = require_diversity_for_comparison

    def evaluate(
        self,
        query: str,
        evidence_list: List[EvidenceRecord],
        filters: Optional[RetrievalFilters] = None,
        query_type: str = "direct",  # direct, guideline, patient, comparison, cases
    ) -> EvidenceSufficiencyResult:
        """Evaluate evidence candidates against deterministic clinical policy."""
        reason_codes: List[str] = []
        
        # 1. Check if empty
        if not evidence_list:
            reason_codes.append("NO_EVIDENCE_RETRIEVED")
            recommended_action = RecommendedAction.RELAX_FILTER.value if (filters and filters.to_dict()) else RecommendedAction.RE_RETRIEVE.value
            return EvidenceSufficiencyResult(
                is_sufficient=False,
                reason_codes=reason_codes,
                valid_evidence_count=0,
                high_quality_evidence_count=0,
                source_count=0,
                source_diversity_count=0,
                best_retrieval_score=None,
                minimum_retrieval_score=None,
                matched_condition=False,
                matched_modality=False,
                required_source_type_satisfied=False,
                recommended_action=recommended_action,
            )

        # 2. Extract scores and counts
        scores = [e.retrieval_score for e in evidence_list]
        best_score = max(scores) if scores else 0.0
        min_score = min(scores) if scores else 0.0

        distinct_sources: Set[str] = {e.source_id for e in evidence_list}
        distinct_docs: Set[str] = {e.document_id for e in evidence_list}
        
        # Quality counts
        high_quality_evidence = [
            e for e in evidence_list
            if e.evidence_level in ("high", "moderate", "expert_consensus")
            or e.source_type in ("guideline", "reference", "research")
        ]
        guideline_evidence = [e for e in evidence_list if e.source_type == "guideline" or e.knowledge_domain == "guidelines"]
        patient_evidence = [e for e in evidence_list if e.audience == "patient" or e.knowledge_domain == "patient_education"]

        valid_count = len(evidence_list)
        high_qual_count = len(high_quality_evidence)
        source_count = len(distinct_sources)
        diversity_count = len(distinct_docs)

        # 3. Minimum chunks check
        required_min_chunks = self.min_chunks
        if query_type == "comparison":
            required_min_chunks = max(2, self.min_chunks)

        if valid_count < required_min_chunks:
            reason_codes.append(f"INSUFFICIENT_CHUNK_COUNT_{valid_count}_OF_{required_min_chunks}")

        # 4. Relevance score check
        if best_score < self.min_score_threshold:
            reason_codes.append(f"LOW_RELEVANCE_SCORE_BEST_{best_score:.4f}_BELOW_{self.min_score_threshold}")

        # 5. Policy-specific requirements
        required_source_satisfied = True

        if query_type == "guideline":
            if not guideline_evidence:
                required_source_satisfied = False
                reason_codes.append("MISSING_REQUIRED_GUIDELINE_SOURCE")

        elif query_type == "patient":
            if not patient_evidence and not any(e.audience in ("patient", "general") for e in evidence_list):
                # If no patient guide, but clinician guide exists, we flag it
                reason_codes.append("NO_PATIENT_SPECIFIC_SOURCE_FOUND")

        elif query_type == "comparison":
            if diversity_count < 2:
                reason_codes.append("INSUFFICIENT_SOURCE_DIVERSITY_FOR_COMPARISON")

        # 6. Condition / Modality matching check
        matched_cond = True
        matched_mod = True

        if filters:
            if filters.condition:
                norm_target = filters.condition.replace("_", " ").lower()
                has_cond_match = any(
                    norm_target in e.condition.replace("_", " ").lower() or
                    norm_target in e.content.lower()
                    for e in evidence_list
                )
                if not has_cond_match:
                    matched_cond = False
                    reason_codes.append("CONDITION_NOT_MATCHED_IN_TOP_RESULTS")

            if filters.modality:
                has_mod_match = any(
                    (e.modality and e.modality.lower() == filters.modality.lower()) or
                    filters.modality.lower() in e.content.lower()
                    for e in evidence_list
                )
                if not has_mod_match:
                    matched_mod = False
                    reason_codes.append("MODALITY_NOT_MATCHED_IN_TOP_RESULTS")

        # 7. Determine Sufficiency & Action
        is_sufficient = len(reason_codes) == 0

        if is_sufficient:
            recommended_action = RecommendedAction.PROCEED.value
            reason_codes.append("PASSED_ALL_SUFFICIENCY_CRITERIA")
        elif "NO_EVIDENCE_RETRIEVED" in reason_codes:
            recommended_action = RecommendedAction.RELAX_FILTER.value if (filters and filters.to_dict()) else RecommendedAction.RE_RETRIEVE.value
        elif "MISSING_REQUIRED_GUIDELINE_SOURCE" in reason_codes or "INSUFFICIENT_CHUNK_COUNT" in str(reason_codes):
            recommended_action = RecommendedAction.RE_RETRIEVE.value
        elif "LOW_RELEVANCE_SCORE" in str(reason_codes):
            recommended_action = RecommendedAction.EXPAND_QUERY.value
        elif "CONDITION_NOT_MATCHED_IN_TOP_RESULTS" in reason_codes:
            recommended_action = RecommendedAction.RELAX_FILTER.value
        else:
            recommended_action = RecommendedAction.SAFE_FALLBACK.value

        return EvidenceSufficiencyResult(
            is_sufficient=is_sufficient,
            reason_codes=reason_codes,
            valid_evidence_count=valid_count,
            high_quality_evidence_count=high_qual_count,
            source_count=source_count,
            source_diversity_count=diversity_count,
            best_retrieval_score=best_score,
            minimum_retrieval_score=min_score,
            matched_condition=matched_cond,
            matched_modality=matched_mod,
            required_source_type_satisfied=required_source_satisfied,
            recommended_action=recommended_action,
        )
