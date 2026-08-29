"""
dense_retriever.py - Vector similarity retriever using ChromaDB.
"""

from typing import List, Optional
from VDB.schema import EvidenceRecord, RetrievalFilters, SearchResult
from VDB.indexing.vector_index import ChromaVectorIndex


class DenseRetriever:
    """Performs semantic dense retrieval over ChromaDB."""

    def __init__(self, vector_index: Optional[ChromaVectorIndex] = None):
        self.index = vector_index if vector_index else ChromaVectorIndex()

    def retrieve(
        self,
        query: str,
        k: int = 10,
        filter_obj: Optional[RetrievalFilters] = None,
    ) -> List[EvidenceRecord]:
        """Retrieve top-k chunks by vector similarity as EvidenceRecord list."""
        scored_chunks = self.index.similarity_search_with_score(
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
                    dense_score=score,
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
