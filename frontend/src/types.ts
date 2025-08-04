/* Shared wire-format types. Keep in sync with backend/app/models.py */

export type EventName =
  | "router_decision"
  | "record_done"
  | "expert_chunk"
  | "expert_done"
  | "final_summary"
  | "error";

export interface SseEnvelope {
  event: EventName;
  thread_id: string;
  seq: number;
  timestamp: string; // ISO-8601 from backend
  payload: Record<string, any>;
}

// Payload Types for specific events
export interface RouterDecisionPayload {
  selected_experts: string[];
  reasoning: string;
  total_records?: number; // Total number of records to be processed
}

export interface ExpertChunkPayload {
  expert_id: string;
  expert_type: string;
  chunk: string;
  is_complete: boolean;
}

export interface RecordDonePayload {
  kind: string; // "host" or "cert"
  id: string; // host.ip or cert.fingerprint_sha256
  summary: string;
}

export interface ExpertDonePayload {
  expert_id: string;
  expert_type: string;
  summary: string;
  confidence: number;
  processing_time_ms: number;
}

export interface FinalSummaryPayload {
  summary: string;
  expert_count: number;
  total_processing_time_ms: number;
}

export interface ErrorPayload {
  error_code: string;
  message: string;
  details?: string;
  expert_id?: string;
  error_type?: string; // Keep for backward compatibility
}

// Expert Types
export type ExpertType = "host" | "cert" | "service" | "metadata";

// UI State Types
export interface ExpertPanelState {
  expert_id: string;
  expert_type: ExpertType;
  status: "idle" | "processing" | "completed" | "error";
  chunks: string[];
  final_summary?: string;
  confidence?: number;
  processing_time_ms?: number;
  error_message?: string;
}

export interface ConversationMessage {
  id: string;
  thread_id: string;
  type: "user" | "system" | "expert" | "final";
  content: string;
  timestamp: string;
  expert_type?: ExpertType;
  expert_id?: string;
  metadata?: Record<string, any>;
}

export interface ConversationState {
  thread_id?: string;
  status: "idle" | "streaming" | "completed" | "error";
  messages: ConversationMessage[];
  expert_panels: Record<string, ExpertPanelState>;
  final_summary?: string;
  router_decision?: string[];
  current_sequence: number;
  errors: string[];
  start_time?: string;
  total_processing_time?: number;
  // New fields for record-based progress tracking
  totalRecords: number | null;
  processedRecords: number;
  recordSummaries: Record<string, { kind: "host" | "cert"; summary: string }>;
  analysisDone: boolean;
}

// Expert Configuration
export interface ExpertConfig {
  id: string;
  type: ExpertType;
  name: string;
  description: string;
  color: string;
  icon: string;
}

// Default expert configurations for UI
export const DEFAULT_EXPERT_CONFIGS: ExpertConfig[] = [
  {
    id: "host_fan", // Match backend fan-out nodes
    type: "host",
    name: "Host Infrastructure Expert",
    description:
      "Host analysis including location, services, and security assessment",
    color: "#52c41a",
    icon: "🖥️",
  },
  {
    id: "cert_fan", // Match backend fan-out nodes
    type: "cert",
    name: "Certificate Security Expert",
    description: "TLS certificate and cryptographic security analysis",
    color: "#1890ff",
    icon: "🔐",
  },
  {
    id: "service",
    type: "service",
    name: "Service Expert",
    description: "Running services and software analysis",
    color: "#722ed1",
    icon: "⚙️",
  },
];
