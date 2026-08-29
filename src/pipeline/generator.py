"""
Medical Report Generator Component (GLM-5.3-Flash via OpenRouter).
"""

from typing import List
from langchain_core.prompts import ChatPromptTemplate
from VDB.schema import EvidenceRecord
from .schemas import ExtractedMedicalInfo
from .models import generator_llm

generator_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are the MediScan Medical Report Generator.
Generate an evidence-grounded, professional response based ONLY on the provided evidence.

CRITICAL RULES:
1. Rely ONLY on the retrieved evidence provided under RETRIEVED EVIDENCE.
2. Cite evidence using the EXACT citation IDs in brackets, e.g., [EV-001], [EV-002].
3. Do NOT cite evidence IDs that are not provided in the current context.
4. Do NOT invent diagnoses, treatments, or patient facts.
5. Preserve explicit negative findings (e.g., 'no pneumothorax').
6. State clinical uncertainty clearly when evidence describes multiple possibilities.
7. Always include the required MediScan Research Disclaimer at the end of the report.

REQUIRED STRUCTURE:
# MEDISCAN - CLINICAL REPORT

## Clinical Summary
[State patient findings and symptoms]

## Imaging Findings & Interpretation
[Explain findings with citations, e.g. [EV-001]]

## Differential & Clinical Significance
[Discuss possibilities supported by evidence]

## Uncertainty & Limitations
[State missing data or ambiguous findings]

## Evidence Citations
[List citations with provenance, e.g., - [EV-001] Source Title]

---
**Disclaimer**: MediScan is a research and educational prototype. This report is for decision-support only and does not constitute a definitive medical diagnosis. A licensed clinician must review all findings.
"""),
    ("human", """User Question: {user_message}
Extracted Clinical State: {extracted_summary}
Response Type: {response_type}
Conversation History: {chat_history}

RETRIEVED EVIDENCE:
{evidence_context}

Generate the response:""")
])


def generate_medical_response(
    user_message: str,
    extracted_info: ExtractedMedicalInfo,
    evidence: List[EvidenceRecord],
    response_type: str,
    history_str: str
) -> str:
    """Generates an evidence-grounded clinical report or answer using isolated generator LLM."""
    extracted_summary = (
        f"Symptoms: {extracted_info.symptoms}, "
        f"Imaging: {extracted_info.imaging_findings}, "
        f"Positive: {extracted_info.positive_findings}, "
        f"Negative: {extracted_info.negative_findings}, "
        f"Missing: {extracted_info.missing_information}"
    )
    if evidence:
        evidence_context = "\n\n".join(r.format_citation() for r in evidence)
    else:
        evidence_context = "No specific evidence records retrieved. State uncertainty."

    response = (generator_prompt | generator_llm).invoke({
        "user_message": user_message,
        "extracted_summary": extracted_summary,
        "response_type": response_type,
        "chat_history": history_str,
        "evidence_context": evidence_context
    })
    return response.content
