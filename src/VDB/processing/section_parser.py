"""
section_parser.py - Detects and extracts clinical sections from unstructured medical text.
"""

import re
from typing import Dict, List, Tuple

CLINICAL_SECTION_PATTERNS = [
    r"^(INDICATION|CLINICAL INDICATION|REASON FOR EXAM):?",
    r"^(FINDINGS|RADIOLOGIC FINDINGS|IMAGING FINDINGS|OBSERVATIONS):?",
    r"^(IMPRESSION|CONCLUSION|SUMMARY|RECOMMENDATION|RECOMMENDATIONS):?",
    r"^(COMPARISON|TECHNIQUE|PROCEDURE):?",
    r"^(DIAGNOSIS|DIAGNOSTIC CRITERIA|DIFFERENTIAL DIAGNOSIS):?",
    r"^(PATHOPHYSIOLOGY|ETIOLOGY|EPIDEMIOLOGY):?",
    r"^(TREATMENT|MANAGEMENT|THERAPY|MEDICATION):?",
    r"^(CASE PRESENTATION|HISTORY OF PRESENT ILLNESS|PHYSICAL EXAMINATION):?",
    r"^(OVERVIEW|INTRODUCTION|BACKGROUND):?",
    r"^(OUTCOME|FOLLOW-UP|COMPLICATIONS):?",
]


def split_text_into_sections(text: str) -> Dict[str, str]:
    """Split medical text into structured sections based on recognized headers.

    If no section headers are identified, returns {'MAIN': text}.
    """
    if not text:
        return {}

    lines = text.split("\n")
    sections: Dict[str, List[str]] = {}
    current_sec = "MAIN"
    sections[current_sec] = []

    combined_regex = re.compile("|".join(f"({p})" for p in CLINICAL_SECTION_PATTERNS), flags=re.IGNORECASE)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        match = combined_regex.match(stripped)
        if match and len(stripped.split()) <= 6:
            # New section header detected
            header_name = re.sub(r"[:\s]+$", "", stripped).upper().replace(" ", "_")
            current_sec = header_name
            if current_sec not in sections:
                sections[current_sec] = []
        else:
            sections[current_sec].append(line)

    result = {}
    for sec_name, sec_lines in sections.items():
        sec_text = "\n".join(sec_lines).strip()
        if sec_text:
            result[sec_name] = sec_text

    return result if result else {"MAIN": text.strip()}
