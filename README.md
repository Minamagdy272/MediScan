# 🫁 MediScan: Evidence-Grounded Agentic AI for Clinical Intelligence

> **An Enterprise-Grade, 13-Stage Agentic RAG Platform with Deterministic Guardrails for Medical Intelligence, Radiology Analysis, and Automated Clinical Delivery.**

---

<div align="center">
  <img src="assets/mediscan_architecture.png" alt="MediScan System Architecture" width="100%" />
</div>

---

## 📑 Visual Architecture & Flow Index

1. [High-Level System Architecture](#1-high-level-system-architecture)
2. [Architectural Flow (Tier 1 & Tier 2)](#2-architectural-flow)
3. [Clinical Work Flow (End-to-End Execution Lifecycle)](#3-clinical-work-flow)
4. [Operations Flow & State Machine (Bounded Recovery Loop)](#4-operations-flow--recovery-state-machine)
5. [Use Case Diagrams](#5-system-use-case-diagrams)
6. [User Story Mapping & Requirements Flow](#6-user-story-mapping--requirements-flow)
7. [Technology Stack](#7-technology-stack)

---

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph KNOWLEDGE_SOURCES ["📚 Multi-Source Clinical Knowledge Base"]
        direction LR
        S1["Cleaned Medical Docs"] ~~~ S2["OpenI CXR Reports (XML)"] ~~~ S3["Clinical Guidelines"] ~~~ S4["Web Medical Sources"] ~~~ S5["Patient Education"]
    end

    subgraph TIER1 ["🟢 TIER 1: Frozen VDB & Deterministic Hybrid RAG Engine"]
        direction TB
        ACQ["Acquisition & Ingestion"] --> CLEAN["Medical Cleaner & De-Identification"]
        CLEAN --> PARSE["Clinical Section Parser<br/>(Findings, Impression, History)"]
        PARSE --> CHUNK["Section-Aware Overlap Chunker"]
        CHUNK --> EMB["NVIDIA NIM Embeddings<br/>(nv-embedqa-e5-v5 / 1024 dims)"]
        EMB --> DUAL_IDX["Dual Index Construction"]
        DUAL_IDX --> DENSE_DB[("ChromaDB Vector Store")]
        DUAL_IDX --> SPARSE_DB[("BM25 Keyword Index")]
        
        DENSE_DB & SPARSE_DB --> RETRIEVE["Dual Retrieval (Top-N)"]
        RETRIEVE --> RRF["Hybrid Fusion (RRF Algorithm)"]
        RRF --> RERANK["NVIDIA NIM Reranker<br/>(nv-rerankqa-mistral-4b Cross-Encoder)"]
        RERANK --> SELECTOR["Evidence Selector & Deduplication"]
        SELECTOR --> SUFF_GATE["Sufficiency Gate (Score & Diversity Check)"]
        SUFF_GATE --> RETRIEVER_API[["MediScanRetriever.retrieve() Stable API"]]
    end

    subgraph TIER2 ["🟣 TIER 2: 13-Stage Agentic Pipeline with Deterministic Guardrails"]
        direction TB
        U_IN["👤 User Input<br/>(Natural Language / CXR Report)"] --> ST1["1. Router (Intent & Complexity)"]
        ST1 --> ST2["2. Planner LLM (AgentPlan Draft)"]
        ST2 --> ST3["3. Plan Validator (Deterministic Python)"]
        ST3 --> ST4["4. Deterministic Executor (Python Controlled)"]
        ST4 --> ST5["5. Call MediScan RAG API (Tier 1 Black Box)"]
        ST5 --> ST6["6. Evidence Selection (Top-K Chunks + Provenance)"]
        ST6 --> ST7["7. Sufficiency Gate (Threshold & Coverage Check)"]
        ST7 --> ST8["8. Clinical Generator LLM (Evidence-Grounded Draft)"]
        ST8 --> ST9["9. Tier-0 Validation (JSON, Schema, Safety Filters)"]
        ST9 --> ST10["10. Independent Evaluator LLM (Faithfulness Scoring)"]
        ST10 --> ST11["11. Deterministic Policy Engine (Accept / Loop / Fallback)"]
        
        ST11 -->|REGENERATE / RE-RETRIEVE| LOOP{"Bounded Recovery Loop<br/>(Max 3 Drafts)"}
        LOOP -.->|Draft Retry| ST8
        LOOP -.->|Broaden Query| ST5
        
        ST11 -->|ACCEPT| ST13["13. Post-Approval Delivery"]
        LOOP -->|ESCALATE (Exhausted)| ESCALATE["Safe Uncertainty Fallback"]
        ESCALATE --> ST13
    end

    subgraph OUTPUTS ["🚀 Verified Multi-Modal Outputs"]
        direction LR
        ST13 --> O1["🩺 Evidence-Grounded Answer"]
        ST13 --> O2["📎 Verifiable Citations (Chunk IDs & Sources)"]
        ST13 --> O3["📄 Branded PDF Clinical Report"]
        ST13 --> O4["✉️ Secure Automated Email Delivery"]
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

## 2. Architectural Flow

```mermaid
flowchart TD
    %% INGESTION FLOW
    subgraph INGESTION ["📥 Ingestion & Dual Indexing Pipeline (Tier 1)"]
        D1["Raw Clinical Data Sources<br/>(XML / PDF / Articles)"] --> D2["Normalization & De-identification"]
        D2 --> D3["Clinical Section Extractor"]
        D3 --> D4["Section-Aware Chunking (Overlap = 15%)"]
        D4 --> D5["NVIDIA Embedding Engine (1024-dim)"]
        D5 --> D6A["Dense Indexing (ChromaDB)"]
        D4 --> D6B["Sparse Tokenizer Indexing (BM25)"]
    end

    %% HYBRID RETRIEVAL FLOW
    subgraph HYBRID_RETRIEVAL ["🔍 Hybrid Retrieval & Reranking Subsystem"]
        Q["Extracted Clinical Retrieval Query"] --> QA["Dense Semantic Search (Cosine)"]
        Q --> QB["Sparse Keyword Search (BM25)"]
        QA -->|Top 25 Dense| FUSION["Reciprocal Rank Fusion (RRF)"]
        QB -->|Top 25 Sparse| FUSION
        FUSION -->|Top 15 Fused Chunks| RERANKER["NVIDIA Cross-Encoder Reranker"]
        RERANKER -->|Top 5 High-Scoring Chunks| DEDUP["Deduplication & Diversity Gate"]
        DEDUP --> EV_OUT["Verified Evidence Bundle + Scores"]
    end

    %% ORCHESTRATION FLOW
    subgraph AGENT_CONTROL ["🛡️ Agentic Reasoning & Guardrail Flow (Tier 2)"]
        USER_QUERY["Clinician Input"] --> ROUTER{"Intent Router"}
        ROUTER -->|Medical / CXR Finding| PLANNER["LLM Plan Generation"]
        ROUTER -->|Conversational / Out-of-Domain| DIRECT_ROUTE["Deterministic Guardrail Handler"]
        
        PLANNER --> PLAN_VAL["Deterministic Python Plan Validator"]
        PLAN_VAL -->|Valid Plan| EXEC["Deterministic Step Executor"]
        PLAN_VAL -->|Invalid Schema| PLAN_FIX["Plan Auto-Correction"]
        PLAN_FIX --> EXEC
        
        EXEC --> HYBRID_RETRIEVAL
        EV_OUT --> SUFF_CHECK{"Retrieval Sufficiency Threshold met?"}
        SUFF_CHECK -->|Yes| GEN_DRAFT["Evidence-Grounded Report Generator"]
        SUFF_CHECK -->|No| QUERY_RETRY["Query Expansion / Soft Fallback"]
        
        GEN_DRAFT --> TIER0_VAL["Tier-0 Syntax & Guardrail Verification"]
        TIER0_VAL --> EVALUATOR["Independent LLM Evaluator (Critique)"]
        EVALUATOR --> POLICY{"Deterministic Policy Engine"}
        
        POLICY -->|Passed (Score >= 0.85)| ACCEPTED["Approved Clinical Response"]
        POLICY -->|Failed & Retries < 3| REGEN["Controlled Regeneration"]
        POLICY -->|Failed & Retries >= 3| SAFE_FAIL["Safe Clinical Escalation Notice"]
        
        REGEN --> GEN_DRAFT
    end

    D6A & D6B -.-> QA & QB
    ACCEPTED & SAFE_FAIL --> DISPATCH["PDF Rendering Engine & SMTP Service"]

    classDef stageBox fill:#ffffff,stroke:#3b82f6,stroke-width:1.5px;
    class D1,D2,D3,D4,D5,D6A,D6B,QA,QB,FUSION,RERANKER,DEDUP,ROUTER,PLANNER,PLAN_VAL,EXEC,GEN_DRAFT,TIER0_VAL,EVALUATOR,POLICY stageBox;
```

---

## 3. Clinical Work Flow

```mermaid
sequenceDiagram
    autonumber
    actor Clinician as 🩺 Clinician / Radiologist
    participant Gateway as 🌐 FastAPI Gateway / Orchestrator
    participant Router as 🧭 Intent Router
    participant Planner as 🧠 Planner & Validator
    participant Tier1 as 🟢 Tier 1 Hybrid VDB
    participant Generator as ✍️ Generator LLM
    participant Evaluator as ⚖️ Independent Evaluator
    participant Policy as 🛡️ Deterministic Policy Engine
    participant Delivery as 📨 PDF & Delivery Service

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

## 4. Operations Flow & Recovery State Machine

```mermaid
stateDiagram-v2
    [*] --> IDLE

    IDLE --> ROUTING : Receive Clinical Payload / Query
    
    ROUTING --> PLANNING : Clinical Findings / Differential Query
    ROUTING --> SAFE_ESCALATION : Out-of-Domain / Dangerous Prompt
    
    PLANNING --> VALIDATING_PLAN : Draft AgentPlan
    VALIDATING_PLAN --> EXECUTING_RETRIEVAL : Plan Conforms to Schema
    VALIDATING_PLAN --> PLANNING : Schema Invalid (Retry Plan)

    EXECUTING_RETRIEVAL --> SUFFICIENCY_GATING : Query Hybrid VDB
    
    SUFFICIENCY_GATING --> DRAFTING : Evidence Threshold Satisfied
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

## 5. System Use Case Diagrams

```mermaid
graph LR
    %% Actors
    RAD((👨‍⚕️ Radiologist))
    PHY((🩺 Attending Physician))
    PAT((👤 Patient))
    ADM((🛡️ Compliance & Safety Auditor))

    %% System Boundary
    subgraph MEDISCAN_PLATFORM ["🏥 MediScan Intelligence System"]
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
    UC1 -.->|<<include>>| UC2
    UC3 -.->|<<include>>| UC9
    UC3 -.->|<<include>>| UC2
    UC6 -.->|<<extend>>| UC7

    classDef actorStyle fill:#f8fafc,stroke:#334155,stroke-width:2px;
    classDef ucStyle fill:#f0fdf4,stroke:#16a34a,stroke-width:1.5px;
    class RAD,PHY,PAT,ADM actorStyle;
    class UC1,UC2,UC3,UC4,UC5,UC6,UC7,UC8,UC9 ucStyle;
```

---

## 6. User Story Mapping & Requirements Flow

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
        Criteria: Query ChromaDB + BM25 and fuse using Reciprocal Rank Fusion
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

## 7. Technology Stack

```mermaid
graph TD
    subgraph CORE ["⚡ Core Intelligence & Models"]
        M1["NVIDIA NIM Embeddings<br/>nv-embedqa-e5-v5 (1024 dims)"]
        M2["NVIDIA NIM Reranker<br/>nv-rerankqa-mistral-4b"]
        M3["NVIDIA Nemotron / Llama-3.1-70B<br/>Clinical Reasoning & Generation"]
    end

    subgraph DATA_ENGINE ["💾 Storage & Retrieval Engine"]
        D1["ChromaDB<br/>(Vector Store)"]
        D2["Rank-BM25<br/>(Sparse Lexical Search)"]
        D3["LangChain Community<br/>(RAG Orchestration)"]
    end

    subgraph BACKEND_FRAMEWORK ["⚙️ Backend & Pipeline Services"]
        B1["FastAPI<br/>(High-Performance REST API)"]
        B2["Pydantic v2<br/>(Deterministic Type Schemas)"]
        B3["ReportLab<br/>(Clinical PDF Generation Engine)"]
        B4["Google API / SMTP<br/>(Automated Email Dispatch)"]
    end

    CORE --- DATA_ENGINE --- BACKEND_FRAMEWORK

    classDef coreStyle fill:#eff6ff,stroke:#3b82f6,stroke-width:2px;
    classDef dataStyle fill:#f0fdf4,stroke:#22c55e,stroke-width:2px;
    classDef beStyle fill:#faf5ff,stroke:#a855f7,stroke-width:2px;
    class M1,M2,M3 coreStyle;
    class D1,D2,D3 dataStyle;
    class B1,B2,B3,B4 beStyle;
```

---

<div align="center">
  <sub>Built for precision, safety, and evidence-grounded clinical decision support.</sub>
</div>
