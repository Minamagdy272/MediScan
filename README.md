# 🫁 MediScan: Evidence-Grounded Agentic AI for Clinical Intelligence

> **An Enterprise-Grade, 13-Stage Agentic RAG Platform with Deterministic Guardrails for Medical Intelligence, Radiology Analysis, and Automated Clinical Delivery.**

---

<div align="center">
  <img src="assets/mediscan_architecture.png" alt="MediScan System Architecture" width="100%" />
</div>

---

## 📑 Complete System Blueprint & Index

1. [High-Level System Architecture](#1-high-level-system-architecture)
2. [Tier 1 Reference: Frozen VDB & Deterministic Hybrid RAG](#2-tier-1-reference-frozen-vdb--deterministic-hybrid-rag)
3. [Tier 2 Reference: 13-Stage Agentic RAG Pipeline](#3-tier-2-reference-13-stage-agentic-rag-pipeline)
4. [Mathematical & Algorithmic Foundations](#4-mathematical--algorithmic-foundations)
5. [Architectural Flow (End-to-End Data & Hybrid Ingestion)](#5-architectural-flow)
6. [Clinical Work Flow (Execution Sequence Diagram)](#6-clinical-work-flow)
7. [Operations Flow & Runtime State Machine (Bounded Recovery Loop)](#7-operations-flow--runtime-state-machine)
8. [System Use Case Diagrams](#8-system-use-case-diagrams)
9. [User Story Mapping & Requirements Hierarchy](#9-user-story-mapping--requirements-hierarchy)
10. [Core Safety & Clinical Guardrail Principles](#10-core-safety--clinical-guardrail-principles)
11. [Data Sources & Storage Layout](#11-data-sources--storage-layout)
12. [Technology Stack](#12-technology-stack)

---

## 1. High-Level System Architecture

MediScan is engineered as a **two-tier decoupled architecture**:
- **Tier 1 (Deterministic Knowledge Base & RAG Engine)**: Fully deterministic, frozen, reproducible, zero LLM side-effects.
- **Tier 2 (Agentic Clinical Orchestrator)**: 13-stage multi-model pipeline operating strictly on top of Tier 1 via deterministic Python guardrails.

```mermaid
graph TB
    subgraph KNOWLEDGE_SOURCES ["Multi-Source Clinical Knowledge Base"]
        direction LR
        S1["Cleaned Medical Docs"] ~~~ S2["OpenI CXR Reports (XML)"] ~~~ S3["Clinical Guidelines"] ~~~ S4["Web Medical Sources"] ~~~ S5["Patient Education"]
    end

    subgraph TIER1 ["TIER 1: Frozen VDB & Deterministic Hybrid RAG Engine"]
        direction TB
        ACQ["Data Ingestion Layer<br/>(Local, OpenI XML, Web, PDF)"] --> CLEAN["Medical Cleaner & De-Identification"]
        CLEAN --> PARSE["Clinical Section Parser<br/>(FINDINGS, IMPRESSION, HISTORY)"]
        PARSE --> CHUNK["Section-Aware Overlap Chunker<br/>(800 chars / 150 overlap)"]
        CHUNK --> EMB["NVIDIA NIM Embeddings<br/>(nv-embedqa-e5-v5 / 1024 dims)"]
        EMB --> DUAL_IDX["Dual Index Construction"]
        DUAL_IDX --> DENSE_DB[("ChromaDB Vector Store<br/>(Dense Cosine Similarity)")]
        DUAL_IDX --> SPARSE_DB[("BM25 Keyword Index<br/>(Okapi BM25 Lexical)")]
        
        DENSE_DB & SPARSE_DB --> RETRIEVE["Dual Retrieval (Top-20 Dense + Top-20 Sparse)"]
        RETRIEVE --> RRF["Hybrid Fusion<br/>(Reciprocal Rank Fusion k=60)"]
        RRF --> RERANK["NVIDIA NIM Cross-Encoder Reranker<br/>(nv-rerankqa-mistral-4b)"]
        RERANK --> SELECTOR["Evidence Selector & Deduplication<br/>(Diversity + Section Mapping)"]
        SELECTOR --> SUFF_GATE["Sufficiency Gate<br/>(Score >= 0.65 & Min Source Check)"]
        SUFF_GATE --> RETRIEVER_API[["MediScanRetriever.retrieve()<br/>Stable API Contract"]]
    end

    subgraph TIER2 ["TIER 2: 13-Stage Agentic Pipeline with Deterministic Guardrails"]
        direction TB
        U_IN["User Input<br/>(Natural Language / CXR CV Findings)"] --> ST1["1. Router<br/>(Classify Intent & Complexity)"]
        ST1 --> ST2["2. Planner LLM<br/>(Draft Structured AgentPlan JSON)"]
        ST2 --> ST3["3. Plan Validator<br/>(Deterministic Python Safety Check)"]
        ST3 --> ST4["4. Deterministic Executor<br/>(Controlled Step Execution)"]
        ST4 --> ST5["5. Call MediScan RAG API<br/>(Tier 1 Stable Contract)"]
        ST5 --> ST6["6. Evidence Selection<br/>(Top-K Chunks + Full Provenance)"]
        ST6 --> ST7["7. Sufficiency Gate<br/>(Coverage, Score & Diversity Check)"]
        ST7 --> ST8["8. Clinical Generator LLM<br/>(Evidence-Grounded Report Draft)"]
        ST8 --> ST9["9. Tier-0 Validation<br/>(JSON Schema, Regex, Safety Filters)"]
        ST9 --> ST10["10. Independent Evaluator LLM<br/>(DeepSeek-V4 Faithfulness Score)"]
        ST10 --> ST11["11. Deterministic Policy Engine<br/>(Policy Decision Matrix)"]
        
        ST11 -->|"REGENERATE / RE-RETRIEVE"| LOOP{"Bounded Recovery Loop<br/>(Max 3 Drafts)"}
        LOOP -.->|"Draft Retry with Critique"| ST8
        LOOP -.->|"Broaden Search Strategy"| ST5
        
        ST11 -->|"ACCEPT"| ST13["13. Post-Approval Delivery"]
        LOOP -->|"ESCALATE (Exhausted)"| ESCALATE["Safe Uncertainty Fallback"]
        ESCALATE --> ST13
    end

    subgraph OUTPUTS ["Verified Multi-Modal Outputs"]
        direction LR
        ST13 --> O1["Evidence-Grounded Answer"]
        ST13 --> O2["Verifiable Citations (Chunk IDs & Sources)"]
        ST13 --> O3["Branded PDF Clinical Report (ReportLab)"]
        ST13 --> O4["Secure Email Dispatch (OAuth2 SMTP)"]
    end

    KNOWLEDGE_SOURCES ==> TIER1
    TIER1 ==> ST5

    classDef tier1Style fill:#ecfdf5,stroke:#059669,stroke-width:2px,color:#065f46;
    classDef tier2Style fill:#f5f3ff,stroke:#7c3aed,stroke-width:2px,color:#5b21b6;
    classDef outStyle fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e40af;
    class TIER1 tier1Style;
    class TIER2 tier2Style;
    class OUTPUTS outStyle;
```

---

## 2. Tier 1 Reference: Frozen VDB & Deterministic Hybrid RAG

```mermaid
classDiagram
    class SourceRecord {
        +str source_id
        +str title
        +str organization
        +str source_type
        +str evidence_level
    }

    class MedicalDocument {
        +str doc_id
        +str source_id
        +str title
        +str raw_text
        +str condition
        +str body_system
        +str knowledge_domain
        +str source_type
        +str audience
        +str evidence_level
        +dict sections
    }

    class MedicalChunk {
        +str chunk_id
        +str doc_id
        +str source_id
        +str content
        +str section_title
        +int chunk_index
        +str condition
        +str body_system
        +generate_chunk_id()
        +to_metadata_dict()
    }

    class EvidenceRecord {
        +str evidence_id
        +str chunk_id
        +str document_id
        +str content
        +float retrieval_score
        +float dense_score
        +float bm25_score
        +float rrf_score
        +float rerank_score
        +int rank
        +str condition
        +str modality
        +str evidence_level
        +format_citation()
    }

    class EvidenceSufficiencyResult {
        +bool is_sufficient
        +list reason_codes
        +int valid_evidence_count
        +int high_quality_evidence_count
        +int source_diversity_count
        +float best_retrieval_score
        +str recommended_action
    }

    SourceRecord "1" --> "*" MedicalDocument : categorizes
    MedicalDocument "1" --> "*" MedicalChunk : parses & chunks
    MedicalChunk "1" --> "1" EvidenceRecord : ranks & enriches
    EvidenceRecord "*" --> "1" EvidenceSufficiencyResult : evaluated by
```

---

## 3. Tier 2 Reference: 13-Stage Agentic RAG Pipeline

```mermaid
flowchart TD
    subgraph STAGES ["13-Stage Execution Matrix"]
        S1["Stage 1: Intent & Complexity Router (LLM)"]
        S2["Stage 2: Planner (LLM) -> AgentPlan JSON Contract"]
        S3["Stage 3: Plan Validator (Deterministic Python)"]
        S4["Stage 4: Deterministic Executor (Python Controlled)"]
        S5["Stage 5: MediScan RAG API Call (Tier 1 Black Box)"]
        S6["Stage 6: Evidence Selection (Top-K + Provenance)"]
        S7["Stage 7: Sufficiency Gate (Deterministic Score Check)"]
        S8["Stage 8: Clinical Generator (LLM)"]
        S9["Stage 9: Tier-0 Validation (Python Schema/Regex)"]
        S10["Stage 10: Independent Evaluator (Dispassionate LLM)"]
        S11["Stage 11: Deterministic Policy Engine (Python)"]
        S12["Stage 12: Bounded Recovery Loop (Max 3 Drafts)"]
        S13["Stage 13: Post-Approval Delivery (PDF & Email)"]
    end

    S1 --> S2 --> S3 --> S4 --> S5 --> S6 --> S7 --> S8 --> S9 --> S10 --> S11
    S11 -->|"Fail (Score < 0.85)"| S12
    S12 -.->|"Regenerate"| S8
    S12 -.->|"Re-Retrieve"| S5
    S11 -->|"Pass (Score >= 0.85)"| S13

    classDef pyStyle fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;
    classDef llmStyle fill:#f3e8ff,stroke:#9333ea,stroke-width:2px,color:#6b21a8;
    class S3,S4,S5,S6,S7,S9,S11,S12,S13 pyStyle;
    class S1,S2,S8,S10 llmStyle;
```

> **Legend**: 🔵 **Deterministic Python Code (Zero Hallucination)** | 🟣 **Controlled LLM Call (Enforced Contracts)**

---

## 4. Mathematical & Algorithmic Foundations

### 4.1 Hybrid Retrieval: Reciprocal Rank Fusion (RRF)
To balance semantic relevance (dense embeddings) and exact medical terminology (BM25 lexical search), candidate chunks are ranked by:

$$RRF(d) = \sum_{r \in R} \frac{1}{k + r(d)}$$

Where:
- $R$: Set of retrievers (Dense Cosine Similarity + Sparse Okapi BM25).
- $r(d)$: Rank of document $d$ within retriever $r$ ($1 \le r(d) \le 20$).
- $k$: Smoothing constant ($k = 60$).

### 4.2 Cross-Encoder Precision Reranking
Top-15 RRF fused chunks are evaluated via the NVIDIA NIM Cross-Encoder (`nv-rerankqa-mistral-4b`):

$$S_{\text{rerank}}(q, c) = \text{CrossEncoder}(q, c) \in [-\infty, +\infty] \xrightarrow{\text{sigmoid}} [0, 1]$$

### 4.3 Deterministic Sufficiency Metric
Evidence passes to the generator if and only if:

$$\text{Sufficiency} = \left( \max_{e \in E} S(e) \ge 0.65 \right) \land \left( |\{ \text{doc\_id}(e) \mid e \in E \}| \ge 1 \right) \land \left( |E| \ge 1 \right)$$

---

## 5. Architectural Flow

```mermaid
flowchart TD
    %% INGESTION FLOW
    subgraph INGESTION ["Ingestion & Dual Indexing Pipeline (Tier 1)"]
        D1["Raw Clinical Data Sources<br/>(OpenI XML, Guidelines, Web, PDFs)"] --> D2["Normalization & Medical De-identification"]
        D2 --> D3["Clinical Section Header Extractor<br/>(FINDINGS, IMPRESSION, HISTORY, COMPARISON)"]
        D3 --> D4["Section-Aware Chunking (800 chars, 150 overlap)"]
        D4 --> D5["NVIDIA NIM Embeddings (1024-dim vectors)"]
        D5 --> D6A["Dense Indexing (ChromaDB Persistent Store)"]
        D4 --> D6B["Sparse Tokenizer Indexing (Okapi BM25)"]
    end

    %% HYBRID RETRIEVAL FLOW
    subgraph HYBRID_RETRIEVAL ["Hybrid Retrieval & Reranking Subsystem"]
        Q["Clinical Retrieval Query"] --> QA["Dense Semantic Search (Top-20)"]
        Q --> QB["Sparse Keyword Search (Top-20)"]
        QA --> FUSION["Reciprocal Rank Fusion (RRF, k=60)"]
        QB --> FUSION
        FUSION -->|Top 15 Fused Chunks| RERANKER["NVIDIA Cross-Encoder Reranker<br/>(Mistral-4B)"]
        RERANKER -->|Top 5 Chunks| DEDUP["Deduplication & Diversity Gate"]
        DEDUP --> EV_OUT["Evidence Records + Canonical Citations"]
    end

    %% ORCHESTRATION FLOW
    subgraph AGENT_CONTROL ["Agentic Reasoning & Guardrail Flow (Tier 2)"]
        USER_QUERY["Clinician / Patient Query"] --> ROUTER{"Intent & Complexity Router"}
        ROUTER -->|Medical Findings| PLANNER["LLM Plan Generation (AgentPlan)"]
        ROUTER -->|Conversational / Out-of-Domain| DIRECT_ROUTE["Deterministic Guardrail Handler"]
        
        PLANNER --> PLAN_VAL["Deterministic Python Plan Validator"]
        PLAN_VAL -->|Valid Plan Schema| EXEC["Deterministic Step Executor"]
        PLAN_VAL -->|Schema Violation| PLAN_FIX["Plan Auto-Correction"]
        PLAN_FIX --> EXEC
        
        EXEC --> HYBRID_RETRIEVAL
        EV_OUT --> SUFF_CHECK{"Sufficiency Gate: Score >= 0.65?"}
        SUFF_CHECK -->|"Yes (Sufficient)"| GEN_DRAFT["Evidence-Grounded Generator (LLM)"]
        SUFF_CHECK -->|"No (Insufficient)"| QUERY_RETRY["Query Expansion / Soft Fallback"]
        
        GEN_DRAFT --> TIER0_VAL["Tier-0 Syntax, Regex & Safety Verification"]
        TIER0_VAL --> EVALUATOR["Independent LLM Evaluator (Critique & Score)"]
        EVALUATOR --> POLICY{"Deterministic Policy Decision"}
        
        POLICY -->|"Passed (Score >= 0.85)"| ACCEPTED["Approved Clinical Response"]
        POLICY -->|"Failed (Drafts < 3)"| REGEN["Controlled Regeneration with Critique"]
        POLICY -->|"Failed (Drafts >= 3)"| SAFE_FAIL["Safe Clinical Uncertainty Fallback"]
        
        REGEN --> GEN_DRAFT
    end

    D6A & D6B -.-> QA & QB
    ACCEPTED & SAFE_FAIL --> DISPATCH["PDF ReportLab Compilation & SMTP Dispatch"]

    classDef stageBox fill:#ffffff,stroke:#3b82f6,stroke-width:1.5px;
    class D1,D2,D3,D4,D5,D6A,D6B,QA,QB,FUSION,RERANKER,DEDUP,ROUTER,PLANNER,PLAN_VAL,EXEC,GEN_DRAFT,TIER0_VAL,EVALUATOR,POLICY stageBox;
```

---

## 6. Clinical Work Flow

```mermaid
sequenceDiagram
    autonumber
    actor Clinician as Clinician / Radiologist
    participant Gateway as FastAPI Gateway / Orchestrator
    participant Router as Intent Router
    participant Planner as Planner & Validator
    participant Tier1 as Tier 1 Hybrid VDB
    participant Generator as Generator LLM
    participant Evaluator as Independent Evaluator
    participant Policy as Deterministic Policy Engine
    participant Delivery as PDF & Delivery Service

    Clinician->>Gateway: Submit CXR Findings / Follow-up Query
    Gateway->>Router: Classify Clinical Intent & Complexity
    Router-->>Gateway: Return Intent Tag + Execution Strategy
    
    Gateway->>Planner: Request Structured Execution Plan
    Planner-->>Gateway: AgentPlan (Deterministic JSON Contract)
    
    Gateway->>Tier1: Call MediScanRetriever.retrieve(queries)
    Note over Tier1: Dense (ChromaDB) + Sparse (BM25)<br/>+ NVIDIA Reranking + Sufficiency Gate
    Tier1-->>Gateway: EvidenceBundle (Chunks, Scores, Citations)
    
    Gateway->>Generator: Generate Grounded Report (Strict Evidence Context)
    Generator-->>Gateway: Drafted Clinical Report (with Claims & Citations)
    
    Gateway->>Evaluator: Assess Clinical Faithfulness & Hallucination Risk
    Evaluator-->>Gateway: EvaluationReport (Faithfulness Score, Critique)
    
    Gateway->>Policy: Evaluate Guardrail Rules & Recovery Threshold
    alt Quality Score >= 0.85 (ACCEPT)
        Policy-->>Gateway: Verdict: ACCEPT
        Gateway->>Delivery: Generate Branded PDF & Queue Email
        Delivery-->>Clinician: Return Grounded Report + PDF Link + Citation Map
    else Quality Score < 0.85 & Draft Count < 3 (REGENERATE)
        Policy-->>Gateway: Verdict: REGENERATE (with targeted critique feedback)
        Gateway->>Generator: Re-draft with Evaluator Critique
    else Quality Score < 0.85 & Draft Count >= 3 (ESCALATE)
        Policy-->>Gateway: Verdict: ESCALATE
        Gateway-->>Clinician: Safe Fallback with Explicit Clinical Uncertainty Warning
    end
```

---

## 7. Operations Flow & Runtime State Machine

```mermaid
stateDiagram-v2
    [*] --> IDLE

    IDLE --> ROUTING : Receive Clinical Payload / Query
    
    ROUTING --> PLANNING : Clinical Findings / Differential Query
    ROUTING --> SAFE_ESCALATION : Out-of-Domain / Dangerous Prompt
    
    PLANNING --> VALIDATING_PLAN : Draft AgentPlan
    VALIDATING_PLAN --> EXECUTING_RETRIEVAL : Plan Conforms to Schema
    VALIDATING_PLAN --> PLANNING : Schema Invalid (Auto-Correction)

    EXECUTING_RETRIEVAL --> SUFFICIENCY_GATING : Query Hybrid VDB
    
    SUFFICIENCY_GATING --> DRAFTING : Evidence Threshold Satisfied (Score >= 0.65)
    SUFFICIENCY_GATING --> EXECUTING_RETRIEVAL : Insufficient (Broaden Search Parameters)

    DRAFTING --> TIER0_VALIDATION : Generator Produces Report Draft
    
    TIER0_VALIDATION --> INDEPENDENT_EVALUATION : Passes JSON & Regex Security Filters
    TIER0_VALIDATION --> DRAFTING : Validation Failed (Format Malformed)

    INDEPENDENT_EVALUATION --> POLICY_DECISION : Compute Faithfulness Score & Critique

    state POLICY_DECISION {
        [*] --> CheckVerdict
        CheckVerdict --> AcceptState : Score >= 0.85
        CheckVerdict --> RetryState : Score < 0.85 & Draft < 3
        CheckVerdict --> ExhaustedState : Score < 0.85 & Draft >= 3
    }

    POLICY_DECISION --> POST_APPROVAL_DELIVERY : AcceptState
    POLICY_DECISION --> DRAFTING : RetryState (Feed Critique)
    POLICY_DECISION --> SAFE_ESCALATION : ExhaustedState

    POST_APPROVAL_DELIVERY --> COMPLETED : Render PDF & Dispatch Email
    SAFE_ESCALATION --> COMPLETED : Output Transparent Uncertainty Notice

    COMPLETED --> IDLE : Reset Session & Ready for Next Turn
```

---

## 8. System Use Case Diagrams

```mermaid
graph LR
    %% Actors
    RAD((Radiologist))
    PHY((Attending Physician))
    PAT((Patient))
    ADM((Compliance & Safety Auditor))

    %% System Boundary
    subgraph MEDISCAN_PLATFORM ["MediScan Intelligence System"]
        UC1(["UC-1: Structure Raw CXR Findings"])
        UC2(["UC-2: Multi-Angle Hybrid Evidence Retrieval"])
        UC3(["UC-3: Grounded Clinical Report Generation"])
        UC4(["UC-4: Interactive Multi-Turn Clinical Chat"])
        UC5(["UC-5: Patient-Friendly Explanation & Lifestyle Synthesis"])
        UC6(["UC-6: Automated Clinical PDF Report Compilation"])
        UC7(["UC-7: Encrypted Email Delivery"])
        UC8(["UC-8: Audit Retrieval Provenance & Faithfulness Metrics"])
        UC9(["UC-9: Deterministic Hallucination Guardrail Check"])
    end

    %% Radiologist Interactions
    RAD --> UC1
    RAD --> UC2
    RAD --> UC3
    RAD --> UC6

    %% Attending Physician Interactions
    PHY --> UC4
    PHY --> UC3
    PHY --> UC6
    PHY --> UC7

    %% Patient Interactions
    PAT --> UC5
    PAT --> UC7

    %% Compliance Auditor Interactions
    ADM --> UC8
    ADM --> UC9

    %% Use Case Relationships
    UC1 -.->|"include"| UC2
    UC3 -.->|"include"| UC9
    UC3 -.->|"include"| UC2
    UC6 -.->|"extend"| UC7

    classDef actorStyle fill:#f8fafc,stroke:#334155,stroke-width:2px;
    classDef ucStyle fill:#f0fdf4,stroke:#16a34a,stroke-width:1.5px;
    class RAD,PHY,PAT,ADM actorStyle;
    class UC1,UC2,UC3,UC4,UC5,UC6,UC7,UC8,UC9 ucStyle;
```

---

## 9. User Story Mapping & Requirements Hierarchy

```mermaid
mindmap
  root((MediScan Clinical Epics))
    Epic 1: Structured Findings Ingestion
      US-1.1: Radiologist uploads unstructured CV model findings
        Criteria: Extract positive and negative findings into typed Pydantic models
      US-1.2: Automatic Missing Information Flagging
        Criteria: Detect missing patient history or imaging view details
    Epic 2: Evidence-Grounded Hybrid Retrieval
      US-2.1: Dual Dense-Sparse Knowledge Retrieval
        Criteria: Query ChromaDB + BM25 and fuse using Reciprocal Rank Fusion (k=60)
      US-2.2: Cross-Encoder Precision Reranking
        Criteria: Filter top candidates via NVIDIA Reranker with score thresholding
      US-2.3: Retrieval Sufficiency Gating
        Criteria: Deterministic stop when evidence does not support diagnosis
    Epic 3: Hallucination-Free Clinical Synthesis
      US-3.1: Zero-Hallucination Report Writing
        Criteria: Every claim mapped to chunk ID and citation index
      US-3.2: Independent Dual-LLM Quality Audit
        Criteria: Dispassionate evaluation of faithfulness before delivery
      US-3.3: Bounded Recovery Loop
        Criteria: Auto-correct up to 3 times before graceful fallback
    Epic 4: Automated Delivery & Multi-Modal Output
      US-4.1: Standardized PDF Report Compilation
        Criteria: Formatted tables, evidence citations, and hospital branding
      US-4.2: Automated Clinician Email Dispatch
        Criteria: OAuth2 SMTP dispatch with PDF attachment
```

---

## 10. Core Safety & Clinical Guardrail Principles

```mermaid
graph TD
    G1["1. NO Direct LLM Tool Calls<br/>LLMs never execute code; Python controls all API calls"]
    G2["2. Full Provenance Tracking<br/>Every claim maps to Chunk ID, Section, and Source"]
    G3["3. Deterministic Policy Decisions<br/>Acceptance/recovery decisions made by code, not LLM"]
    G4["4. Bounded Recovery Loop<br/>Max 3 iterations before guaranteed safe fallback"]
    G5["5. Safe Fallback on Uncertainty<br/>Pipeline explicitly admits insufficient evidence"]

    G1 --- G2 --- G3 --- G4 --- G5

    classDef guardStyle fill:#fff1f2,stroke:#e11d48,stroke-width:2px,color:#9f1239;
    class G1,G2,G3,G4,G5 guardStyle;
```

---

## 11. Data Sources & Storage Layout

```mermaid
graph LR
    subgraph INGESTED_DATA ["Knowledge Base Repositories"]
        D_OPENI["OpenI CXR Reports<br/>(Indiana University XML collection)"]
        D_GUIDE["Clinical Guidelines<br/>(Cardiology, Pulmonology, Radiology)"]
        D_REF["Clinical Reference Material<br/>(Gold-standard medical literature)"]
        D_PAT["Patient Education Material<br/>(Lifestyle, nutrition, discharge guidance)"]
    end

    subgraph STORAGE_TIER ["Persistent Storage"]
        ST_CHROMA[("ChromaDB Vector Store<br/>vectorstore/chromadb")]
        ST_BM25[("BM25 Serialized Index<br/>vectorstore/bm25_index.pkl")]
        ST_REG[("Source Registry CSV<br/>data/registry/source_registry.csv")]
    end

    INGESTED_DATA ==> STORAGE_TIER

    classDef dataBox fill:#f8fafc,stroke:#475569,stroke-width:1.5px;
    class D_OPENI,D_GUIDE,D_REF,D_PAT,ST_CHROMA,ST_BM25,ST_REG dataBox;
```

---

## 12. Technology Stack

```mermaid
graph TD
    subgraph CORE ["Core Intelligence & Models"]
        M1["NVIDIA NIM Embeddings<br/>nv-embedqa-e5-v5 (1024 dims)"]
        M2["NVIDIA NIM Reranker<br/>nv-rerankqa-mistral-4b"]
        M3["NVIDIA Nemotron / Llama-3.1-70B<br/>Clinical Reasoning & Planning"]
        M4["DeepSeek-V4 Flash / Nemotron<br/>Independent Quality Evaluator"]
    end

    subgraph DATA_ENGINE ["Storage & Retrieval Engine"]
        D1["ChromaDB<br/>(Persistent Vector Database)"]
        D2["Rank-BM25<br/>(Sparse Lexical Search)"]
        D3["LangChain Community<br/>(RAG Orchestration & Loaders)"]
    end

    subgraph BACKEND_FRAMEWORK ["Backend & Delivery Services"]
        B1["FastAPI<br/>(High-Performance Async REST API)"]
        B2["Pydantic v2<br/>(Deterministic Type Schemas)"]
        B3["ReportLab<br/>(Clinical PDF Generation Engine)"]
        B4["Google API / SMTP<br/>(Automated Secure Email Dispatch)"]
    end

    CORE --- DATA_ENGINE --- BACKEND_FRAMEWORK

    classDef coreStyle fill:#eff6ff,stroke:#3b82f6,stroke-width:2px;
    classDef dataStyle fill:#f0fdf4,stroke:#22c55e,stroke-width:2px;
    classDef beStyle fill:#faf5ff,stroke:#a855f7,stroke-width:2px;
    class M1,M2,M3,M4 coreStyle;
    class D1,D2,D3 dataStyle;
    class B1,B2,B3,B4 beStyle;
```

---

<div align="center">
  <sub>Built with precision, safety, and deterministic evidence-grounding for clinical decision support.</sub>
</div>
