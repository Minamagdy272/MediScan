"""
openi_loader.py - Individual OpenI XML chest X-ray report parser.

Parses every OpenI report as an INDEPENDENT MedicalDocument object, preserving
structured sections (INDICATION, FINDINGS, IMPRESSION, COMPARISON, MeSH).
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Generator, List, Optional
import sys

from VDB.config import OPENI_XML_DIR
from VDB.schema import MedicalDocument


def infer_condition_from_report(findings: str, impression: str, mesh_terms: List[str]) -> str:
    """Infer the primary medical condition tag from report text and MeSH tags."""
    combined = f"{findings} {impression} {' '.join(mesh_terms)}".lower()

    if "pneumothorax" in combined:
        return "Pneumothorax"
    if "effusion" in combined:
        return "Pleural_Effusion"
    if "pneumonia" in combined or "consolidation" in combined or "infiltrate" in combined:
        return "Pneumonia"
    if "edema" in combined or "congestion" in combined:
        return "Pulmonary_Edema"
    if "cardiomegaly" in combined or "enlarged heart" in combined:
        return "Cardiomegaly"
    if "copd" in combined or "emphysema" in combined:
        return "COPD"
    if "nodule" in combined or "mass" in combined or "granuloma" in combined:
        return "Pulmonary_Nodules"
    if "normal" in combined or "no acute" in combined or "unremarkable" in combined:
        return "Normal_CXR"
    return "Chest_Radiology"


def parse_openi_xml_file(xml_path: Path) -> Optional[MedicalDocument]:
    """Parse a single OpenI XML file into an independent MedicalDocument.

    Parameters
    ----------
    xml_path : Path
        Path to the OpenI XML file.

    Returns
    -------
    Optional[MedicalDocument]
        The parsed document, or None if file has no medical text.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Extract UID and Report ID
        uid_elem = root.find(".//uId")
        uid = uid_elem.get("id") if uid_elem is not None else xml_path.stem

        # Extract structured sections
        indication_elem = root.find(".//AbstractText[@Label='INDICATION']")
        findings_elem = root.find(".//AbstractText[@Label='FINDINGS']")
        impression_elem = root.find(".//AbstractText[@Label='IMPRESSION']")
        comparison_elem = root.find(".//AbstractText[@Label='COMPARISON']")

        indication = indication_elem.text.strip() if indication_elem is not None and indication_elem.text else ""
        findings = findings_elem.text.strip() if findings_elem is not None and findings_elem.text else ""
        impression = impression_elem.text.strip() if impression_elem is not None and impression_elem.text else ""
        comparison = comparison_elem.text.strip() if comparison_elem is not None and comparison_elem.text else ""

        # Extract MeSH terms
        mesh_terms = []
        for m in root.findall(".//MeSH/major"):
            if m.text and m.text.strip():
                mesh_terms.append(m.text.strip())

        # If there are no findings and no impression, skip empty template
        if not findings and not impression:
            return None

        sections = {}
        if indication:
            sections["INDICATION"] = indication
        if comparison:
            sections["COMPARISON"] = comparison
        if findings:
            sections["FINDINGS"] = findings
        if impression:
            sections["IMPRESSION"] = impression

        condition = infer_condition_from_report(findings, impression, mesh_terms)
        body_sys = "cardiovascular" if condition in ["Cardiomegaly", "Heart_Failure"] else "respiratory"

        raw_parts = [f"OpenI Report ID: {xml_path.name}", f"Condition Tag: {condition}"]
        for sec_name, sec_val in sections.items():
            raw_parts.append(f"{sec_name}:\n{sec_val}")
        if mesh_terms:
            raw_parts.append(f"MeSH Keywords: {', '.join(mesh_terms)}")
        raw_text = "\n\n".join(raw_parts)

        return MedicalDocument(
            doc_id=f"OpenI_{uid}",
            source_id="OpenI_IU_CXR",
            title=f"OpenI Chest X-ray Report ({uid})",
            condition=condition,
            body_system=body_sys,
            knowledge_domain="cases",
            source_type="radiology_report",
            audience="clinician",
            evidence_level="case_report",
            priority="P2",
            url="https://openi.nlm.nih.gov/",
            publication_year="2013",
            sections=sections,
            raw_text=raw_text,
            metadata={
                "report_id": xml_path.name,
                "uid": uid,
                "modality": "CXR",
                "mesh_terms": mesh_terms,
                "has_findings": bool(findings),
                "has_impression": bool(impression),
            },
        )
    except Exception as e:
        return None


def iter_openi_reports(
    xml_dir: Optional[Path] = None,
    max_reports: Optional[int] = None,
) -> Generator[MedicalDocument, None, None]:
    """Iterate through all OpenI XML files yielding independent MedicalDocuments."""
    if xml_dir is None:
        xml_dir = OPENI_XML_DIR

    if not xml_dir.is_dir():
        print(f"OpenI directory not found at {xml_dir}")
        return

    count = 0
    for xml_file in xml_dir.glob("*.xml"):
        doc = parse_openi_xml_file(xml_file)
        if doc is not None:
            yield doc
            count += 1
            if max_reports and count >= max_reports:
                break


def load_all_openi_reports(
    xml_dir: Optional[Path] = None,
    max_reports: Optional[int] = None,
) -> List[MedicalDocument]:
    """Load and return all OpenI reports as a list of independent documents."""
    docs = list(iter_openi_reports(xml_dir=xml_dir, max_reports=max_reports))
    print(f"Loaded {len(docs)} independent OpenI XML reports.")
    return docs
