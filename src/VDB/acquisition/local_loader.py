"""
local_loader.py - Load local cleaned/raw text files into MedicalDocument objects.
"""

from pathlib import Path
from typing import List, Optional
import os

from VDB.config import DATA_DIR, CLEANED_DATA_DIR
from VDB.schema import MedicalDocument


def infer_domain_from_path(file_path: Path) -> tuple[str, str, str]:
    """Infer (condition, body_system, knowledge_domain, audience) from file path."""
    path_str = str(file_path).lower().replace("\\", "/")
    
    # Body system inference
    body_system = "general"
    if "cardiovascular" in path_str or "heart" in path_str:
        body_system = "cardiovascular"
    elif "respiratory" in path_str or "lung" in path_str or "chest" in path_str:
        body_system = "respiratory"
    elif "neurology" in path_str or "stroke" in path_str or "hemorrhage" in path_str:
        body_system = "neurology"
    elif "gastrointestinal" in path_str or "pancreatitis" in path_str or "appendicitis" in path_str:
        body_system = "gastrointestinal"
    elif "renal" in path_str or "kidney" in path_str:
        body_system = "renal"
    elif "oncology" in path_str or "cancer" in path_str:
        body_system = "oncology"

    # Domain & Audience inference
    knowledge_domain = "clinical_references"
    audience = "clinician"
    source_type = "clinical_reference"

    if "guideline" in path_str:
        knowledge_domain = "guidelines"
        source_type = "guideline"
        audience = "clinician"
    elif "patient" in path_str or "medlineplus" in path_str:
        knowledge_domain = "patient_education"
        source_type = "patient_education"
        audience = "patient"
    elif "research" in path_str or "review" in path_str or "meta" in path_str:
        knowledge_domain = "research"
        source_type = "research_article"
        audience = "clinician"
    elif "case" in path_str or "report" in path_str:
        knowledge_domain = "cases"
        source_type = "case_report"
        audience = "clinician"
    elif "radiology" in path_str:
        knowledge_domain = "radiology_reference"
        source_type = "radiology_guide"
        audience = "clinician"

    # Condition inference
    condition = file_path.stem.replace("_", " ").title()
    for known in [
        "Pneumonia", "Pleural Effusion", "Pneumothorax", "Pulmonary Edema",
        "COPD", "Heart Failure", "Cardiomegaly", "Ischemic Stroke",
        "Intracranial Hemorrhage", "Appendicitis", "Pancreatitis",
        "Kidney Stones", "Lung Cancer", "Pulmonary Nodules", "Consolidation"
    ]:
        if known.lower() in path_str:
            condition = known.replace(" ", "_")
            break

    return condition, body_system, knowledge_domain, source_type, audience


def load_local_cleaned_documents(
    cleaned_dir: Optional[Path] = None,
) -> List[MedicalDocument]:
    """Load all cleaned .txt documents (excluding openi_reports.txt) into MedicalDocuments."""
    if cleaned_dir is None:
        cleaned_dir = CLEANED_DATA_DIR

    if not cleaned_dir.is_dir():
        print(f"Cleaned directory not found at {cleaned_dir}")
        return []

    documents = []
    for txt_file in cleaned_dir.rglob("*.txt"):
        # We process OpenI XML files individually, so skip the legacy combined file
        if txt_file.name == "openi_reports.txt":
            continue

        raw_text = txt_file.read_text(encoding="utf-8", errors="ignore").strip()
        if len(raw_text) < 50:
            continue

        cond, body_sys, domain, src_type, audience = infer_domain_from_path(txt_file)
        doc_id = f"LOCAL_{txt_file.stem}"

        doc = MedicalDocument(
            doc_id=doc_id,
            source_id=f"SRC_LOCAL_{txt_file.stem[:12]}",
            title=txt_file.stem.replace("_", " "),
            condition=cond,
            body_system=body_sys,
            knowledge_domain=domain,
            source_type=src_type,
            audience=audience,
            evidence_level="guideline" if domain == "guidelines" else "clinical_reference",
            priority="P1" if domain == "guidelines" else "P2",
            url="",
            publication_year="2023",
            sections={},
            raw_text=raw_text,
            metadata={"source_file": str(txt_file.name), "file_path": str(txt_file)},
        )
        documents.append(doc)

    print(f"Loaded {len(documents)} local cleaned reference documents.")
    return documents
