"""
loader.py - Load raw medical documents from URLs, PDFs, and XML files.

Contains the original data-loading logic that was in the notebook:
  - Radiology URLs
  - OpenI XML extraction
  - Cardiovascular URLs
  - Respiratory URLs
  - Patient Care URLs & PDFs
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_urls(urls: dict[str, str], output_dir: Path) -> list[str]:
    """Download web pages and save as .txt files.

    Parameters
    ----------
    urls : dict
        Mapping of `{name: url}`.
    output_dir : Path
        Directory to save text files.

    Returns
    -------
    list[str]
        List of saved file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for name, url in urls.items():
        loader = WebBaseLoader(url)
        docs = loader.load()
        text = "\n\n".join(doc.page_content for doc in docs)
        file_path = output_dir / f"{name}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved: {file_path}")
        saved.append(str(file_path))
    return saved


def load_pdfs(pdfs: dict[str, str], output_dir: Path) -> list[str]:
    """Extract text from PDFs and save as .txt files.

    Parameters
    ----------
    pdfs : dict
        Mapping of `{name: pdf_path}`.
    output_dir : Path
        Directory to save text files.

    Returns
    -------
    list[str]
        List of saved file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for name, pdf_path in pdfs.items():
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        text = "\n\n".join(doc.page_content for doc in docs)
        file_path = output_dir / f"{name}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved: {file_path}")
        saved.append(str(file_path))
    return saved


def extract_openi_reports(xml_dir: Path, output_file: Path) -> dict:
    """Extract radiology reports from OpenI XML files.

    Parameters
    ----------
    xml_dir : Path
        Directory containing the XML files.
    output_file : Path
        Path to save the combined reports text file.

    Returns
    -------
    dict
        Summary with `extracted` count and `failed` list.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    reports = []
    failed_files = []

    for xml_file in xml_dir.iterdir():
        if not xml_file.is_file():
            continue
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            indication = root.find(".//AbstractText[@Label='INDICATION']")
            findings = root.find(".//AbstractText[@Label='FINDINGS']")
            impression = root.find(".//AbstractText[@Label='IMPRESSION']")

            indication_text = (
                indication.text.strip()
                if indication is not None and indication.text
                else ""
            )
            findings_text = (
                findings.text.strip()
                if findings is not None and findings.text
                else ""
            )
            impression_text = (
                impression.text.strip()
                if impression is not None and impression.text
                else ""
            )

            if findings_text or impression_text:
                report = f"""Source: OpenI / Indiana University Chest X-ray Collection
Report ID: {xml_file.name}

Indication:
{indication_text}

Findings:
{findings_text}

Impression:
{impression_text}

----------------------------------------"""
                reports.append(report.strip())

        except ET.ParseError:
            failed_files.append(xml_file.name)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n\n".join(reports))

    print(f"Successfully extracted: {len(reports)} reports")
    print(f"Failed files: {len(failed_files)}")
    print(f"Saved to: {output_file}")

    return {"extracted": len(reports), "failed": failed_files}


def load_all_raw_data():
    """Run ALL the original notebook loading steps."""
    root = get_project_root()
    data = root / "data"

    # ---- Radiology URLs ----
    print("\n=== Loading Radiology URLs ===")
    load_urls(
        {
            "basic_interpretation": "https://radiologyassistant.nl/chest/chest-x-ray/basic-interpretation",
            "lung_disease": "https://radiologyassistant.nl/chest/chest-x-ray/lung-disease",
            "cardiovascular_cxr": "https://www.ncbi.nlm.nih.gov/books/NBK355/?report=printable",
        },
        data / "radiology",
    )

    # ---- OpenI XML reports ----
    xml_dir = data / "radiology" / "ecgen-radiology"
    if xml_dir.is_dir():
        print("\n=== Extracting OpenI Reports ===")
        extract_openi_reports(xml_dir, data / "radiology" / "openi_reports.txt")
    else:
        print(f"\nSkipping OpenI extraction: {xml_dir} not found")

    # ---- Cardiovascular URLs ----
    print("\n=== Loading Cardiovascular URLs ===")
    load_urls(
        {
            "Heart_Failure": "https://www.ncbi.nlm.nih.gov/books/NBK430873/?report=printable",
            "Cardiomegaly": "https://www.ncbi.nlm.nih.gov/books/NBK542296/?report=printable",
            "Pleural_Effusion": "https://www.ncbi.nlm.nih.gov/books/NBK448189/?report=printable",
            "Pulmonary_Edema": "https://www.ncbi.nlm.nih.gov/books/NBK554557/?report=printable",
            "Pericardial_Effusion": "https://www.ncbi.nlm.nih.gov/books/NBK431089/?report=printable",
        },
        data / "cardiovascular",
    )

    # ---- Respiratory URLs ----
    print("\n=== Loading Respiratory URLs ===")
    load_urls(
        {
            "Pneumonia": "https://www.ncbi.nlm.nih.gov/books/NBK279396/?report=printable",
            "Pneumothorax": "https://en.wikipedia.org/wiki/Pneumothorax",
            "COPD": "https://medlineplus.gov/copd.html",
            "Pulmonary_Edema": "https://www.mayoclinic.org/diseases-conditions/pulmonary-edema/symptoms-causes/syc-20377009",
            "Consolidation": "https://radiologyassistant.nl/chest/chest-x-ray/lung-disease",
        },
        data / "respiratory",
    )

    # ---- Patient Care URLs ----
    print("\n=== Loading Patient Care URLs ===")
    load_urls(
        {
            "MedlinePlus-HeartFailure": "https://medlineplus.gov/heartfailure.html",
            "COPD": "https://medlineplus.gov/copd.html",
            "pneuomonia": "https://medlineplus.gov/pneumonia.html",
            "Heart_Failure_Diet": "https://my.clevelandclinic.org/departments/heart/patient-education/recovery-care/heart-failure/diet",
        },
        data / "patient_care",
    )

    print("\nAll raw data loading complete!")


if __name__ == "__main__":
    load_all_raw_data()
