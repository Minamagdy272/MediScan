# MediScan: Adapted Agentic RAG, Feedback, and Evaluation Upgrade

## 1. Purpose and scope

This document adapts the proposed *Hybrid Adaptive Agentic RAG and Feedback/Evaluation* addendum to the **current MediScan repository**. It is an implementation plan for the existing chest-X-ray reporting prototype; it is not a direct adoption of the addendum's broader multi-role clinical platform.

The target remains:

> Convert a chest X-ray CV finding and a user question into an evidence-grounded draft report, then create a PDF and optionally deliver it by email.

The upgrade should improve traceability, retrieval quality, and safety without prematurely turning the notebook prototype into a large multi-tool medical platform.

## 2. Current-project assessment

### What already fits the proposed direction

| Current capability | Existing implementation | How it supports the upgrade |
|---|---|---|
| Structured clinical extraction | `ExtractedMedicalInfo` Pydantic schema in `src/Mediscan_pipeline.ipynb` | Provides the correct starting state for controlled retrieval and evaluation. |
| Grounded report prompt | `final_rag_prompt` instructs the model to use retrieved context only and state uncertainty | Can become the draft-generation stage. |
| Persistent RAG store | Chroma collection `mediscan_rag` in `vectorstore/chroma_db` | Retain as the first dense retriever. |
| Curated chest/radiology corpus | `data/cleaned/` plus OpenI report extraction and clinical references | Supports a focused chest-X-ray pilot corpus. |
| NVIDIA NIM models | `NVIDIAEmbeddings` and `ChatNVIDIA` | Can be used for structured grading calls as well as generation. |
| PDF and Gmail delivery | ReportLab and Gmail functions in the pipeline notebook | Keep as post-approval delivery stages. |
| Basic conversation memory | `InMemoryChatMessageHistory` | May remain for prototype follow-up questions, but is not a clinical longitudinal record. |

### Important gaps to close

| Gap | Why it matters | Adapted change |
|---|---|---|
| Retrieval uses only dense similarity search and then keeps the first six unique chunks | Context quality depends on query order and can include weak evidence | Add stable evidence records, ranking scores, and a lightweight reranking/selection stage. |
| Chunks have no documented clinical provenance schema | The pipeline cannot reliably validate or cite the evidence used | Enrich ingestion metadata and assign a stable `chunk_id` to every indexed chunk. |
| The report exposes source names but no auditable citations | A generated statement cannot be traced to a specific retrieved passage | Generate citations only from the retrieved evidence IDs. |
| Safety rules currently live mainly in the generation prompt | Prompts alone cannot prevent unsupported output from being delivered | Add deterministic output checks and a structured feedback verdict before PDF/email delivery. |
| No automated evaluation dataset, feedback log, or tests | Retrieval and report quality cannot be measured as the corpus changes | Store non-sensitive traces and create a small fixed evaluation set. |
| The pipeline emails automatically to a hard-coded recipient | Unsafe for demonstrations and inappropriate for real clinical data | Make delivery explicitly opt-in and pass the recipient as a runtime argument; never send a rejected draft. |
| The project is notebook-first | Complex quality checks can become hard to follow when scattered across notebook cells | Keep each new concern in a clearly named, documented notebook section and add notebook validation cells. |

## 3. Decisions for this MediScan version

### Adopt now

1. **Evidence provenance and citations.** Every retrieved chunk must carry a stable ID, source title, source URL or local source path, source type, audience, and condition tags. The final report can cite only IDs returned in that request.
2. **Deterministic safety gates.** Validate required report sections, citations, known source IDs, explicit uncertainty text where evidence is insufficient, and the presence of the research disclaimer before delivery.
3. **A structured feedback verdict.** Use a separate, fresh structured-output model call to assess groundedness, citation validity, relevance, context sufficiency, and safety. It must not decide routing by itself.
4. **Bounded recovery.** Use deterministic routing: accept, regenerate from the same evidence, re-retrieve once with a focused query, or return a safe insufficient-evidence response. Cap the complete flow at three generation attempts.
5. **Shadow-mode evaluation first.** Log what the evaluator would have done before allowing it to block or retry any live pipeline output.
6. **Offline evaluation.** Maintain a small chest-X-ray test set with expected evidence and safety expectations; rerun it after changes to the corpus, prompts, or retrieval configuration.

