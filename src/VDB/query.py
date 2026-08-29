"""
query.py - Run similarity searches against the MediScan vector store.

Provides helper functions that mirror the query cells at the end of the
original notebook.
"""

from langchain_chroma import Chroma


def search(
    vectorstore: Chroma,
    query: str,
    k: int = 5,
    verbose: bool = True,
) -> list:
    """Run a similarity search and optionally print results.

    Parameters
    ----------
    vectorstore : Chroma
        The vector store to query.
    query : str
        Natural-language query.
    k : int
        Number of results to return.
    verbose : bool
        If True, print formatted results.

    Returns
    -------
    list
        Matching LangChain Document objects.
    """
    results = vectorstore.similarity_search(query, k=k)

    if verbose:
        print(f"\n{'=' * 80}")
        print(f"QUERY: {query}")
        print("=" * 80)
        for i, doc in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Source: {doc.metadata.get('source')}")
            print(doc.page_content[:800])

    return results


def run_demo_queries(vectorstore: Chroma) -> None:
    """Run the same demo queries from the original notebook."""
    queries = [
        "What chest X-ray findings may indicate pneumonia?",
        "What chest X-ray findings may indicate pneumothorax?",
        "What lifestyle recommendations are relevant for a patient with heart failure?",
    ]
    for q in queries:
        search(vectorstore, q, k=3)


if __name__ == "__main__":
    # Quick standalone test - requires existing DB
    from embedding import get_embeddings
    from vectorstore import load_vectorstore

    embeddings = get_embeddings()
    vs = load_vectorstore(embeddings)
    run_demo_queries(vs)
