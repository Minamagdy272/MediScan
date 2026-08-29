# MediScan Chatbot UI Adaptation Specification

> **Purpose:** Define the presentation and interaction layer for MediScan as a simple, professional, chatbot-first application.
>
> **Architecture boundary:** The UI sits above the existing controlled MediScan Agentic RAG pipeline. It must not change retrieval, evaluation, safety, policy, or delivery behavior.
>
> **Edit policy:** Future chatbot UI, UX, layout, component, and visual-workflow changes should be made in this file only. Changes to the underlying RAG/agent architecture belong in the core architecture documentation.

---

# 1. Product Direction

MediScan should look and behave like a **focused medical AI chatbot**, not a dashboard, admin portal, or generic enterprise application.

The main user experience is one conversation screen where a user can:

- ask a clinical or educational question;
- upload supported findings/documents when relevant;
- receive a grounded MediScan answer;
- inspect evidence and citations attached to the answer;
- see lightweight processing status while the pipeline runs;
- generate/download an approved PDF report;
- explicitly request email delivery of an approved report.

The UI should remain intentionally simple. Do not introduce login, registration, user profiles, roles, analytics dashboards, admin pages, or cloud account workflows in the local prototype.

---

# 2. Implementation Direction

## Frontend

Use:

```text
Angular
```

## Backend

Use:

```text
FastAPI
```

FastAPI is the application/API boundary for the MediScan Python pipeline.

## Data for the current prototype

Keep development data local:

```text
MediScan/
├── frontend/
│   └── angular/
├── backend/
│   └── fastapi/
├── notebooks/
├── data/
├── vectorstore/
├── outputs/
│   └── reports/
└── feedback/
```

Do not require MongoDB for the first local prototype unless persistence becomes necessary.

Do not add Express merely to satisfy the traditional MEAN acronym. FastAPI is the backend used by the AI pipeline.

The notebooks remain the research/validation environment. The frontend must call FastAPI instead of importing or duplicating notebook UI logic.

---

# 3. Core UI Architecture

```text
Angular Chat UI
      │
      │ HTTP / SSE
      ▼
FastAPI API
      │
      ▼
MediScan Pipeline
      ├── Structured Extraction
      ├── Nemotron Router
      ├── GLM-5.3 Planner
      ├── Retrieval / Reranking
      ├── Report Generation
      ├── Tier 0 Validation
      ├── DeepSeek Evaluation
      └── Controlled Policy Action
             │
             ├── ACCEPT
             ├── REGENERATE
             ├── RE_RETRIEVE
             └── ESCALATE
```

The UI is a presentation layer. It must not imply an unrestricted autonomous multi-agent system.

---

# 4. Visual Identity

## Logo

Use the provided **MediScan logo** as the primary brand mark.

Recommended asset location in the Angular project:

```text
frontend/angular/src/assets/mediscan-logo.png
```

Use the supplied logo without redesigning it. Preserve its proportions and keep enough whitespace around it.

## Color Direction

The visual language should be derived from the logo:

```text
Primary Blue:        #1464C0
Deep Blue:           #0B4F9C
Logo Cyan:           #48BBD8
Light Cyan:          #EAF8FC
Soft Blue Surface:   #F4F9FD
Main Background:     #FFFFFF
Text:                #172033
Muted Text:          #667085
Borders:             #DCE6F0
Success State:       restrained green
Warning State:       restrained amber
Error State:         restrained red
```

Use blue/cyan as accents rather than filling the entire interface with strong color.

The interface should feel:

- clinical;
- calm;
- modern;
- lightweight;
- trustworthy;
- minimal.

Avoid gradients, glassmorphism, excessive shadows, neon effects, and decorative medical imagery.

---

# 5. Overall Chatbot Layout

The main application should be a simple two-area layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ MediScan logo / name                            New Chat     │
├─────────────────┬────────────────────────────────────────────┤
│                 │                                            │
│ Recent Chats    │              Chat Conversation             │
│                 │                                            │
│ Today           │  MediScan                                   │
│ • Pleural ...   │  Evidence-grounded medical assistant       │
│ • Chest X-ray   │                                            │
│                 │  User message                               │
│ Yesterday       │                         ┌────────────────┐  │
│ • ...           │                         │ ...            │  │
│                 │                         └────────────────┘  │
│                 │                                            │
│                 │  MediScan response                          │
│                 │  ...                                       │
│                 │                                            │
│                 │  [Evidence] [Sources] [Report]             │
│                 │                                            │
│                 │ ┌────────────────────────────────────────┐ │
│                 │ │ Ask MediScan...                        │ │
│                 │ │                                        │ │
│                 │ │ 📎 Attach                    Send  ↑   │ │
│                 │ └────────────────────────────────────────┘ │
└─────────────────┴────────────────────────────────────────────┘
```

The chat should remain the dominant visual element.

The sidebar is optional and compact. It may contain local recent conversations only.

No separate dashboard homepage is required.

---

# 6. Header

Keep the top bar minimal.

Recommended:

```text
[ MediScan Logo ]
MediScan
Evidence-Grounded Medical AI

                              [ + New Chat ]
