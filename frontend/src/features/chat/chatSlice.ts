/**
 * Redux Toolkit slice for chat/conversation state management.
 * Handles SSE events and expert panel state updates.
 */

import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { v4 as uuidv4 } from "uuid";
import {
  ConversationState,
  SseEnvelope,
  RouterDecisionPayload,
  RecordDonePayload,
  ExpertChunkPayload,
  ExpertDonePayload,
  FinalSummaryPayload,
  ErrorPayload,
  DEFAULT_EXPERT_CONFIGS,
} from "../../types";

// Initial state
const initialState: ConversationState = {
  status: "idle",
  messages: [],
  expert_panels: {},
  current_sequence: 0,
  errors: [],
  totalRecords: null,
  processedRecords: 0,
  recordSummaries: {},
  analysisDone: false,
};

// Helper function to get expert config
const getExpertConfig = (expertId: string) => {
  return (
    DEFAULT_EXPERT_CONFIGS.find((config) => config.id === expertId) || {
      id: expertId,
      type: "service" as const,
      name: expertId,
      description: "Unknown expert",
      color: "#666666",
      icon: "❓",
    }
  );
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    // Initialize a new conversation
    startConversation: (
      state,
      action: PayloadAction<{ threadId: string; message: string }>,
    ) => {
      const { threadId, message } = action.payload;

      state.thread_id = threadId;
      state.status = "streaming";
      state.messages = [
        {
          id: uuidv4(),
          thread_id: threadId,
          type: "user",
          content: message,
          timestamp: new Date().toISOString(),
        },
      ];
      state.expert_panels = {};
      state.current_sequence = 0;
      state.errors = [];
      state.start_time = new Date().toISOString();
      state.final_summary = undefined;
      state.router_decision = undefined;
      state.totalRecords = null;
      state.processedRecords = 0;
      state.recordSummaries = {};
      state.analysisDone = false;
    },

    // Handle incoming SSE events
    handleSseEvent: (state, action: PayloadAction<SseEnvelope>) => {
      const event = action.payload;
      state.current_sequence = Math.max(state.current_sequence, event.seq);

      switch (event.event) {
        case "router_decision":
          chatSlice.caseReducers.handleRouterDecision(state, {
            type: "handleRouterDecision",
            payload: event,
          });
          break;

        case "record_done":
          chatSlice.caseReducers.handleRecordDone(state, {
            type: "handleRecordDone",
            payload: event,
          });
          break;

        case "expert_chunk":
          chatSlice.caseReducers.handleExpertChunk(state, {
            type: "handleExpertChunk",
            payload: event,
          });
          break;

        case "expert_done":
          chatSlice.caseReducers.handleExpertDone(state, {
            type: "handleExpertDone",
            payload: event,
          });
          break;

        case "final_summary":
          chatSlice.caseReducers.handleFinalSummary(state, {
            type: "handleFinalSummary",
            payload: event,
          });
          break;

        case "error":
          chatSlice.caseReducers.handleError(state, {
            type: "handleError",
            payload: event,
          });
          break;
      }
    },

    // Handle router decision
    handleRouterDecision: (state, action: PayloadAction<SseEnvelope>) => {
      const payload = action.payload.payload as RouterDecisionPayload;

      state.router_decision = payload.selected_experts;

      // Set total records if provided
      if (payload.total_records) {
        state.totalRecords = payload.total_records;
      }

      // Initialize expert panels for selected experts
      payload.selected_experts.forEach((expertId) => {
        const config = getExpertConfig(expertId);
        state.expert_panels[expertId] = {
          expert_id: expertId,
          expert_type: config.type,
          status: "processing",
          chunks: [],
        };
      });

      // Add router decision message
      state.messages.push({
        id: uuidv4(),
        thread_id: state.thread_id!,
        type: "system",
        content: `Router selected experts: ${payload.selected_experts.join(", ")}`,
        timestamp: action.payload.timestamp,
        metadata: { reasoning: payload.reasoning },
      });
    },

    // Handle record done
    handleRecordDone: (state, action: PayloadAction<SseEnvelope>) => {
      const payload = action.payload.payload as RecordDonePayload;

      state.processedRecords += 1;
      state.recordSummaries[payload.id] = {
        kind: payload.kind as "host" | "cert",
        summary: payload.summary,
      };
    },

    // Handle expert chunk
    handleExpertChunk: (state, action: PayloadAction<SseEnvelope>) => {
      const payload = action.payload.payload as ExpertChunkPayload;
      const { expert_id, chunk } = payload;

      // Ensure expert panel exists
      if (!state.expert_panels[expert_id]) {
        const config = getExpertConfig(expert_id);
        state.expert_panels[expert_id] = {
          expert_id,
          expert_type: config.type,
          status: "processing",
          chunks: [],
        };
      }

      // Add chunk to expert panel
      state.expert_panels[expert_id].chunks.push(chunk);
      state.expert_panels[expert_id].status = "processing";
    },

    // Handle expert completion
    handleExpertDone: (state, action: PayloadAction<SseEnvelope>) => {
      const payload = action.payload.payload as ExpertDonePayload;
      const { expert_id, summary, confidence, processing_time_ms } = payload;

      // Update expert panel
      if (state.expert_panels[expert_id]) {
        state.expert_panels[expert_id].status = "completed";
        state.expert_panels[expert_id].final_summary = summary;
        state.expert_panels[expert_id].confidence = confidence;
        state.expert_panels[expert_id].processing_time_ms = processing_time_ms;
      }

      // Add expert message
      state.messages.push({
        id: uuidv4(),
        thread_id: state.thread_id!,
        type: "expert",
        content: summary,
        timestamp: action.payload.timestamp,
        expert_type: payload.expert_type as any,
        expert_id: expert_id,
        metadata: {
          confidence,
          processing_time_ms,
        },
      });
    },

    // Handle final summary
    handleFinalSummary: (state, action: PayloadAction<SseEnvelope>) => {
      const payload = action.payload.payload as FinalSummaryPayload;

      state.final_summary = payload.summary;
      state.total_processing_time = payload.total_processing_time_ms;
      state.status = "completed";
      state.analysisDone = true;

      // Set total records if not already set from router_decision
      if (state.totalRecords === null) {
        state.totalRecords = payload.expert_count;
      }

      // Add final summary message
      state.messages.push({
        id: uuidv4(),
        thread_id: state.thread_id!,
        type: "final",
        content: payload.summary,
        timestamp: action.payload.timestamp,
        metadata: {
          expert_count: payload.expert_count,
          total_processing_time_ms: payload.total_processing_time_ms,
        },
      });
    },

    // Handle errors
    handleError: (state, action: PayloadAction<SseEnvelope>) => {
      const payload = action.payload.payload as ErrorPayload;

      state.errors.push(`${payload.error_code}: ${payload.message}`);

      // If it's an expert error, update the expert panel
      if ("expert_id" in payload && payload.expert_id) {
        const expertId = payload.expert_id as string;
        if (state.expert_panels[expertId]) {
          state.expert_panels[expertId].status = "error";
          state.expert_panels[expertId].error_message = payload.message;
        }
      }

      // Add error message
      state.messages.push({
        id: uuidv4(),
        thread_id: state.thread_id!,
        type: "system",
        content: `Error [${payload.error_code}]: ${payload.message}`,
        timestamp: action.payload.timestamp,
        metadata: {
          error_code: payload.error_code,
          details: payload.details,
        },
      });
    },

    // Reset conversation
    resetConversation: (state) => {
      return { ...initialState };
    },

    // Set streaming status
    setStreamingStatus: (
      state,
      action: PayloadAction<ConversationState["status"]>,
    ) => {
      state.status = action.payload;
    },

    // Clear errors
    clearErrors: (state) => {
      state.errors = [];
    },
  },
});

