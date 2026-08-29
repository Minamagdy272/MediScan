"""
Deterministic Action Policy Engine.
Computes ACCEPT, REGENERATE, RE_RETRIEVE, or ESCALATE.
"""

from .schemas import PolicyAction, Tier0Result, EvaluationVerdict


def decide_policy_action(
    tier0: Tier0Result,
    verdict: EvaluationVerdict,
    attempt: int,
    max_attempts: int = 3
) -> PolicyAction:
    """Pure deterministic Python policy mapping evaluations to actions."""
    if not tier0.is_valid:
        if attempt >= max_attempts:
            return PolicyAction.ESCALATE
        return PolicyAction.REGENERATE

    if verdict.safety_compliance < 0.80 or "unsupported" in " ".join(verdict.blocking_issues).lower():
        return PolicyAction.ESCALATE

    if verdict.context_sufficiency < 0.60 and attempt == 1 and verdict.missing_evidence_query:
        return PolicyAction.RE_RETRIEVE

    if (
        verdict.groundedness < 0.75
        or verdict.citation_validity < 0.85
        or verdict.answer_relevance < 0.70
    ) and attempt < max_attempts:
        return PolicyAction.REGENERATE

    if (
        verdict.groundedness >= 0.75
        and verdict.citation_validity >= 0.85
        and verdict.safety_compliance >= 0.80
    ):
        return PolicyAction.ACCEPT

    return PolicyAction.ESCALATE