```

Do not include:

- login/profile controls;
- notifications;
- admin controls;
- complex navigation menus;
- product-management UI.

---

# 7. Empty State

When the user opens a new chat, show a simple welcoming state.

Example:

```text
                    [ MediScan Logo ]

                    How can I help?

        Ask a medical question or upload findings
        for an evidence-grounded analysis.

   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ Explain a  │  │ Analyze my │  │ Compare    │
   │ condition  │  │ findings   │  │ findings   │
   └────────────┘  └────────────┘  └────────────┘

             [ Ask MediScan something... ]
```

Suggested prompts are only shortcuts. Do not make them mandatory.

---

# 8. Composer

The composer should feel familiar to modern AI chat applications.

Required controls:

```text
[ + / Attach ]
[ Clinical question input........................ ]
[ Send ]
```

Supported local interactions may include:

- text question;
- findings/document upload;
- optional image upload only when the backend CV/image pipeline is actually connected.

Do not expose X-ray/image analysis as a fake capability.

The composer should disable conflicting actions while a request is actively running.

---

# 9. User Message

Use a clean user bubble or compact aligned message.

Keep it visually subordinate to the assistant response.

Attachments should appear as small file cards above or inside the user message.

Example:

```text
You
What are the radiographic findings of pleural effusion?
```

---

# 10. Assistant Response

The assistant response is the primary content area.

Use readable typography and generous line spacing.

Recommended response structure:

```text
MediScan

Answer text...

Key findings
• ...
• ...

[EV-001]   [EV-002]

────────────────────────────
Evidence-grounded response
```

Do not overwhelm the default view with debug information.

---

# 11. Evidence and Citation Presentation

Evidence should be available without turning the UI into a dashboard.

Use compact expandable cards beneath the answer.

Example:

```text
Evidence used  3

┌─────────────────────────────────────────────┐
│ [EV-001]  Pleural Effusion                  │
│ Source: Radiology Reference                 │
│ Type: Educational                           │
│ Score: 0.91                                 │
│                              View evidence ▾ │
└─────────────────────────────────────────────┘
```

The expanded card may show the relevant retrieved passage and provenance metadata.

The UI must make the relationship visible:

```text
Retrieved Evidence
       ↓
Citation ID
       ↓
Generated Answer
```

Do not display evidence as if it were generated text.

---

# 12. Processing State

The chatbot should provide a compact processing indicator while the backend runs.

Example:

```text
MediScan is analyzing...

✓ Understanding the request
✓ Planning retrieval
✓ Retrieving evidence
✓ Checking evidence sufficiency
⟳ Generating response
○ Evaluating response
```

The exact visible stages must come from real backend events.

Never mark a stage complete merely because the UI expects it to be complete.

The underlying controlled flow is:

```text
Input
  ↓
Structured Extraction
  ↓
Query Planning
  ↓
Evidence Retrieval
  ↓
Evidence Sufficiency Check
  ↓
Report Generation
  ↓
Tier 0 Validation
  ↓
Structured Evaluation
  ↓
Policy Action
```

---

# 13. Safety and Error States

Safety states should appear naturally in the conversation.

## Insufficient Evidence

```text
MediScan could not find sufficient evidence to provide a
reliable evidence-grounded interpretation.

Please seek review from a qualified clinician.
```

## Escalated

```text
This request could not be safely completed by MediScan.

Clinical review is recommended.
```

## Evaluator Unavailable

Do not present an approved-looking answer.

Clearly state that the system could not complete verified evaluation.

## Technical Failure

Show a concise non-technical message to the user, with a small expandable technical detail section for local development.

---

# 14. Report / PDF Actions

PDF actions belong inside the chat result, not in a separate report dashboard.

For an accepted answer:

```text
[ Generate PDF ]
```

After generation:

```text
PDF ready
[ Preview ]   [ Download ]
```

PDF generation must remain controlled and should occur only for an accepted report.

Rejected, escalated, insufficient-evidence, or evaluator-unavailable outputs must not be offered as approved PDF reports.

---

# 15. Email Action

Email delivery remains explicitly opt-in.

Place it next to the approved report action:

```text
PDF ready

[ Download PDF ]   [ Email Report ]
```

If the user chooses email:

```text
Send approved report

Recipient email
[________________________]

