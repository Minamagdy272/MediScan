"""
chunker.py - Section-aware document chunker generating stable, deterministic chunk_ids.
"""

from typing import List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter

from VDB.config import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, MAX_REPORT_CHUNK_SIZE
from VDB.schema import MedicalDocument, MedicalChunk
from VDB.processing.cleaner import clean_medical_text
from VDB.processing.section_parser import split_text_into_sections


class SectionAwareChunker:
    """Chunks MedicalDocuments respecting clinical section boundaries."""

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "; ", ", ", " "],
        )

    def chunk_document(self, doc: MedicalDocument) -> List[MedicalChunk]:
        """Split a single MedicalDocument into section-aware MedicalChunk objects."""
        chunks: List[MedicalChunk] = []

        # 1. Radiology reports (like OpenI) are concise and high-value:
        # Keep key sections intact (e.g. Findings, Impression) as atomic chunks when possible
        if doc.source_type == "radiology_report" and doc.sections:
            chunk_idx = 0
            
            # Combine Indication + Findings as a structured chunk
            findings_text = doc.sections.get("FINDINGS", "")
            impression_text = doc.sections.get("IMPRESSION", "")
            indication_text = doc.sections.get("INDICATION", "")

            # If small enough, create a complete atomic report chunk
            full_report = doc.get_full_text()
            if len(full_report) <= MAX_REPORT_CHUNK_SIZE:
                chunks.append(
                    MedicalChunk.create(
                        doc=doc,
                        content=full_report,
                        section_title="FULL_REPORT",
                        chunk_index=chunk_idx,
                        extra_meta={"has_impression": bool(impression_text)},
                    )
                )
                chunk_idx += 1
            else:
                # Chunk sections individually
                for sec_name, sec_text in doc.sections.items():
                    clean_sec = clean_medical_text(sec_text)
                    if not clean_sec:
                        continue
                    if len(clean_sec) <= self.chunk_size:
                        chunks.append(
                            MedicalChunk.create(
                                doc=doc,
                                content=f"[{sec_name}] {clean_sec}",
                                section_title=sec_name,
                                chunk_index=chunk_idx,
                            )
                        )
                        chunk_idx += 1
                    else:
                        sub_splits = self.text_splitter.split_text(clean_sec)
                        for sub_idx, sub_text in enumerate(sub_splits):
                            chunks.append(
                                MedicalChunk.create(
                                    doc=doc,
                                    content=f"[{sec_name}] {sub_text}",
                                    section_title=sec_name,
                                    chunk_index=chunk_idx,
                                )
                            )
                            chunk_idx += 1
            return chunks

        # 2. General medical documents (guidelines, research, references, patient education):
        # Extract sections first to avoid mixing unrelated clinical domains
        sections = doc.sections if doc.sections else split_text_into_sections(doc.raw_text)

        global_chunk_idx = 0
        for sec_name, sec_content in sections.items():
            cleaned_sec = clean_medical_text(sec_content)
            if not cleaned_sec:
                continue

            if len(cleaned_sec) <= self.chunk_size:
                prefix = f"[{doc.title} - {sec_name}]\n" if sec_name != "MAIN" else f"[{doc.title}]\n"
                chunks.append(
                    MedicalChunk.create(
                        doc=doc,
                        content=f"{prefix}{cleaned_sec}",
                        section_title=sec_name,
                        chunk_index=global_chunk_idx,
                    )
                )
                global_chunk_idx += 1
            else:
                sub_splits = self.text_splitter.split_text(cleaned_sec)
                for sub_text in sub_splits:
                    prefix = f"[{doc.title} - {sec_name}]\n" if sec_name != "MAIN" else f"[{doc.title}]\n"
                    chunks.append(
                        MedicalChunk.create(
                            doc=doc,
                            content=f"{prefix}{sub_text}",
                            section_title=sec_name,
                            chunk_index=global_chunk_idx,
                        )
                    )
                    global_chunk_idx += 1

        return chunks

    def chunk_documents(self, docs: List[MedicalDocument]) -> List[MedicalChunk]:
        """Chunk a batch of MedicalDocuments."""
        all_chunks = []
        for doc in docs:
            doc_chunks = self.chunk_document(doc)
            all_chunks.extend(doc_chunks)
        return all_chunks
