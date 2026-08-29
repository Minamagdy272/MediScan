"""
index_builder.py - Orchestrates full knowledge base ingestion, chunking, and index building.
"""

from pathlib import Path
from typing import List, Optional

from VDB.config import OPENI_XML_DIR, CLEANED_DATA_DIR
from VDB.schema import MedicalDocument, MedicalChunk
from VDB.acquisition.openi_loader import load_all_openi_reports
from VDB.acquisition.local_loader import load_local_cleaned_documents
from VDB.processing.chunker import SectionAwareChunker
from VDB.indexing.vector_index import ChromaVectorIndex
from VDB.indexing.bm25_index import BM25Index


def build_complete_knowledge_index(
    include_openi: bool = True,
    max_openi_reports: Optional[int] = 500,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> tuple[ChromaVectorIndex, BM25Index, List[MedicalChunk]]:
    """Build both dense ChromaDB and sparse BM25 indices from all acquired documents.

    Parameters
    ----------
    include_openi : bool
        Whether to parse and include OpenI individual XML reports.
    max_openi_reports : int, optional
        Limit for OpenI reports (None for all).
    """
    print("=" * 60)
    print("  MediScan Index Building Pipeline")
    print("=" * 60)

    # 1. Load all local documents (guidelines, references, research, patient care)
    print("\n[1/4] Loading local reference & guideline documents...")
    all_docs: List[MedicalDocument] = load_local_cleaned_documents()

    # 2. Load individual OpenI XML reports
    if include_openi:
        print(f"\n[2/4] Loading independent OpenI XML reports (max: {max_openi_reports})...")
        openi_docs = load_all_openi_reports(max_reports=max_openi_reports)
        all_docs.extend(openi_docs)

    print(f"\nTotal loaded independent documents: {len(all_docs)}")

    # 3. Section-aware chunking
    print("\n[3/4] Performing section-aware chunking with stable chunk_ids...")
    chunker = SectionAwareChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = chunker.chunk_documents(all_docs)
    print(f"Total section-aware chunks generated: {len(chunks)}")

    # 4. Build Dense Vector Index (ChromaDB)
    print("\n[4/4] Building indices...")
    vector_idx = ChromaVectorIndex(reset_collection=True)
    vector_idx.add_chunks(chunks)

    # 5. Build Sparse BM25 Index
    bm25_idx = BM25Index()
    bm25_idx.build_index(chunks)

    print("\n" + "=" * 60)
    print("  Indexing Complete!")
    print(f"  ChromaDB Chunks: {vector_idx.count()}")
    print(f"  BM25 Corpus Size: {len(chunks)}")
    print("=" * 60)

    return vector_idx, bm25_idx, chunks


if __name__ == "__main__":
    build_complete_knowledge_index()
