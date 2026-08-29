"""
Agent Planner Component (GLM-5.3-Flash via OpenRouter) & Deterministic Plan Validation.
"""

from typing import List, Set
from langchain_core.prompts import ChatPromptTemplate
from .schemas import (
    AgentPlan,
    PlanIntent,
    PlanRetrievalMode,
    ExtractedMedicalInfo,
    RouterDecision
)
from .models import planner_llm

planner_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are the Agent Planner for the MediScan medical RAG system.
Your SOLE responsibility is to output a structured AgentPlan.
You do NOT execute tools, retrieve documents, or generate the final medical report.

Guidelines for Planning:
1. Understand the user query, clinical extracted state, and conversation history.
2. Select intent: EXPLAIN, INTERPRET, COMPARE, GUIDELINE, EDUCATIONAL, FOLLOW_UP, GENERAL_MEDICAL.
3. Select retrieval mode:
   - BM25: Precise medical acronyms, exact radiological signs, named criteria (e.g., 'Kerley B', 'Light criteria', 'pH < 7.2').
   - HYBRID: Semantic phrasing, general symptoms, paraphrased questions.
   - HYBRID_RERANKED: Complex multi-condition comparisons, nuanced differential diagnoses where passage ranking order is critical.
4. Formulate 1 to 3 concise, highly focused retrieval queries.
5. Choose allowed tools from: ['MedicalRAGTool', 'ClinicalGuidelineTool', 'SimilarCaseTool', 'PatientHistoryTool', 'ReportGeneratorTool'].
"""),
    ("human", """User Message: {user_message}
Extracted Findings: {extracted_summary}
Router Hint: {router_hint}
Conversation History: {chat_history}

Create a structured AgentPlan:""")
])

structured_planner = planner_llm.with_structured_output(AgentPlan)
planning_chain = planner_prompt | structured_planner

ALLOWED_TOOLS: Set[str] = {
    "MedicalRAGTool",
    "ClinicalGuidelineTool",
    "PatientHistoryTool",
    "SimilarCaseTool",
    "RiskAssessmentTool",
    "ReportGeneratorTool"
}


def generate_agent_plan(
    user_message: str,
    extracted_info: ExtractedMedicalInfo,
    router_hint: RouterDecision,
    history_str: str
) -> AgentPlan:
    """Generate structured AgentPlan for retrieval and synthesis."""
    try:
        extracted_summary = (
            f"Imaging: {extracted_info.imaging_findings} | "
            f"Positive: {extracted_info.positive_findings} | "
            f"Negative: {extracted_info.negative_findings}"
        )
        return planning_chain.invoke({
            "user_message": user_message,
            "extracted_summary": extracted_summary,
            "router_hint": f"Type={router_hint.query_type}, Mode={router_hint.suggested_retrieval_mode}",
            "chat_history": history_str
        })
    except Exception:
        mode_val = (
            router_hint.suggested_retrieval_mode
            if router_hint.suggested_retrieval_mode in ["BM25", "HYBRID", "HYBRID_RERANKED"]
            else "HYBRID"
        )
        intent_val = (
            PlanIntent.COMPARE
            if "follow" in user_message.lower() or "previous" in user_message.lower()
            else PlanIntent.INTERPRET
        )
        return AgentPlan(
            intent=intent_val,
            retrieval_mode=PlanRetrievalMode(mode_val),
            queries=[user_message[:120]],
            tools=["MedicalRAGTool"],
            needs_evidence=True,
            reason="Router-guided fallback plan."
        )


def validate_agent_plan(plan: AgentPlan) -> AgentPlan:
    """Validates and sanitizes the AgentPlan before execution."""
    # 1. Validate tools
    valid_tools = [t for t in plan.tools if t in ALLOWED_TOOLS]
    if not valid_tools:
        valid_tools = ["MedicalRAGTool"]
    plan.tools = valid_tools

    # 2. Ensure queries exist if evidence is needed
    if plan.needs_evidence and not plan.queries:
        plan.queries = ["chest x-ray clinical findings"]

    # 3. Sanitize query count (max 4 queries)
    plan.queries = [q.strip() for q in plan.queries if q.strip()][:4]
    return plan
