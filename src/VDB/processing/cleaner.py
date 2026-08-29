"""
cleaner.py - Medical text normalization and boilerplate removal.
"""

import re

UNICODE_REPLACEMENTS = {
    "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2015": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u00a0": " ", "\u200b": "", "\ufeff": "", "\t": " ",
}

BOILERPLATE_PATTERNS = [
    r"(?i)^.*(cookie policy|accept all cookies|privacy policy|terms of use|all rights reserved).*$",
    r"(?i)^.*(subscribe to our newsletter|sign up for free|follow us on|share this article).*$",
    r"(?i)^.*(skip to main content|back to top|accessibility statement|download pdf version).*$",
    r"(?i)^.*(related topics|you might also like|popular articles|read next).*$",
    r"(?i)^.*(an official website of the united states government|here's how you know).*$",
    r"(?i)^.*(site map|contact us|about us|careers|press room).*$",
    r"(?i)^.*(advertisement|sponsored content|click here to).*$",
]


def clean_medical_text(raw_text: str) -> str:
    """Clean raw medical text while preserving clinical indicators and section semantics."""
    if not raw_text:
        return ""

    text = raw_text

    # Normalize unicode
    for old, new in UNICODE_REPLACEMENTS.items():
        text = text.replace(old, new)

    # Remove boilerplate lines
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.MULTILINE)

    # Clean decorative horizontal separators
    text = re.sub(r"[-=_~*]{4,}", "\n", text)

    # Remove standalone links
    text = re.sub(r"^\s*https?://\S+\s*$", "", text, flags=re.MULTILINE)

    # Clean multiple spaces & excessive newlines
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    return text.strip()
