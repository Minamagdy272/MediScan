"""
registry.py - Source registry reader, validator, and entry query utility.
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional

from VDB.config import SOURCE_REGISTRY_CSV


def load_source_registry(registry_path: Optional[Path] = None) -> List[Dict[str, str]]:
    """Load and return all validated records from source_registry.csv."""
    if registry_path is None:
        registry_path = SOURCE_REGISTRY_CSV

    if not registry_path.is_file():
        print(f"Registry file not found at {registry_path}")
        return []

    records = []
    with open(registry_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("source_id"):
                records.append({k.strip(): (v.strip() if v else "") for k, v in row.items() if k})

    return records


def get_sources_by_condition(condition: str, registry_path: Optional[Path] = None) -> List[Dict[str, str]]:
    """Get all registered sources matching a condition name."""
    records = load_source_registry(registry_path)
    return [r for r in records if r.get("condition", "").lower() == condition.lower()]


def get_sources_by_domain(domain: str, registry_path: Optional[Path] = None) -> List[Dict[str, str]]:
    """Get all registered sources matching a knowledge domain."""
    records = load_source_registry(registry_path)
    return [r for r in records if r.get("knowledge_domain", "").lower() == domain.lower()]


def get_source_by_id(source_id: str, registry_path: Optional[Path] = None) -> Optional[Dict[str, str]]:
    """Look up a single source entry by its source_id (e.g., 'SRC001')."""
    records = load_source_registry(registry_path)
    for r in records:
        if r.get("source_id", "").upper() == source_id.upper():
            return r
    return None
