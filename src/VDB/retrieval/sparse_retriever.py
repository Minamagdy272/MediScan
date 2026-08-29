"""
sparse_retriever.py - Lexical keyword retriever using BM25.
"""

from typing import List, Optional
from VDB.schema import EvidenceRecord, RetrievalFilters
from VDB.indexing.bm25_index import BM25Index


class SparseRetriever:
    """Performs exact term, abbreviation, and acronym matching via BM25."""

    def __init__(self, bm25_index: Optional[BM25Index] = None):
        self.index = bm25_index if bm25_index else BM25Index()

    def retrieve(
        self,
        query: str,
        k: int = 10,
        filter_obj: Optional[RetrievalFilters] = None,
    ) -> List[EvidenceRecord]:
        """Retrieve top-k chunks by BM25 score as EvidenceRecord list."""
        scored_chunks = self.index.search(
            query=query,
            k=k,
            filter_obj=filter_obj,
        )

        results: List[EvidenceRecord] = []
        for rank, (chunk, score) in enumerate(scored_chunks, 1):
            results.append(
                EvidenceRecord(
                    evidence_id=f"EV-{rank:03d}",
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.doc_id,
                    source_id=chunk.source_id,
                    content=chunk.content,
                    retrieval_score=score,
                    bm25_score=score,
                    rank=rank,
                    source_title=chunk.title,
                    source_type=chunk.source_type,
                    organization=chunk.metadata.get("organization", ""),
                    source_url=chunk.url,
                    condition=chunk.condition,
                    body_system=chunk.body_system,
                    knowledge_domain=chunk.knowledge_domain,
                    modality=chunk.metadata.get("modality", None),
                    audience=chunk.audience,
                    evidence_level=chunk.evidence_level,
                    publication_year=chunk.publication_year,
                    section=chunk.section_title,
                    metadata=chunk.metadata,
                )
            )
        return results
