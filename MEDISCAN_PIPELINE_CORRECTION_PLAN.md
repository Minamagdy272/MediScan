# MediScan Pipeline Correction Plan

## Purpose

This plan addresses the gaps between the intended agentic-RAG architecture and the current implementation in `src/Mediscan_pipeline.ipynb`. It is a planning document only. It does not change the current notebook, vector database, or delivery flow.

The goal is to stabilize the conversational, evidence-grounded pipeline before adding more tools, user roles, multilingual output, or other advanced features.

## Current Architecture Strengths

The current pipeline already has a solid foundation:

- A separate router, planner, deterministic executor, generator, evaluator, and delivery stage.
- A frozen VDB retrieval interface with BM25, hybrid retrieval, reranking, and `EvidenceRecord` citations.
- Bounded recovery actions: `ACCEPT`, `REGENERATE`, `RE_RETRIEVE`, and `ESCALATE`.
- Optional PDF generation and optional email delivery after an accepted response.
- An in-memory session history for follow-up questions.

The required work is primarily about making the runtime behavior match these architectural intentions.

## Priority 1 — Safety and Evidence Integrity

### 1. Fail safely when the evaluator is unavailable

**Current issue:** If the evaluator call fails, the fallback produces high quality scores and returns `ACCEPT`.

**Required change:** An evaluator failure must never create a synthetic successful verdict. Return an explicit `EVALUATOR_UNAVAILABLE` status and route to `ESCALATE`, or use a conservative deterministic safe response.

**Acceptance criteria:**

- A forced evaluator exception cannot result in `ACCEPT`.
- The returned response clearly states that the system could not complete a verified assessment.
- PDF and email delivery remain disabled for that response.

### 2. Use the VDB sufficiency result as the authoritative gate

**Current issue:** Retrieval requests `require_sufficient_evidence=True`, but the resulting sufficiency information is discarded. The local check only tests whether at least one evidence item exists.

**Required change:** Preserve the full retrieval result for each query, including sufficiency status, reasons, quality indicators, and result count. Use this returned data before generation.

**Acceptance criteria:**

- A retrieval result marked insufficient by the frozen VDB cannot proceed to an evidence-grounded answer.
- The pipeline returns a safe limitation response when the VDB cannot provide sufficient evidence.
- The trace records the VDB sufficiency decision and reason.

### 3. Strengthen Tier 0 deterministic validation

**Current issue:** Tier 0 checks only basic length, disclaimer text, citation IDs, and the existence of a heading.

**Required change:** Add deterministic checks for:

- all required sections for the selected response type;
- citations that belong to the active evidence set;
- required uncertainty wording when evidence is limited;
- preservation of explicit negative findings;
- prohibited unsupported statements or diagnostic certainty patterns;
- source audience/type restrictions for patient-facing responses.

**Acceptance criteria:**

- Synthetic drafts with fake citations, missing sections, missing limitations, or negative-finding contradictions are rejected.
- The checks run without an LLM call.

## Priority 2 — Make the Pipeline a Real Chatbot

### 4. Make `response_type` control the final answer format

**Current issue:** `response_type` exists in `AgentPlan`, but the generator always follows the same clinical-report structure.

**Required change:** Define a distinct response contract for each supported type:

| Response type | Intended output |
|---|---|
| `direct_answer` / `EXPLAIN` | Concise explanation, common context, evidence citations, and disclaimer. |
| `educational_summary` / `EDUCATIONAL` | Patient-friendly explanation, symptoms/context, when to seek review, citations, and disclaimer. |
| `report` / `INTERPRET` | Structured clinical interpretation with findings, possible explanations, limitations, citations, and disclaimer. |
| `comparison_table` / `COMPARE` | Explicit comparison between current and previous stated findings; no inference beyond available evidence. |
| `guideline` / `GUIDELINE` | Guideline-focused answer with source provenance and uncertainty. |

**Acceptance criteria:**

- A question such as “What is pleural effusion?” returns an explanatory answer, not a full radiology report.
- A CV finding input produces the structured interpretation format.
- A comparison question uses a comparison-oriented structure only when earlier information exists in the session.

### 5. Clarify Router and Planner authority

**Current issue:** The router suggests retrieval mode and the planner chooses a retrieval mode, but the final authority is not explicit.

**Required change:** Define the router as a lightweight classifier that provides language, query type, and complexity hints. Define the planner as the final authority for intent, retrieval mode, queries, and available tool selection. Log both decisions for evaluation.

**Acceptance criteria:**

- Documentation and trace data clearly label the router output as a hint.
- The executor uses only the validated planner decision for execution.
- Planner fallback behavior remains deterministic and safe.

## Priority 3 — Align the Plan Contract with Real Capabilities

### 6. Restrict tools to implemented tools

**Current issue:** The planner may choose tools that do not have independent execution paths.

**Required change:** For the current phase, allow only:

