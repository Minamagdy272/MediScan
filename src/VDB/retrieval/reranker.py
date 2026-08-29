"""
reranker.py - NVIDIA NIM Reranker / Cross-Encoder integration.
"""

import requests
from typing import List, Optional
from VDB.config import NVIDIA_API_KEY, NVIDIA_BASE_URL, RERANKER_MODEL
from VDB.schema import EvidenceRecord


class NvidiaReranker:
    """Reranks candidate evidence chunks using NVIDIA NIM Reranker endpoint."""

    def __init__(
        self,
        model: str = RERANKER_MODEL,
        api_key: str = NVIDIA_API_KEY,
        base_url: str = NVIDIA_BASE_URL,
    ):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") + "/ranking"

    def rerank(
        self,
        query: str,
        candidates: List[EvidenceRecord],
        top_k: int = 5,
    ) -> List[EvidenceRecord]:
        """Rerank candidates using cross-attention model scoring."""
        if not candidates or not self.api_key:
            return candidates[:top_k]

        passages = [{"text": c.content} for c in candidates]
        payload = {
            "model": self.model,
            "query": {"text": query},
            "passages": passages,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            resp = requests.post(self.base_url, json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                rankings = data.get("rankings", [])
                
                reranked_results: List[EvidenceRecord] = []
                for item in rankings[:top_k]:
                    idx = item.get("index", 0)
                    logit = item.get("logit", 0.0)
                    orig = candidates[idx]
                    orig.rerank_score = float(logit)
                    orig.retrieval_score = float(logit)
                    orig.rank = len(reranked_results) + 1
                    orig.evidence_id = f"EV-{orig.rank:03d}"
                    reranked_results.append(orig)
                return reranked_results
            else:
                return candidates[:top_k]
        except Exception:
            return candidates[:top_k]
