"""
schema.py - Unified Data Models and Typed Contracts for MediScan VDB & Evidence Retrieval.

Defines the canonical contracts for Phase 2:
  - SourceRecord, DocumentRecord, ChunkRecord
  - EvidenceRecord (canonical evidence object preserving full provenance & nullable scores)
  - RetrievalFilters (typed deterministic metadata filters)
  - EvidenceSufficiencyResult (deterministic gate evaluation result)
  - RetrievalResult (canonical public retrieval response with trace and latency)
  - RetrievalMode enum
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import hashlib
import time


class RetrievalMode(str, Enum):
    """Supported retrieval operational modes."""
    DENSE = "dense"
    BM25 = "bm25"
    HYBRID = "hybrid"
    HYBRID_RERANKED = "hybrid_reranked"


class RecommendedAction(str, Enum):
    """Deterministic actions recommended by the Evidence Sufficiency Gate."""
    PROCEED = "PROCEED"
    RE_RETRIEVE = "RE_RETRIEVE"
    EXPAND_QUERY = "EXPAND_QUERY"
    RELAX_FILTER = "RELAX_FILTER"
    SAFE_FALLBACK = "SAFE_FALLBACK"
    HUMAN_REVIEW = "HUMAN_REVIEW"


@dataclass
class SourceRecord:
    """Represents a registered medical source repository or publisher."""
    source_id: str
    title: str
    organization: str = ""
    source_type: str = "guideline"  # guideline, reference, research, patient_education, cases
    source_url: str = ""
    evidence_level: str = "expert_consensus"
    publication_year: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MedicalDocument:
    """Represents an ingested medical document before chunking."""
    doc_id: str
    source_id: str
    title: str
    raw_text: str
    condition: str = "General"
    body_system: str = "General"
    knowledge_domain: str = "clinical_references"
    source_type: str = "reference"
    audience: str = "clinician"
    evidence_level: str = "moderate"
    publication_year: Optional[int] = None
    url: str = ""
    sections: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Backward compatibility alias
DocumentRecord = MedicalDocument


@dataclass
class MedicalChunk:
    """Represents a section-aware chunk with stable deterministic identifier."""
    chunk_id: str
    doc_id: str
    source_id: str
    title: str
    content: str
    section_title: str = "MAIN"
    chunk_index: int = 0
    condition: str = "General"
    body_system: str = "General"
    knowledge_domain: str = "clinical_references"
    source_type: str = "reference"
    audience: str = "clinician"
    evidence_level: str = "moderate"
    priority: str = "medium"
    publication_year: Optional[int] = None
    url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def generate_chunk_id(doc_id: str, section_title: str, chunk_index: int) -> str:
        """Deterministic chunk ID format: {doc_id}#{SECTION}_{idx}"""
        clean_sec = section_title.upper().replace(" ", "_").strip()
        return f"{doc_id}#{clean_sec}_{chunk_index}"

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Convert chunk metadata to flat dictionary for ChromaDB."""
        meta = {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "source_id": self.source_id,
            "title": self.title,
            "section_title": self.section_title,
            "chunk_index": self.chunk_index,
            "condition": self.condition,
            "body_system": self.body_system,
            "knowledge_domain": self.knowledge_domain,
            "source_type": self.source_type,
            "audience": self.audience,
            "evidence_level": self.evidence_level,
            "publication_year": self.publication_year if self.publication_year else 0,
            "url": self.url,
        }
        for k, v in self.metadata.items():
            if isinstance(v, (str, int, float, bool)):
                meta[f"meta_{k}"] = v
        return meta


# Backward compatibility alias
ChunkRecord = MedicalChunk


@dataclass
class EvidenceRecord:
    """Canonical evidence record preserving full provenance, metadata, and multi-model scores."""
    evidence_id: str                          # e.g., EV-001
    chunk_id: str                             # Stable chunk ID (e.g. OpenI_CXR1000#FINDINGS_0)
    document_id: str                          # Document ID
    source_id: str                            # Source registry ID
    content: str                              # Cleaned evidence text

    # Multi-retrieval scores (nullable where not applicable)
    retrieval_score: float = 0.0              # Primary composite score
    dense_score: Optional[float] = None       # Vector distance / cosine similarity
    bm25_score: Optional[float] = None        # Okapi BM25 lexical score
    rrf_score: Optional[float] = None         # Reciprocal Rank Fusion score
    rerank_score: Optional[float] = None      # Cross-encoder logit

    rank: int = 1                             # Final rank in result set

    # Source & Publisher Provenance
    source_title: str = ""
    source_type: str = "reference"            # guideline, reference, research, patient_education, cases
    organization: str = ""
    source_url: str = ""
    full_text_url: str = ""

    # Clinical Taxonomy
    condition: str = "General"
    body_system: str = "General"
    knowledge_domain: str = "clinical_references"
    modality: Optional[str] = None            # CXR, CT, MRI, US, None
    exam: Optional[str] = None
    lab: Optional[str] = None

    # Context & Quality
    audience: str = "clinician"               # clinician, patient, general
    evidence_level: str = "moderate"          # high, moderate, low, expert_consensus
    publication_year: Optional[int] = None
    section: str = "MAIN"
    local_path: str = ""

    metadata: Dict[str, Any] = field(default_factory=dict)

    def format_citation(self) -> str:
        """Deterministic citation header and body for LLM context injection."""
        mod_str = f" | Modality: {self.modality}" if self.modality else ""
        year_str = f" ({self.publication_year})" if self.publication_year else ""
        return (
            f"[{self.evidence_id}] [{self.source_id}] {self.source_title}{year_str}\n"
            f"Provenance: {self.chunk_id} | Domain: {self.knowledge_domain} | Section: {self.section}{mod_str}\n"
            f"Evidence Level: {self.evidence_level} | Audience: {self.audience}\n"
            f"Content:\n{self.content}"
        )


@dataclass
class EvidenceSufficiencyResult:
    """Deterministic result of the Evidence Sufficiency Gate."""
    is_sufficient: bool
    reason_codes: List[str] = field(default_factory=list)
    valid_evidence_count: int = 0
    high_quality_evidence_count: int = 0
    source_count: int = 0
    source_diversity_count: int = 0
    best_retrieval_score: Optional[float] = None
    minimum_retrieval_score: Optional[float] = None
    matched_condition: bool = True
    matched_modality: bool = True
    required_source_type_satisfied: bool = True
    recommended_action: str = RecommendedAction.PROCEED.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_sufficient": self.is_sufficient,
            "reason_codes": self.reason_codes,
            "valid_evidence_count": self.valid_evidence_count,
            "high_quality_evidence_count": self.high_quality_evidence_count,
            "source_count": self.source_count,
            "source_diversity_count": self.source_diversity_count,
            "best_retrieval_score": self.best_retrieval_score,
            "minimum_retrieval_score": self.minimum_retrieval_score,
            "matched_condition": self.matched_condition,
            "matched_modality": self.matched_modality,
            "required_source_type_satisfied": self.required_source_type_satisfied,
            "recommended_action": self.recommended_action,
        }


@dataclass
class RetrievalFilters:
    """Typed deterministic metadata filters for precision routing."""
    condition: Optional[str] = None
    body_system: Optional[str] = None
    knowledge_domain: Optional[str] = None
    source_type: Optional[str] = None
    audience: Optional[str] = None
    modality: Optional[str] = None
    exam: Optional[str] = None
    lab: Optional[str] = None
    publication_year: Optional[int] = None
    evidence_level: Optional[str] = None

    def to_chroma_filter(self) -> Optional[Dict[str, Any]]:
        """Translate typed filter into ChromaDB where dictionary."""
        conditions = []
        if self.condition:
            conditions.append({"condition": self.condition})
        if self.body_system:
            conditions.append({"body_system": self.body_system})
        if self.knowledge_domain:
            conditions.append({"knowledge_domain": self.knowledge_domain})
        if self.source_type:
            conditions.append({"source_type": self.source_type})
        if self.audience:
            conditions.append({"audience": self.audience})
        if self.evidence_level:
            conditions.append({"evidence_level": self.evidence_level})
        if self.modality:
            conditions.append({"meta_modality": self.modality})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def to_chroma_where(self) -> Optional[Dict[str, Any]]:
        """Alias for to_chroma_filter."""
        return self.to_chroma_filter()

    def matches(self, chunk: MedicalChunk) -> bool:
        """Check if a chunk matches this filter in memory."""
        if self.condition:
            norm_q = self.condition.replace("_", " ").strip().lower()
            norm_c = chunk.condition.replace("_", " ").strip().lower()
            if norm_q != norm_c and norm_q not in norm_c:
                return False
        if self.body_system:
            if self.body_system.lower() != chunk.body_system.lower():
                return False
        if self.knowledge_domain:
            if self.knowledge_domain.lower() != chunk.knowledge_domain.lower():
                return False
        if self.source_type:
            if self.source_type.lower() != chunk.source_type.lower():
                return False
        if self.audience:
            if self.audience.lower() != chunk.audience.lower():
                return False
        if self.evidence_level:
            if self.evidence_level.lower() != chunk.evidence_level.lower():
                return False
        if self.modality:
            chunk_mod = chunk.metadata.get("modality", "")
            if chunk_mod and chunk_mod.lower() != self.modality.lower():
                return False
        if self.publication_year:
            if chunk.publication_year and chunk.publication_year < self.publication_year:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


# Backward compatibility alias
RetrievalFilter = RetrievalFilters


@dataclass
class RetrievalResult:
    """Canonical public retrieval response structure with trace and sufficiency."""
    query: str
    retrieval_mode: str                        # dense, bm25, hybrid, hybrid_reranked
    results: List[EvidenceRecord] = field(default_factory=list)
    total_candidates: int = 0
    returned_count: int = 0
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    reranking_applied: bool = False
    sufficiency: Optional[EvidenceSufficiencyResult] = None
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieval_trace: Dict[str, Any] = field(default_factory=dict)

    def get_evidence_context(self) -> str:
        """Returns clean formatted citations ready for prompt injection."""
        if not self.results:
            return "No relevant medical evidence found in knowledge base."
        return "\n\n".join(r.format_citation() for r in self.results)


# Backward compatibility wrapper
@dataclass
class SearchResult:
    """Legacy SearchResult compatibility wrapper converting to/from EvidenceRecord."""
    chunk: MedicalChunk
    score: float
    retriever_type: str = "dense"
    rank: int = 1

    def to_evidence_record(self, evidence_id: Optional[str] = None) -> EvidenceRecord:
        eid = evidence_id if evidence_id else f"EV-{self.rank:03d}"
        return EvidenceRecord(
            evidence_id=eid,
            chunk_id=self.chunk.chunk_id,
            document_id=self.chunk.doc_id,
            source_id=self.chunk.source_id,
            content=self.chunk.content,
            retrieval_score=self.score,
            dense_score=self.score if "dense" in self.retriever_type else None,
            bm25_score=self.score if "sparse" in self.retriever_type or "bm25" in self.retriever_type else None,
            rrf_score=self.score if "rrf" in self.retriever_type or "hybrid" in self.retriever_type else None,
            rerank_score=self.score if "rerank" in self.retriever_type else None,
            rank=self.rank,
            source_title=self.chunk.title,
            source_type=self.chunk.source_type,
            organization=self.chunk.metadata.get("organization", ""),
            source_url=self.chunk.url,
            condition=self.chunk.condition,
            body_system=self.chunk.body_system,
            knowledge_domain=self.chunk.knowledge_domain,
            modality=self.chunk.metadata.get("modality", None),
            audience=self.chunk.audience,
            evidence_level=self.chunk.evidence_level,
            publication_year=self.chunk.publication_year,
            section=self.chunk.section_title,
            metadata=self.chunk.metadata,
        )

    def format_citation(self) -> str:
        return self.to_evidence_record().format_citation()
