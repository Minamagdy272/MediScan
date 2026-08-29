/**
 * TypeScript Data Models for MediScan Angular App.
 */

export interface EvidenceRecord {
  evidence_id: string;
  chunk_id: string;
  source_id: string;
  source_title: string;
  source_type: string;
  content: string;
  score: number;
  rank: number;
  expanded?: boolean;
}

export interface AgentPlan {
  intent: string;
  retrieval_mode: string;
  queries: string[];
  tools: string[];
  needs_evidence: boolean;
  needs_guideline: boolean;
  needs_history: boolean;
  response_type: string;
  reason: string;
}

export interface ExtractedMedicalInfo {
  symptoms: string[];
  imaging_findings: string[];
  positive_findings: string[];
  negative_findings: string[];
  patient_information: string[];
  missing_information: string[];
}

export interface RouterDecision {
  query_type: string;
  language: string;
  complexity: string;
  suggested_retrieval_mode: string;
}

export interface PipelineStageEvent {
  stage: string;
  message: string;
  attempt?: number;
  action?: string;
  findings?: ExtractedMedicalInfo;
  router?: RouterDecision;
  plan?: AgentPlan;
  evidence_count?: number;
  evidence?: EvidenceRecord[];
  groundedness?: number;
  safety?: number;
  tier0_valid?: boolean;
  error?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  status?: 'processing' | 'done' | 'error';
  stages?: PipelineStageEvent[];
  currentStageMessage?: string;
  plan?: AgentPlan;
  final_action?: 'ACCEPT' | 'REGENERATE' | 'RE_RETRIEVE' | 'ESCALATE' | string;
  attempts_made?: number;
  evidence_used?: EvidenceRecord[];
  pdf_download_url?: string;
  pdf_filename?: string;
  email_sent?: boolean;
  email_status?: string;
  attachmentName?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  updatedAt: Date;
}
