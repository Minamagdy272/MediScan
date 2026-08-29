"""
MediScan Pipeline Coordinator & Deterministic Execution Loop.
Executes the exact multi-tier agentic RAG and recovery loop.
Supports both synchronous calls and SSE async generator streaming.
"""

import time
from typing import Optional, List, Dict, Any, AsyncGenerator

from VDB.schema import EvidenceRecord
from .schemas import (
    PolicyAction,
    ChatResponsePayload,
    EvidencePayload,
    AgentPlan,
    ExtractedMedicalInfo,
    RouterDecision,
    Tier0Result,
    EvaluationVerdict
)
from .session import session_store
from .extraction import extract_clinical_info
from .router import route_query
from .planner import generate_agent_plan, validate_agent_plan
from .retriever import execute_retrieval, select_and_map_citations
from .generator import generate_medical_response
from .validation import run_tier0_validation, evaluate_draft
from .policy import decide_policy_action
from .pdf_service import generate_pdf_report
from .email_service import send_report_email


def _convert_evidence_records(evidence: List[EvidenceRecord]) -> List[EvidencePayload]:
    """Helper to convert EvidenceRecord to serialized EvidencePayload."""
    payloads = []
    for rec in evidence:
        payloads.append(
            EvidencePayload(
                evidence_id=rec.evidence_id or "EV-000",
                chunk_id=rec.chunk_id,
                source_id=rec.source_id,
                source_title=rec.source_title,
                source_type=rec.source_type.value if hasattr(rec.source_type, "value") else str(rec.source_type),
                content=rec.content,
                score=round(float(rec.retrieval_score), 4),
                rank=rec.rank
            )
        )
    return payloads


def run_pipeline(
    user_message: str,
    *,
    session_id: str = "default",
    generate_pdf: bool = False,
    send_email: bool = False,
    email_recipient: Optional[str] = None
) -> ChatResponsePayload:
    """Synchronous execution of the entire MediScan Agentic RAG pipeline."""
    t_start = time.perf_counter()
    history_str = session_store.format_history(session_id)
    session_store.add_message(session_id, "user", user_message)

    # 1. Clinical Extraction
    extracted_info = extract_clinical_info(user_message)

    # 2. Router
    router_hint = route_query(user_message)

    # 3. GLM Planner
    raw_plan = generate_agent_plan(user_message, extracted_info, router_hint, history_str)
    plan = validate_agent_plan(raw_plan)

    # 4. Retrieval Execution
    evidence: List[EvidenceRecord] = []
    if plan.needs_evidence:
        evidence = execute_retrieval(plan.queries, plan.retrieval_mode.value, router_hint.query_type)
        evidence = select_and_map_citations(evidence, max_items=5)

    # 5. Bounded Generation & Recovery Loop
    max_drafts = 3
    attempt = 1
    final_draft = ""
    final_action = PolicyAction.ESCALATE
    tier0 = Tier0Result(is_valid=False, errors=["Not executed"])

    while attempt <= max_drafts:
        # Generate Draft
        draft = generate_medical_response(
            user_message,
            extracted_info,
            evidence,
            plan.response_type,
            history_str
        )

        # Tier 0 Deterministic Checks
        tier0 = run_tier0_validation(draft, evidence)

        # DeepSeek Evaluator
        verdict = evaluate_draft(user_message, draft, evidence)

        # Policy Decision
        action = decide_policy_action(tier0, verdict, attempt, max_drafts)
        final_action = action
        final_draft = draft

        if action == PolicyAction.ACCEPT:
            break
        elif action == PolicyAction.RE_RETRIEVE:
            new_query = verdict.missing_evidence_query or f"{user_message} guideline recommendations"
            more_evidence = execute_retrieval([new_query], plan.retrieval_mode.value, "guideline")
            evidence = select_and_map_citations(evidence + more_evidence, max_items=5)
            attempt += 1
        elif action == PolicyAction.REGENERATE:
            attempt += 1
        else:  # ESCALATE
            final_draft = (
                "### MediScan Clinical Notice\n\n"
                "The available knowledge base evidence is insufficient to formulate a verified clinical interpretation "
                f"for the query: *'{user_message}'*.\n\n"
                "**Recommendation**: Please consult a licensed radiologist or clinical specialist for a definitive reading.\n\n"
                "---\n**Disclaimer**: MediScan is a research prototype. Clinical findings require human expert verification."
            )
            break

    # Append assistant response to session memory
    session_store.add_message(session_id, "assistant", final_draft)

    # 6. Post-Approval Delivery (ONLY on ACCEPT)
    pdf_file = None
    pdf_download_url = None
    email_delivered = False
    email_status = None

    if final_action == PolicyAction.ACCEPT:
        # Generate PDF only when explicitly requested
        if generate_pdf or send_email:
            pdf_file = generate_pdf_report(
                final_draft,
                session_id=session_id,
                response_type=plan.response_type,
                final_action=final_action.value,
                evidence_count=len(evidence)
            )
            pdf_name = Path(pdf_file).name
            pdf_download_url = f"/api/reports/download/{pdf_name}"

        # Explicit opt-in email delivery only
        if send_email:
            if not email_recipient:
                email_status = "EMAIL_NOT_SENT_NO_RECIPIENT"
            else:
                email_delivered, email_status = send_report_email(pdf_file, email_recipient)
    else:
        if generate_pdf or send_email:
            email_status = f"DELIVERY_BLOCKED_FINAL_ACTION_{final_action.value}"

    latency = round((time.perf_counter() - t_start) * 1000, 2)

    return ChatResponsePayload(
        user_message=user_message,
        final_answer=final_draft,
        session_id=session_id,
        plan=plan,
        final_action=final_action.value,
        attempts_made=attempt,
        evidence_used=_convert_evidence_records(evidence),
        pdf_path=pdf_file,
        pdf_download_url=pdf_download_url,
        email_sent=email_delivered,
        email_status=email_status,
        trace={
            "latency_ms": latency,
            "router": router_hint.model_dump(),
            "tier0_valid": tier0.is_valid
        }
    )


