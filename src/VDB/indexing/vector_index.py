"""
vector_index.py - ChromaDB dense vector store manager for MediScan.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from VDB.config import VECTORSTORE_DIR
from VDB.schema import MedicalChunk, RetrievalFilter
from VDB.indexing.embeddings import get_embedding_function


class ChromaVectorIndex:
    """Manages dense vector storage and similarity search in ChromaDB."""

    def __init__(
        self,
        persist_dir: Optional[Path] = None,
        collection_name: str = "mediscan_rag",
        embeddings=None,
        reset_collection: bool = False,
    ):
        self.persist_dir = persist_dir if persist_dir else VECTORSTORE_DIR
        self.collection_name = collection_name
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings = embeddings if embeddings else get_embedding_function()

        if reset_collection:
            client = chromadb.PersistentClient(path=str(self.persist_dir))
            try:
                client.delete_collection(name=self.collection_name)
                print(f"Reset existing Chroma collection: '{self.collection_name}'")
            except Exception:
                pass
        
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_dir),
        )

    def add_chunks(self, chunks: List[MedicalChunk], batch_size: int = 25) -> int:
        """Add MedicalChunk objects to ChromaDB in batches."""
        if not chunks:
            return 0

        total_added = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            
            docs = [
                Document(
                    page_content=chunk.content,
                    metadata=chunk.to_chroma_dict(),
                )
                for chunk in batch
            ]
            ids = [chunk.chunk_id for chunk in batch]

            self.vectorstore.add_documents(documents=docs, ids=ids)
            total_added += len(batch)
            print(f"  Indexed batch {i//batch_size + 1}: {len(batch)} chunks (Total: {total_added}/{len(chunks)})")

        return total_added

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 10,
        filter_obj: Optional[RetrievalFilter] = None,
    ) -> List[Tuple[MedicalChunk, float]]:
        """Run vector similarity search with metadata filtering."""
        where_filter = filter_obj.to_chroma_where() if filter_obj else None

        results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=where_filter,
        )

        matched_chunks: List[Tuple[MedicalChunk, float]] = []
        for doc, dist in results:
            meta = doc.metadata or {}
            chunk = MedicalChunk(
                chunk_id=meta.get("doc_id", "") + "#" + meta.get("section_title", "MAIN") + "_" + str(meta.get("chunk_index", 0)),
                doc_id=meta.get("doc_id", ""),
                source_id=meta.get("source_id", ""),
                title=meta.get("title", ""),
                condition=meta.get("condition", ""),
                body_system=meta.get("body_system", ""),
                knowledge_domain=meta.get("knowledge_domain", ""),
                source_type=meta.get("source_type", ""),
                audience=meta.get("audience", ""),
                evidence_level=meta.get("evidence_level", ""),
                priority=meta.get("priority", "P2"),
                section_title=meta.get("section_title", ""),
                content=doc.page_content,
                url=meta.get("url", ""),
                publication_year=str(meta.get("publication_year", "")),
                chunk_index=int(meta.get("chunk_index", 0)),
                metadata=meta,
            )
            # Distance to normalized similarity score (lower distance = higher similarity)
            score = 1.0 / (1.0 + float(dist))
            matched_chunks.append((chunk, score))

        return matched_chunks

    def count(self) -> int:
        """Return total chunks in the collection."""
        try:
            return self.vectorstore._collection.count()
        except Exception:
            return 0
