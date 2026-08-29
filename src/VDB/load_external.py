"""
load_external.py - Load external medical sources from the source registry.

Reads data/registry/source_registry.csv and downloads/extracts each source
using the specified retrieval method (html_loader, pdf_loader, direct_download).
"""

import csv
import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader

# Ensure console supports utf-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_project_root() -> Path:
    """Return the MediScan project root (two levels up from this file)."""
    return Path(__file__).resolve().parent.parent.parent


def fetch_html_text(url: str) -> str:
    """Fallback HTML loader with standard browser headers."""
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.extract()
    return soup.get_text(separator="\n", strip=True)


def load_external_sources(
    registry_path: Path | None = None,
) -> dict:
    """Load external sources defined in the source registry CSV.

    Parameters
    ----------
    registry_path : Path, optional
        Path to `source_registry.csv`. Defaults to
        `<project_root>/data/registry/source_registry.csv`.

    Returns
    -------
    dict
        Summary with keys `loaded`, `failed`, `skipped`.
    """
    if registry_path is None:
        registry_path = get_project_root() / "data" / "registry" / "source_registry.csv"

    summary = {"loaded": 0, "failed": 0, "skipped": 0, "errors": []}

    if not registry_path.is_file():
        print(f"Registry file not found at {registry_path}. Skipping.")
        return summary

    print(f"Reading registry: {registry_path}\n")

    with registry_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source_id = row["source_id"].strip()
            save_dir = get_project_root() / row["suggested_save_directory"].strip()
            save_dir.mkdir(parents=True, exist_ok=True)
            suggested_name = row["suggested_filename"].strip()
            file_path = save_dir / suggested_name
            txt_path = file_path.with_suffix(".txt")
            method = row["retrieval_method"].strip()
            url = (row.get("full_text_url") or row.get("url") or "").strip()

            if not url or url.startswith("requires_credential") or method == "requires_credential":
                print(f"  [SKIP] {source_id}: Credentials/registration required or empty URL")
                summary["skipped"] += 1
                continue

            print(f"  [DOWNLOADING] {source_id} via {method}: {url}")

            try:
                if method == "direct_download":
                    resp = requests.get(url, headers=DEFAULT_HEADERS, stream=True, timeout=60)
                    resp.raise_for_status()
                    with open(file_path, "wb") as out_f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            out_f.write(chunk)

                    if file_path.suffix.lower() == ".pdf":
                        try:
                            loader = PyPDFLoader(str(file_path))
                            docs = loader.load()
                            text = "\n\n".join(d.page_content for d in docs)
                            txt_path.write_text(text, encoding="utf-8")
                        except Exception as pdf_err:
                            txt_path.write_text(f"PDF Downloaded: {file_path.name}\nError extracting text: {pdf_err}", encoding="utf-8")

                elif method == "html_loader":
                    try:
                        loader = WebBaseLoader(url, header_template=DEFAULT_HEADERS)
                        docs = loader.load()
                        text = "\n\n".join(doc.page_content for doc in docs)
                    except Exception:
                        text = fetch_html_text(url)
                    txt_path.write_text(text, encoding="utf-8")

                elif method == "pdf_loader":
                    pdf_cache = save_dir / (txt_path.stem + ".pdf")
                    resp = requests.get(url, headers=DEFAULT_HEADERS, stream=True, timeout=60)
                    resp.raise_for_status()
                    with open(pdf_cache, "wb") as out_f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            out_f.write(chunk)
                    try:
                        loader = PyPDFLoader(str(pdf_cache))
                        docs = loader.load()
                        text = "\n\n".join(doc.page_content for doc in docs)
                        txt_path.write_text(text, encoding="utf-8")
                    except Exception as pdf_err:
                        txt_path.write_text(f"PDF Downloaded from {url}\nExtraction note: {pdf_err}", encoding="utf-8")

                else:
                    print(f"  [SKIP] {source_id}: unknown method '{method}'")
                    summary["skipped"] += 1
                    continue

                print(f"  [OK]   {source_id} -> {txt_path.name}")
                summary["loaded"] += 1

            except Exception as e:
                print(f"  [FAIL] {source_id}: {e}")
                summary["failed"] += 1
                summary["errors"].append((source_id, str(e)))

    print("\n=============================================")
    print(f"Done: {summary['loaded']} loaded, {summary['failed']} failed, {summary['skipped']} skipped")
    print("=============================================")
    return summary


if __name__ == "__main__":
    load_external_sources()
