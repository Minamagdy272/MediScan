"""
cleaning.py - Clean and preprocess raw medical documents for vector embedding.

Cleans text from data/external_sources/ and raw sources, removing web artifacts,
boilerplate, navigation menus, and excess whitespace, then saves clean, high-signal
documents into data/cleaned/.
"""

import re
import sys
from pathlib import Path

# Ensure console supports utf-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def get_project_root() -> Path:
    """Return the MediScan project root."""
    return Path(__file__).resolve().parent.parent.parent


def clean_text(raw_text: str) -> str:
    """Clean and normalize medical document text.

    - Replaces non-standard unicode characters (hyphens, smart quotes, nbsp)
    - Strips website navigation headers, footers, cookie banners, social links
    - Removes citation marker noise and repeated symbols
    - Normalizes paragraph spacing and line breaks
    """
    if not raw_text:
        return ""

    text = raw_text

    # 1. Normalize unicode characters
    unicode_replacements = {
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
        "\u200b": "",
        "\ufeff": "",
        "\t": " ",
    }
    for old, new in unicode_replacements.items():
        text = text.replace(old, new)

    # 2. Strip common web boilerplate lines & patterns
    boilerplate_patterns = [
        r"(?i)^.*(cookie policy|accept all cookies|privacy policy|terms of use|all rights reserved).*$",
        r"(?i)^.*(subscribe to our newsletter|sign up for free|follow us on|share this article).*$",
        r"(?i)^.*(skip to main content|back to top|accessibility statement|download pdf version).*$",
        r"(?i)^.*(related topics|you might also like|popular articles|read next).*$",
        r"(?i)^.*(an official website of the united states government|here's how you know).*$",
        r"(?i)^.*(site map|contact us|about us|careers|press room).*$",
        r"(?i)^.*(advertisement|sponsored content|click here to).*$",
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text, flags=re.MULTILINE)

    # 3. Clean repetitive separator lines / underscores / dashes / equals
    text = re.sub(r"[-=_~*]{4,}", "\n", text)

    # 4. Remove standalone URL lines that don't add semantic value
    text = re.sub(r"^\s*https?://\S+\s*$", "", text, flags=re.MULTILINE)

    # 5. Fix multiple consecutive spaces and empty lines
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    # 6. Trim leading/trailing whitespace
    return text.strip()


def clean_all_external_sources(
    source_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict:
    """Read all .txt files from external_sources and write cleaned files to data/cleaned/external_sources/.

    Parameters
    ----------
    source_dir : Path, optional
        Source directory containing raw external files. Defaults to data/external_sources/.
    output_dir : Path, optional
        Target directory for cleaned files. Defaults to data/cleaned/external_sources/.

    Returns
    -------
    dict
        Summary of cleaned files count and total character savings.
    """
    root = get_project_root()
    if source_dir is None:
        source_dir = root / "data" / "external_sources"
    if output_dir is None:
        output_dir = root / "data" / "cleaned" / "external_sources"

    summary = {"total_files": 0, "cleaned_files": 0, "bytes_before": 0, "bytes_after": 0}

    if not source_dir.is_dir():
        print(f"Source directory not found: {source_dir}")
        return summary

    txt_files = list(source_dir.rglob("*.txt"))
    summary["total_files"] = len(txt_files)

    print(f"Starting cleaning for {len(txt_files)} external text documents...\n")

    for txt_file in txt_files:
        try:
            rel_path = txt_file.relative_to(source_dir)
            target_path = output_dir / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)

            raw_content = txt_file.read_text(encoding="utf-8", errors="ignore")
            cleaned_content = clean_text(raw_content)

            # Skip empty or nearly empty files
            if len(cleaned_content.strip()) < 50:
                print(f"  [SKIP] {rel_path} (too short or empty after cleaning)")
                continue

            target_path.write_text(cleaned_content, encoding="utf-8")

            summary["cleaned_files"] += 1
            summary["bytes_before"] += len(raw_content)
            summary["bytes_after"] += len(cleaned_content)

            print(f"  [CLEANED] {rel_path} ({len(raw_content)} -> {len(cleaned_content)} chars)")

        except Exception as e:
            print(f"  [ERROR] {txt_file.name}: {e}")

    savings = summary["bytes_before"] - summary["bytes_after"]
    print("\n=============================================")
    print(f"Cleaned {summary['cleaned_files']} / {summary['total_files']} files")
    print(f"Total size before: {summary['bytes_before']:,} characters")
    print(f"Total size after:  {summary['bytes_after']:,} characters")
    print(f"Boilerplate reduction: {savings:,} characters ({(savings / (summary['bytes_before'] or 1) * 100):.1f}%)")
    print(f"Cleaned files saved to: {output_dir}")
    print("=============================================")

    return summary


if __name__ == "__main__":
    clean_all_external_sources()
