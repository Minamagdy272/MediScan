"""
MediScan Pipeline Schemas and Data Models.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class ExtractedMedicalInfo(BaseModel):
    symptoms: List[str] = Field(default_factory=list, description="Symptoms explicitly mentioned in input.")
    imaging_findings: List[str] = Field(default_factory=list, description="Imaging findings explicitly mentioned.")
    positive_findings: List[str] = Field(default_factory=list, description="Abnormal or positive findings explicitly present.")
    negative_findings: List[str] = Field(default_factory=list, description="Explicit negative findings (e.g., no pneumothorax).")
    patient_information: List[str] = Field(default_factory=list, description="Patient demographics explicitly provided.")
    missing_information: List[str] = Field(default_factory=list, description="Important clinical information not provided.")


class RouterDecision(BaseModel):
    query_type: str = Field(
        description="direct, guideline, patient, comparison, cases, or general"
    )
    language: str = Field(
        default="en",
        description="Detected language (en, ar)"
    )
    complexity: str = Field(
        description="simple, moderate, complex"
    )
    suggested_retrieval_mode: str = Field(
        description="BM25, HYBRID, HYBRID_RERANKED"
    )


class PlanIntent(str, Enum):
    EXPLAIN = "EXPLAIN"
    INTERPRET = "INTERPRET"
    COMPARE = "COMPARE"
    GUIDELINE = "GUIDELINE"
    EDUCATIONAL = "EDUCATIONAL"
    FOLLOW_UP = "FOLLOW_UP"
    GENERAL_MEDICAL = "GENERAL_MEDICAL"


class PlanRetrievalMode(str, Enum):
    BM25 = "BM25"
    HYBRID = "HYBRID"
    HYBRID_RERANKED = "HYBRID_RERANKED"


class AgentPlan(BaseModel):
    intent: PlanIntent = Field(description="Primary clinical intent of the user request.")
    retrieval_mode: PlanRetrievalMode = Field(description="Chosen retrieval strategy based on terminology and complexity.")
    queries: List[str] = Field(description="Focused search queries to retrieve relevant medical evidence.")
    tools: List[str] = Field(default_factory=lambda: ["MedicalRAGTool"], description="Allowed tools to invoke.")
    needs_evidence: bool = Field(default=True, description="Whether knowledge retrieval is required.")
    needs_guideline: bool = Field(default=False, description="Whether guideline-specific sources are required.")
    needs_history: bool = Field(default=False, description="Whether comparison with past findings is requested.")
    response_type: str = Field(default="report", description="report, educational_summary, comparison_table, or direct_answer")
    reason: str = Field(description="Clear architectural rationale for this plan.")


@dataclass
class Tier0Result:
    is_valid: bool
    errors: List[str] = field(default_factory=list)


class EvaluationVerdict(BaseModel):
    groundedness: float = Field(description="Score 0.0-1.0: How well draft is supported by evidence.")
    citation_validity: float = Field(description="Score 0.0-1.0: Accuracy of citation placement.")
    answer_relevance: float = Field(description="Score 0.0-1.0: Relevance to the user's question.")
    context_sufficiency: float = Field(description="Score 0.0-1.0: Sufficiency of evidence for the draft.")
    safety_compliance: float = Field(description="Score 0.0-1.0: Adherence to medical safety rules.")
    blocking_issues: List[str] = Field(default_factory=list, description="Critical issues detected.")
    missing_evidence_query: Optional[str] = Field(default=None, description="Suggested query if evidence is missing.")
    suggested_action: str = Field(description="ACCEPT, REGENERATE, RE_RETRIEVE, ESCALATE")


class PolicyAction(str, Enum):
    ACCEPT = "ACCEPT"
    REGENERATE = "REGENERATE"
    RE_RETRIEVE = "RE_RETRIEVE"
    ESCALATE = "ESCALATE"


class EvidencePayload(BaseModel):
    evidence_id: str
    chunk_id: str
    source_id: str
    source_title: str
    source_type: str
    content: str
    score: float
    rank: int


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    generate_pdf: bool = False
    send_email: bool = False
    email_recipient: Optional[str] = None


class ChatResponsePayload(BaseModel):
    user_message: str
    final_answer: str
    session_id: str
    plan: Optional[AgentPlan] = None
    final_action: str
    attempts_made: int
    evidence_used: List[EvidencePayload] = Field(default_factory=list)
    pdf_path: Optional[str] = None
    pdf_download_url: Optional[str] = None
    email_sent: bool = False
    email_status: Optional[str] = None
    trace: Dict[str, Any] = Field(default_factory=dict)


class EmailReportRequest(BaseModel):
    session_id: str
    recipient_email: str
    pdf_filename: Optional[str] = None


class GeneratePdfRequest(BaseModel):
    session_id: str
    report_text: Optional[str] = None
