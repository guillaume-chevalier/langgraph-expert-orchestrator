import chatReducer, {
  startConversation,
  handleSseEvent,
  resetConversation,
} from "./chatSlice";
import { ConversationState, SseEnvelope } from "../../types";

describe("chatSlice", () => {
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

  it("should return the initial state", () => {
    expect(chatReducer(undefined, { type: "unknown" })).toEqual(initialState);
  });

  it("should handle startConversation", () => {
    const action = startConversation({
      threadId: "test-123",
      message: "Test message",
    });

    const actual = chatReducer(initialState, action);

    expect(actual.thread_id).toBe("test-123");
    expect(actual.status).toBe("streaming");
    expect(actual.messages).toHaveLength(1);
    expect(actual.messages[0].content).toBe("Test message");
    expect(actual.messages[0].type).toBe("user");
  });

  it("should handle router_decision event", () => {
    const sseEvent: SseEnvelope = {
      event: "router_decision",
      thread_id: "test-123",
      seq: 1,
      timestamp: new Date().toISOString(),
      payload: {
        selected_experts: ["host_fan", "cert_fan"],
        reasoning: "Test reasoning",
        total_records: 6,
      },
    };

    const stateWithConversation = {
      ...initialState,
      thread_id: "test-123",
      status: "streaming" as const,
    };

    const actual = chatReducer(stateWithConversation, handleSseEvent(sseEvent));

    expect(actual.router_decision).toEqual(["host_fan", "cert_fan"]);
    expect(actual.expert_panels).toHaveProperty("host_fan");
    expect(actual.expert_panels).toHaveProperty("cert_fan");
    expect(actual.expert_panels.host_fan.status).toBe("processing");
    expect(actual.totalRecords).toBe(6);
  });

  it("should handle expert_done event", () => {
    const sseEvent: SseEnvelope = {
      event: "expert_done",
      thread_id: "test-123",
      seq: 2,
      timestamp: new Date().toISOString(),
      payload: {
        expert_id: "host_fan",
        expert_type: "host",
        summary: "Host analysis complete",
        confidence: 0.95,
        processing_time_ms: 1500,
      },
    };

    const stateWithExpert = {
      ...initialState,
      thread_id: "test-123",
      expert_panels: {
        host_fan: {
          expert_id: "host_fan",
          expert_type: "host" as const,
          status: "processing" as const,
          chunks: [],
        },
      },
    };

    const actual = chatReducer(stateWithExpert, handleSseEvent(sseEvent));

    expect(actual.expert_panels.host_fan.status).toBe("completed");
    expect(actual.expert_panels.host_fan.final_summary).toBe(
      "Host analysis complete",
    );
    expect(actual.expert_panels.host_fan.confidence).toBe(0.95);
    expect(actual.messages).toHaveLength(1);
    expect(actual.messages[0].type).toBe("expert");
  });

  it("should handle resetConversation", () => {
    const stateWithData = {
      ...initialState,
      thread_id: "test-123",
      status: "completed" as const,
      messages: [
        {
          id: "1",
          thread_id: "test",
          type: "user" as const,
          content: "test",
          timestamp: "",
        },
      ],
      errors: ["some error"],
    };

    const actual = chatReducer(stateWithData, resetConversation());

    expect(actual).toEqual(initialState);
  });
});