// Export actions
export const {
  startConversation,
  handleSseEvent,
  handleRouterDecision,
  handleRecordDone,
  handleExpertChunk,
  handleExpertDone,
  handleFinalSummary,
  handleError,
  resetConversation,
  setStreamingStatus,
  clearErrors,
} = chatSlice.actions;

// Selectors
export const selectConversation = (state: { chat: ConversationState }) =>
  state.chat;
export const selectMessages = (state: { chat: ConversationState }) =>
  state.chat.messages;
export const selectExpertPanels = (state: { chat: ConversationState }) =>
  state.chat.expert_panels;
export const selectStreamingStatus = (state: { chat: ConversationState }) =>
  state.chat.status;
export const selectFinalSummary = (state: { chat: ConversationState }) =>
  state.chat.final_summary;
export const selectErrors = (state: { chat: ConversationState }) =>
  state.chat.errors;
export const selectRouterDecision = (state: { chat: ConversationState }) =>
  state.chat.router_decision;

// Expert panel selectors
export const selectExpertPanel =
  (expertId: string) => (state: { chat: ConversationState }) =>
    state.chat.expert_panels[expertId];

export const selectActiveExperts = (state: { chat: ConversationState }) =>
  Object.keys(state.chat.expert_panels);

export const selectCompletedExperts = (state: { chat: ConversationState }) =>
  Object.values(state.chat.expert_panels).filter(
    (panel) => panel.status === "completed",
  );

export const selectProcessingExperts = (state: { chat: ConversationState }) =>
  Object.values(state.chat.expert_panels).filter(
    (panel) => panel.status === "processing",
  );

// New selectors for record-based progress
export const selectTotalRecords = (state: { chat: ConversationState }) =>
  state.chat.totalRecords;

export const selectProcessedRecords = (state: { chat: ConversationState }) =>
  state.chat.processedRecords;

export const selectRecordSummaries = (state: { chat: ConversationState }) =>
  state.chat.recordSummaries;

export const selectAnalysisDone = (state: { chat: ConversationState }) =>
  state.chat.analysisDone;

// Export reducer
export default chatSlice.reducer;