[ Cancel ]   [ Send ]
```

The UI must clearly show success/failure after the FastAPI response.

Never use a hard-coded recipient.

Never allow email delivery for a non-approved response.

---

# 16. Clinical Report Content

The chatbot response/report may contain the following structured sections when relevant:

```text
Clinical Summary
Symptoms
Imaging Findings
Positive Findings
Negative Findings
Possible Explanations
Lifestyle & Relevant Risk Factors
Uncertainty & Limitations
Evidence Citations
Safety Disclaimer
```

The UI does not need to show all sections as separate dashboard cards. The report should primarily remain readable as a conversational clinical response.

`Possible Explanations` may contain model reasoning based on the supplied case and retrieved evidence, but must remain explicitly framed as possibilities rather than confirmed patient facts.

`Lifestyle & Relevant Risk Factors` must not fabricate undocumented lifestyle information. Missing information should be shown as not documented.

---

# 17. Local Conversation History

The first prototype may keep recent conversation sessions locally.

Suggested sidebar:

```text
Recent Chats

Today
• Pleural effusion
• Chest X-ray findings

Yesterday
• Follow-up comparison
```

No login is required.

No cloud account is required.

No clinical patient-record system is implied.

A future persistence layer may replace local memory without changing the chatbot UI contract.

---

# 18. Minimal Navigation

Use only:

```text
MediScan

[ + New Chat ]

Recent Chats
```

Avoid separate pages for:

- Evaluation Dashboard;
- System Architecture;
- Admin;
- Users;
- Authentication;
- Settings-heavy control panels.

Technical pipeline details may appear inside an optional expandable `Details` section when useful for demonstrations.

---

# 19. API / Frontend Contract

The Angular frontend should consume a structured FastAPI result.

Conceptual response:

```text
MediScanResult
├── status
├── message
├── extracted_findings
├── selected_evidence
├── citations
├── tier0_result
├── evaluation_verdict
├── action
├── attempts
├── pdf_path
└── delivery_status
```

The frontend must never depend on raw notebook print statements.

Suggested API surface:

```text
POST /api/chat
POST /api/chat/stream
POST /api/upload
GET  /api/chats
GET  /api/chats/{session_id}
POST /api/reports/{session_id}/generate
POST /api/reports/{session_id}/email
GET  /api/health
```

The exact implementation can evolve, but the UI contract should remain structured.

---

# 20. Streaming Behavior

Prefer Server-Sent Events for the chatbot processing stream when practical.

Suggested events:

```text
analysis_started
extraction_completed
planning_completed
retrieval_completed
sufficiency_completed
generation_started
evaluation_started
evaluation_completed
policy_completed
report_ready
delivery_completed
```

The UI should progressively update the current assistant message rather than creating a separate page for each stage.

---

# 21. Responsive Design

Desktop is the primary target.

The layout should still adapt cleanly to tablet/mobile widths.

Desktop:

```text
Sidebar 260–280px
Chat area fills remaining width
Composer centered with readable max-width
```

Mobile:

```text
Sidebar collapses
Chat becomes full width
Composer remains fixed to the bottom
```

---

# 22. Typography

Use a clean modern sans-serif typography system.

Recommended hierarchy:

```text
App title:       20–24px
Section title:   16–18px
Body:            15–16px
Metadata:        12–13px
```

Do not use oversized marketing typography.

The product should look like a focused clinical assistant rather than a landing page.

---

# 23. Component Principles

Prefer a small component system:

```text
AppShell
ChatSidebar
ChatHeader
ChatMessage
AssistantMessage
AttachmentCard
ProcessingStatus
EvidenceCard
CitationChip
ReportActions
EmailDialog
Composer
EmptyState
SafetyNotice
```

Keep components reusable but do not over-engineer the first prototype.

---

# 24. What the UI Must NOT Do

The first chatbot prototype must not:

- implement authentication;
- require user registration;
- expose roles/permissions;
- fabricate evaluation metrics;
- expose unsupported image analysis;
- present rejected drafts as approved;
- hide insufficient-evidence states;
- hide evaluator failures;
- invent patient information;
- duplicate the RAG pipeline in Angular;
- replace FastAPI with a second backend layer.

---

# 25. Final UX Principle

MediScan should feel like:

```text
Simple chatbot
       ↓
Professional medical answer
       ↓
Evidence when needed
       ↓
Clear safety state
       ↓
Approved report actions
```

Not:

```text
Dashboard
  ├── Agents
  ├── Metrics
  ├── Analytics
  ├── Architecture
  ├── Users
  └── Reports
```

The interface should make the controlled Agentic RAG system feel simple to the user while preserving the underlying safety and evidence workflow.

---

# 26. Visual Reference

The desired visual simplicity is inspired by the provided reference screenshot:

- mostly white canvas;
- compact left navigation/history;
- large central conversation area;
- one dominant rounded composer;
- subtle borders;
- minimal shadows;
- clear blue accent color;
- very limited decorative UI.

The MediScan logo supplied for this project is the primary visual anchor and should replace generic branding.
