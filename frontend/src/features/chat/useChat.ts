import { useCallback, useRef } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { v4 as uuidv4 } from "uuid";

import {
  startConversation,
  handleSseEvent,
  setStreamingStatus,
  selectConversation,
  selectStreamingStatus,
} from "./chatSlice";
import { SseEnvelope } from "../../types";

export const useChat = () => {
  const dispatch = useDispatch();
  const conversation = useSelector(selectConversation);
  const streamingStatus = useSelector(selectStreamingStatus);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (message: string) => {
      // Generate thread ID if starting new conversation
      const threadId = conversation.thread_id || uuidv4();

      // Start the conversation
      dispatch(startConversation({ threadId, message }));

      // Create abort controller for this request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      const backendUrl =
        process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

      try {
        await fetchEventSource(`${backendUrl}/v1/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message,
          }),
          signal: abortControllerRef.current.signal,

          onmessage(event) {
            try {
              const envelope: SseEnvelope = JSON.parse(event.data);
              dispatch(handleSseEvent(envelope));
            } catch (error) {
              console.error("Failed to parse SSE event:", error);
            }
          },

          onerror(error) {
            console.error("SSE connection error:", error);
            dispatch(setStreamingStatus("error"));
            throw error; // Will cause fetchEventSource to stop retrying
          },

          onclose() {
            console.log("SSE connection closed");
            if (streamingStatus === "streaming") {
              dispatch(setStreamingStatus("completed"));
            }
          },

          openWhenHidden: true, // Keep connection open when tab is not active
        });
      } catch (error: unknown) {
        if (error instanceof Error && error.name !== "AbortError") {
          console.error("Error sending message:", error);
          dispatch(setStreamingStatus("error"));
        }
      }
    },
    [dispatch, conversation.thread_id, streamingStatus],
  );

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      dispatch(setStreamingStatus("completed"));
    }
  }, [dispatch]);

  return {
    sendMessage,
    stopStreaming,
    conversation,
    isStreaming: streamingStatus === "streaming",
    isCompleted: streamingStatus === "completed",
    hasError: streamingStatus === "error",
  };
};