- `MedicalRAGTool` — the canonical frozen retrieval interface;
- `ClinicalGuidelineTool` — only if implemented explicitly as metadata-filtered guideline retrieval.

Keep `SimilarCaseTool`, `PatientHistoryTool`, `RiskAssessmentTool`, and `ReportGeneratorTool` disabled until each has a real implementation, governed data source, standalone test, and clear safety contract.

**Acceptance criteria:**

- Every tool permitted by the plan validator has an actual executor path.
- Unsupported tools cannot appear in a validated executable plan.
- `needs_guideline` and `needs_history` either affect execution or are removed/deferred from the plan schema.

### 7. Correct the re-retrieval flow

**Current issue:** The recovery loop combines old and new evidence, then takes the first five records. It does not re-rank, deduplicate, or rerun the sufficiency gate.

**Required flow:**

```text
Focused missing-evidence query
        ↓
Retrieve candidate evidence
        ↓
Merge with prior candidate pool
        ↓
Deduplicate by stable chunk ID
        ↓
Rerank and select using the response-type evidence budget
        ↓
Assign fresh citation IDs
        ↓
Run VDB/evidence sufficiency validation again
        ↓
Generate one new draft
```

**Acceptance criteria:**

- Re-retrieval cannot leave duplicate evidence records in the selected context.
- Citation IDs always represent the final selected evidence set.
- New evidence is not crowded out merely because old evidence was retrieved first.

### 8. Replace the fixed evidence budget

**Current issue:** The pipeline always limits selected evidence to five records.

**Required change:** Choose an evidence budget by response type and query complexity.

| Scenario | Initial evidence budget |
|---|---:|
| Simple direct explanation | 3–5 records |
| Patient educational answer | 4–6 records |
| Clinical interpretation | 5–8 records |
| Comparison or complex guideline question | 8–12 records |

These are engineering defaults and should be calibrated on the evaluation set.

## Priority 4 — Delivery and Conversation Reliability

### 9. Repair Gmail delivery semantics

**Current issue:** Missing Gmail credentials currently produce a simulated message but return `True`, which can mark email delivery as successful. The OAuth flow also does not handle the case where client credentials exist but the token is missing.

**Required change:**

- Return `False` and a clear delivery status when email is simulated or unavailable.
- Restore a complete OAuth desktop flow: load valid token, refresh an expired token, or create a token from client credentials when needed.
- Keep `send_email=False` by default and require an explicit recipient.

**Acceptance criteria:**

- `email_sent=True` means the Gmail API returned a successful send result.
- Missing credentials never report a successful send.
- A rejected, escalated, or evaluator-unavailable draft cannot trigger delivery.

### 10. Define history and attempt metrics explicitly

**Current issue:** Current-user input is passed separately from history, which is valid but should be documented. `attempts_made` does not distinguish draft generation from retrieval recovery.

**Required change:** Keep the current turn separate from previous history, but document this contract. Record:

- `generation_attempts`;
- `retrieval_attempts`;
- `total_recovery_cycles`;
- final policy action;
- evaluator and Tier 0 results.

**Acceptance criteria:**

- Every trace can explain why the pipeline accepted, regenerated, re-retrieved, or escalated a response.

## Priority 5 — Multilingual Support (After Core Stabilization)

### 11. Add translation as a boundary layer

Translation is not currently implemented and should not be mixed into the planner or tool-execution logic.

```text
Raw user message
      ↓
Language detection
      ↓
Arabic input: translate to canonical English
      ↓
Extraction → Router → Planner → Retrieval → Generation → Evaluation
      ↓
Arabic original language: translate approved final answer to Arabic
      ↓
User response
```

Preserve negation, laterality, measurements, units, and citation identifiers. Translation must occur only after a response has passed the safety and evidence gates.

**Acceptance criteria:**

- Arabic input reaches retrieval as canonical English while retaining the original-language record for the response layer.
- Citation IDs remain unchanged after translation.
- Arabic medical output is tested on a reviewed bilingual case set.

## Execution Order

1. Evaluator failure safety.
2. VDB sufficiency integration.
3. Tier 0 expansion.
4. Tool-contract restriction.
5. Response-type generator formats.
6. Re-retrieval rebuild and evidence budgets.
7. Gmail OAuth and delivery-status correction.
8. Trace metrics and interactive end-to-end tests.
9. Arabic translation boundary.
10. Only then consider patient/doctor/student roles and future tools.

## Definition of a Stable Baseline

The pipeline is ready for additional features when it can reliably:

- answer simple educational questions as chat answers rather than reports;
- produce structured interpretations for CV findings;
- cite only selected evidence records;
- refuse safely when evidence or evaluator verification is unavailable;
- complete bounded recovery without duplicate or stale evidence;
- avoid false email-success states;
- pass a fixed, de-identified evaluation set covering direct questions, CV interpretation, follow-up comparison, insufficient evidence, invalid citations, evaluator failure, and email opt-out.

Until this baseline is reached, new role modes, additional clinical tools, and multilingual output should remain deferred.