### Defer until the project has the required foundations

The following addendum features should remain future work rather than being copied into the current prototype:

- A general-purpose, multi-tool LangGraph agent with `PatientHistoryTool`, `SimilarCaseTool`, and `RiskAssessmentTool`. The repository currently has no patient-history database, risk model, or governed case-retrieval interface.
- Doctor, patient, and student role modes. The current output is a single patient/clinician-oriented report and requires separate requirements and review before role-specific output is safe.
- Arabic/English medical translation. Add only after a bilingual evaluation set and medical terminology validation are available.
- `SelfQueryRetriever` and metadata-driven natural-language filters. These depend on completing source and chunk metadata first.
- `ParentDocumentRetriever`, `MultiQueryRetriever`, full BM25 hybrid retrieval, and cross-encoder reranking. They are useful next-stage retrieval improvements, but should follow a measured dense-retrieval baseline rather than be introduced together.
- Automated collection of new external sources. Source acquisition must be governed by a registry, licensing review, content cleaning, and manual quality checks.

## 4. Adapted runtime architecture

The upgrade introduces a **controlled recovery loop**, not an unrestricted autonomous agent.

```text
CV findings + user question
          |
          v
Structured extraction (existing Pydantic model)
          |
          v
Query planner (existing query templates, made configurable)
          |
          v
Chroma dense retrieval -> de-duplication -> evidence normalization/ranking
          |                                  |
          |                                  +-- stable chunk IDs and provenance
          v
Evidence sufficiency check
          |
          +-- insufficient --> safe insufficient-evidence response
          |
          v
Draft report generation (existing grounded prompt, now with citation IDs)
          |
          v
Tier 0 deterministic checks
          |
          v
Structured evaluator in shadow mode / enforced mode
          |
          +-- ACCEPT ------> final report -> PDF -> optional explicit email delivery
          |
          +-- REGENERATE --> revise using the evaluator's structured issues
          |
          +-- RE_RETRIEVE -> focused retrieval -> one new draft
          |
          +-- ESCALATE ----> safe non-diagnostic response; do not email automatically
```

The evaluator never communicates directly with the end user. Its explanations are internal trace data; the user receives either an approved report or a short safe fallback.

## 5. Core contracts

### 5.1 Evidence record

Replace raw `Document` handling at the generation boundary with a normalized record similar to the following:

```text
EvidenceRecord
  chunk_id: string
  content: string
  retrieval_score: float | null
  source_id: string
  source_title: string
  source_type: guideline | clinical_reference | patient_education | radiology_report
  audience: clinician | patient | mixed
  condition_tags: list[string]
  source_url: string | null
  local_path: string
```

`chunk_id` must be deterministic across retrieval and report generation. A hash of source ID, section identifier, and chunk index is sufficient for the first version.

### 5.2 Evaluation verdict

Use Pydantic structured output for a verdict with independent 0–1 scores:

```text
EvaluationVerdict
  groundedness
  citation_validity
  answer_relevance
  context_sufficiency
  safety_compliance
  blocking_issues: list[string]
  missing_evidence_query: string | null
  suggested_action: ACCEPT | REGENERATE | RE_RETRIEVE | ESCALATE
```

The actual action is calculated in normal Python code. Example initial policy:

| Condition | Deterministic action |
|---|---|
| Invalid/missing citation, unsupported patient fact, missing disclaimer, or `safety_compliance < 0.80` | `ESCALATE` |
| `context_sufficiency < 0.60` and no focused retrieval has been attempted | `RE_RETRIEVE` |
| `groundedness < 0.75`, `citation_validity < 0.85`, or `answer_relevance < 0.70` on the first draft | `REGENERATE` |
| The same issue remains after the allowed recovery attempts | `ESCALATE` |
| All thresholds pass | `ACCEPT` |

