"""
run_vdb.py - Main entry point for the MediScan VDB pipeline.

Orchestrates the full workflow that was originally in building_vdb.ipynb:
  1. (Optional) Load external sources from source_registry.csv
  2. (Optional) Load raw data from URLs / PDFs / XML
  3. Load cleaned documents
  4. Chunk documents
  5. Initialize embeddings
  6. Build ChromaDB vector store
  7. Run demo queries

Usage:
    python -m VDB.run_vdb              # from src/ directory
    python src/VDB/run_vdb.py          # from project root
"""

import argparse
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def main(
    skip_raw_loading: bool = True,
    skip_external: bool = True,
    skip_cleaning: bool = True,
    skip_queries: bool = False,
):
    """Run the complete VDB building pipeline.

    Parameters
    ----------
    skip_raw_loading : bool
        If True, skip downloading raw data from URLs (assumes data
        already exists in data/ folders).
    skip_external : bool
        If True, skip loading external sources from source_registry.csv.
    skip_queries : bool
        If True, skip demo similarity queries at the end.
    """
    print("=" * 60)
    print("  MediScan VDB Pipeline")
    print("=" * 60)

    # ---- Step 1: Load external sources ----
    if not skip_external:
        print("\n[1/6] Loading external sources from registry...")
        from VDB.load_external import load_external_sources
        load_external_sources()
    else:
        print("\n[1/6] Skipping external source loading")

    # ---- Step 2: Load raw data ----
    if not skip_raw_loading:
        print("\n[2/6] Loading raw data from URLs/PDFs/XML...")
        from VDB.loader import load_all_raw_data
        load_all_raw_data()
    else:
        print("\n[2/6] Skipping raw data loading (using existing data)")

    # ---- Step 2.5: Clean external sources ----
    if not skip_cleaning:
        print("\n[3/7] Cleaning raw external sources...")
        from VDB.cleaning import clean_all_external_sources
        clean_all_external_sources()
    else:
        print("\n[3/7] Skipping cleaning (using existing cleaned files)")

    # ---- Step 3: Load cleaned documents ----
    print("\n[4/7] Loading cleaned documents...")
    from VDB.chunking import load_cleaned_documents, chunk_documents, print_chunk_stats

    docs = load_cleaned_documents()

    # ---- Step 4: Chunk documents ----
    print("\n[5/7] Chunking documents...")
    chunks = chunk_documents(docs)
    print_chunk_stats(chunks)

    # ---- Step 5: Initialize embeddings ----
    print("\n[6/7] Initializing embedding model...")
    from VDB.embedding import get_embeddings, test_embedding

    embeddings = get_embeddings()
    test_embedding(embeddings)

    # ---- Step 6: Build vector store ----
    print("\n[7/7] Building ChromaDB vector store...")
    from VDB.vectorstore import create_vectorstore

    vectorstore = create_vectorstore(chunks, embeddings)

    # ---- Demo queries ----
    if not skip_queries:
        print("\n" + "=" * 60)
        print("  Running Demo Queries")
        print("=" * 60)
        from VDB.query import run_demo_queries
        run_demo_queries(vectorstore)

    print("\n" + "=" * 60)
    print("  Pipeline Complete!")
    print("=" * 60)

    return vectorstore


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MediScan VDB Pipeline")
    parser.add_argument(
        "--load-raw",
        action="store_true",
        help="Download raw data from URLs/PDFs/XML (usually already done)",
    )
    parser.add_argument(
        "--load-external",
        action="store_true",
        help="Load external sources from source_registry.csv",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Run text cleaning on data/external_sources/ before indexing",
    )
    parser.add_argument(
        "--no-queries",
        action="store_true",
        help="Skip demo similarity queries",
    )
    args = parser.parse_args()

    main(
        skip_raw_loading=not args.load_raw,
        skip_external=not args.load_external,
        skip_cleaning=not args.clean,
        skip_queries=args.no_queries,
    )

