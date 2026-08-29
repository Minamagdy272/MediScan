"""
Router Component (NVIDIA Nemotron-3-Nano-30B).
"""

from langchain_core.prompts import ChatPromptTemplate
from .schemas import RouterDecision
from .models import router_llm, invoke_json_model

router_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a routing component for MediScan.

Analyze the user query and provide routing hints.

Allowed query types:
- direct: factual questions
- guideline: management or recommendations
- patient: educational or simple explanation
- comparison: follow-up or change comparison
- cases: case matching
- general: other/general questions

Allowed complexity:
- simple
- moderate
- complex

Allowed retrieval modes:
- BM25: exact medical terms, acronyms, precise terminology
- HYBRID: semantic or general phrasing
- HYBRID_RERANKED: complex multi-case or comparison queries
"""),
    ("human", "Analyze this query:\n{query}")
])


def route_query(query: str) -> RouterDecision:
    """Route user query to appropriate retrieval mode and intent classification."""
    try:
        messages = router_prompt.format_messages(query=query)
        decision = invoke_json_model(
            llm=router_llm,
            prompt=messages,
            schema=RouterDecision,
            temperature=0.0
        )
        return decision
    except Exception as e:
        print(f"⚠ Router failed, using deterministic fallback: {e}")
        return RouterDecision(
            query_type="direct",
            language="en",
            complexity="moderate",
            suggested_retrieval_mode="HYBRID"
        )