Thresholds are initial engineering defaults, not clinical validation. They must be calibrated against manually reviewed test cases.

### 5.3 Tier 0 deterministic checks

Run these checks on every report before any LLM evaluator call:

- Required report headings are present and non-empty.
- Every citation ID in the draft belongs to the current request's selected evidence set.
- No source type excluded from patient-facing content is used in the patient explanation.
- The report includes uncertainty/limitations when the evidence set is below the minimum threshold.
- The required MediScan research disclaimer is included.
- The report does not claim that an explicitly negative X-ray finding rules out a condition.

These checks are cheap, predictable, and testable. They should be the first safety layer; a judge model is a supplement, not a substitute.

## 6. Retrieval upgrade path

### Phase R1 — make the current dense retrieval measurable

Keep Chroma and the current NVIDIA embedding model. Modify ingestion so each cleaned document has documented metadata and each output chunk receives a `chunk_id`. At runtime, retain scores and choose final context according to score and source diversity rather than query-loop order.

Create 15–20 representative chest-X-ray questions covering pneumonia, pleural effusion, pneumothorax, pulmonary edema, COPD, and heart failure. For each, record the expected source or chunk. Measure Recall@k and manually assess the final context before changing retrieval architecture.

### Phase R2 — improve precision

Add a deterministic evidence filter first: remove duplicate text, preserve high-quality source types, and limit near-identical chunks. If the baseline shows poor precision, add a reranker or LLM evidence-relevance grader that returns `keep/drop` decisions with chunk IDs.

### Phase R3 — hybrid retrieval, only if the baseline justifies it

Add BM25 over the same cleaned corpus and fuse it with the Chroma dense results. Compare dense, BM25, and hybrid retrieval on the fixed evaluation set. Keep hybrid retrieval only if it improves the measured metrics or clear manual review, not merely because it was present in the original addendum.

### Phase R4 — advanced retrievers

After metadata quality is verified, evaluate metadata filters and section/parent-document retrieval. Multi-query expansion should be restricted to comparison or follow-up questions because it increases latency and can broaden irrelevant context.

## 7. Feedback and evaluation rollout

### Phase E1 — offline test assets

Create a versioned evaluation file containing at least 20 synthetic or fully de-identified cases. Each case should include:

- CV input and user question;
- expected extracted facts;
- expected or acceptable evidence IDs/source types;
- expected safety behaviour, including an insufficient-evidence case;
- a short human-reviewed reference assessment.

Do not place identifiable patient information, emails, access tokens, or Gmail credentials in this file or in feedback logs.

### Phase E2 — evaluator in shadow mode

Run Tier 0 checks and the structured evaluator, but always return the current draft. Save the verdict, policy decision, selected evidence IDs, and attempt number. Review false accepts and false rejects against the offline set before turning on recovery actions.

### Phase E3 — enforce bounded recovery

Enable `REGENERATE` and one `RE_RETRIEVE` attempt for selected test scenarios. The maximum is three generated drafts total. If a draft still fails, return a standard safe response saying that the available information is not sufficient for a reliable interpretation and that a qualified clinician should review the finding.

### Phase E4 — operational metrics

Measure and document:

- extraction schema-validity rate;
- retrieval Recall@k and context precision on the fixed set;
- citation-validity rate;
- evaluator agreement with manual review;
- report acceptance, regeneration, re-retrieval, and fallback rates;
- latency and API cost per report.

## 8. Notebook-based implementation structure

All new implementation logic should remain inside the two existing notebooks. No additional Python source files are required for this upgrade. The notebooks remain the executable implementation and documentation of the system.

```text
MediScan/
├── src/
│   ├── building_vdb.ipynb
│   │   ├── source registry and metadata preparation
│   │   ├── chunk ID assignment
│   │   ├── Chroma indexing
│   │   └── retrieval-baseline validation cells
│   │
│   └── Mediscan_pipeline.ipynb
│       ├── existing extraction and query generation
│       ├── evidence normalization, ranking, and citation formatting
│       ├── Tier 0 deterministic checks
│       ├── structured evaluator and action policy
│       ├── bounded regenerate / re-retrieve loop
│       ├── feedback logging
│       ├── PDF generation and explicit email delivery
│       └── notebook validation/demo cells
├── data/
│   ├── cleaned/
│   ├── registry/
│   │   └── source_registry.csv       # created/read by building_vdb.ipynb
│   └── evaluation/
│       └── chest_xray_cases.jsonl    # read by validation cells in the notebooks
├── feedback/                         # non-sensitive development traces; ignored by Git
└── vectorstore/
```