async def stream_pipeline(
    user_message: str,
    *,
    session_id: str = "default",
    generate_pdf: bool = False,
    send_email: bool = False,
    email_recipient: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """Async generator streaming SSE events at every pipeline step."""
    t_start = time.perf_counter()
    history_str = session_store.format_history(session_id)
    session_store.add_message(session_id, "user", user_message)

    yield {
        "event": "analysis_started",
        "data": {"stage": "analysis_started", "message": "Understanding clinical request..."}
    }

    # 1. Extraction
    extracted_info = extract_clinical_info(user_message)
    yield {
        "event": "extraction_completed",
        "data": {
            "stage": "extraction_completed",
            "message": "Extracted structured clinical facts",
            "findings": extracted_info.model_dump()
        }
    }

    # 2. Router
    router_hint = route_query(user_message)
    yield {
        "event": "routing_completed",
        "data": {
            "stage": "routing_completed",
            "message": f"Query routed: {router_hint.query_type} (mode: {router_hint.suggested_retrieval_mode})",
            "router": router_hint.model_dump()
        }
    }

    # 3. GLM Planner
    raw_plan = generate_agent_plan(user_message, extracted_info, router_hint, history_str)
    plan = validate_agent_plan(raw_plan)
    yield {
        "event": "planning_completed",
        "data": {
            "stage": "planning_completed",
            "message": f"Plan formulated: {plan.intent.value} via {plan.retrieval_mode.value}",
            "plan": plan.model_dump()
        }
    }

    # 4. Retrieval Execution
    evidence: List[EvidenceRecord] = []
    if plan.needs_evidence:
        yield {
            "event": "retrieval_started",
            "data": {
                "stage": "retrieval_started",
                "message": f"Searching knowledge store with {len(plan.queries)} queries..."
            }
        }
        evidence = execute_retrieval(plan.queries, plan.retrieval_mode.value, router_hint.query_type)
        evidence = select_and_map_citations(evidence, max_items=5)
        yield {
            "event": "retrieval_completed",
            "data": {
                "stage": "retrieval_completed",
                "message": f"Found {len(evidence)} verified evidence records",
                "evidence_count": len(evidence),
                "evidence": [e.model_dump() for e in _convert_evidence_records(evidence)]
            }
        }

    # 5. Bounded Generation & Recovery Loop
    max_drafts = 3
    attempt = 1
    final_draft = ""
    final_action = PolicyAction.ESCALATE
    tier0 = Tier0Result(is_valid=False, errors=["Not executed"])

    while attempt <= max_drafts:
        yield {
            "event": "generation_started",
            "data": {
                "stage": "generation_started",
                "message": f"Synthesizing evidence-grounded response (Attempt {attempt}/{max_drafts})...",
                "attempt": attempt
            }
        }

        draft = generate_medical_response(
            user_message,
            extracted_info,
            evidence,
            plan.response_type,
            history_str
        )

        yield {
            "event": "validation_started",
            "data": {
                "stage": "validation_started",
                "message": "Validating clinical structure and citations...",
                "attempt": attempt
            }
        }
        tier0 = run_tier0_validation(draft, evidence)

        yield {
            "event": "evaluation_started",
            "data": {
                "stage": "evaluation_started",
                "message": "DeepSeek independent clinical evaluator running...",
                "attempt": attempt
            }
        }
        verdict = evaluate_draft(user_message, draft, evidence)

        action = decide_policy_action(tier0, verdict, attempt, max_drafts)
        final_action = action
        final_draft = draft

        yield {
            "event": "policy_evaluated",
            "data": {
                "stage": "policy_evaluated",
                "action": action.value,
                "attempt": attempt,
                "tier0_valid": tier0.is_valid,
                "groundedness": verdict.groundedness,
                "safety": verdict.safety_compliance
            }
        }

        if action == PolicyAction.ACCEPT:
            break
        elif action == PolicyAction.RE_RETRIEVE:
            new_query = verdict.missing_evidence_query or f"{user_message} guideline recommendations"
            more_evidence = execute_retrieval([new_query], plan.retrieval_mode.value, "guideline")
            evidence = select_and_map_citations(evidence + more_evidence, max_items=5)
            attempt += 1
        elif action == PolicyAction.REGENERATE:
            attempt += 1
        else:  # ESCALATE
            final_draft = (
                "### MediScan Clinical Notice\n\n"
                "The available knowledge base evidence is insufficient to formulate a verified clinical interpretation "
                f"for the query: *'{user_message}'*.\n\n"
                "**Recommendation**: Please consult a licensed radiologist or clinical specialist for a definitive reading.\n\n"
                "---\n**Disclaimer**: MediScan is a research prototype. Clinical findings require human expert verification."
            )
            break

    # Save to history
    session_store.add_message(session_id, "assistant", final_draft)

    # 6. PDF and delivery
    pdf_file = None
    pdf_download_url = None
    email_delivered = False
    email_status = None

    if final_action == PolicyAction.ACCEPT:
        if generate_pdf or send_email:
            pdf_file = generate_pdf_report(
                final_draft,
                session_id=session_id,
                response_type=plan.response_type,
                final_action=final_action.value,
                evidence_count=len(evidence)
            )
            pdf_name = Path(pdf_file).name
            pdf_download_url = f"/api/reports/download/{pdf_name}"

        if send_email:
            if not email_recipient:
                email_status = "EMAIL_NOT_SENT_NO_RECIPIENT"
            else:
                email_delivered, email_status = send_report_email(pdf_file, email_recipient)
    else:
        if generate_pdf or send_email:
            email_status = f"DELIVERY_BLOCKED_FINAL_ACTION_{final_action.value}"

    latency = round((time.perf_counter() - t_start) * 1000, 2)

    final_payload = ChatResponsePayload(
        user_message=user_message,
        final_answer=final_draft,
        session_id=session_id,
        plan=plan,
        final_action=final_action.value,
        attempts_made=attempt,
        evidence_used=_convert_evidence_records(evidence),
        pdf_path=pdf_file,
        pdf_download_url=pdf_download_url,
        email_sent=email_delivered,
        email_status=email_status,
        trace={
            "latency_ms": latency,
            "router": router_hint.model_dump(),
            "tier0_valid": tier0.is_valid
        }
    )

    yield {
        "event": "report_ready",
        "data": final_payload.model_dump()
    }