### Placement inside `building_vdb.ipynb`

Add the following sections after document cleaning and before Chroma persistence:

1. **Source registry and metadata** — define the source fields, source type, intended audience, condition tags, and local path for each collected document.
2. **Stable chunk identifiers** — assign a deterministic `chunk_id` and preserve source metadata on every chunk created by the splitter.
3. **Index validation** — run the fixed retrieval questions and print the returned chunk IDs, sources, and scores for manual review.

### Placement inside `Mediscan_pipeline.ipynb`

Add the following sections after the existing retrieval/deduplication cells and before the final PDF/email cells:

1. **Evidence normalization and context selection** — retain retrieval scores and provenance, select context based on relevance and source diversity, and build citation labels from `chunk_id`.
2. **Tier 0 validation** — define ordinary notebook functions for required headings, valid citations, disclaimer presence, and limitations checks.
3. **Structured evaluator** — define `DimensionScore` and `EvaluationVerdict` Pydantic models, then invoke a fresh `ChatNVIDIA` structured-output call to grade the generated draft.
4. **Deterministic action policy and bounded retry** — define normal notebook functions that map the verdict to `ACCEPT`, `REGENERATE`, `RE_RETRIEVE`, or `ESCALATE`; keep the cap at three drafts total.
5. **Feedback log** — append non-sensitive JSONL records from the notebook. Do not log tokens, credentials, email addresses, or identifiable patient information.
6. **Validation cells** — load the de-identified evaluation cases, run them through the pipeline, and display the metrics defined in Section 7.

## 9. Implementation sequence and acceptance criteria

| Order | Deliverable | Acceptance criterion |
|---:|---|---|
| 1 | Baseline and configuration cleanup | Notebook flow runs with configuration supplied outside source cells; email delivery is opt-in. |
| 2 | Source registry and chunk metadata | A retrieved chunk can be traced to one source record and a stable chunk ID. |
| 3 | Evidence-aware generation | A report cites only the chunk IDs selected for its request. |
| 4 | Tier 0 checks with tests | Synthetic invalid citations and missing required sections are always rejected. |
| 5 | Fixed evaluation set | At least 20 de-identified chest-X-ray cases can be run reproducibly. |
| 6 | Structured evaluator in shadow mode | Verdicts and deterministic recommended actions are recorded without blocking reports. |
| 7 | Bounded recovery loop | A seeded unsupported claim triggers regeneration or safe fallback and never reaches PDF/email as an approved report. |
| 8 | Retrieval enhancement experiment | Dense baseline and any BM25/hybrid alternative are compared on the same evaluation set. |
| 9 | Controlled delivery | PDF/email runs only after an accepted verdict and an explicit delivery request. |

## 10. Out-of-scope and safety boundary

MediScan remains a research/portfolio prototype for **clinical report drafting**, not diagnosis, treatment, triage, or autonomous patient communication. The upgraded pipeline must:

- preserve explicit negative findings without treating them as disease exclusion;
- avoid definitive diagnoses and treatment recommendations unless the retrieved, approved evidence directly supports the wording;
- return a safe limitation message rather than invent evidence or looping indefinitely;
- retain only the minimum non-sensitive trace data needed for evaluation;
- require licensed clinical review before any real patient-care use.

## 11. Final recommendation

Implement the feedback/evaluation layer and evidence provenance **before** introducing a full agent framework. For this repository, the highest-value next milestone is a testable, citation-aware, bounded RAG pipeline with shadow-mode evaluation. Once that baseline is measured, the project can make an evidence-based decision about hybrid retrieval, extra tools, LangGraph orchestration, bilingual output, and role-specific workflows.
