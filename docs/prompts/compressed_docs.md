Below are some docs to help you get started. 

---

# LangGraph: Hierarchical Expertise Router (Topic-Specific Experts) – Compressed Guide

## 1. Overview

LangGraph is a framework for building agentic, multi-agent, and tool-using LLM applications with first-class support for streaming, persistence, and human-in-the-loop workflows. It is highly modular, allowing you to compose complex workflows as graphs of nodes (functions) and edges (control flow).

**Hierarchical Expertise Router** is a pattern where a central router (LLM) receives user input and routes it to one or more specialized expert agents (subgraphs), each responsible for a specific topic or view (e.g., Geo, Certificate, Vulnerability). Each expert processes the same input data and returns a specialized summary, which are then merged into a final answer.

---

## 2. Key Concepts

### Graphs, Nodes, and State

- **Graph**: A workflow composed of nodes (functions) and edges (control flow).
- **Node**: A function (sync or async) that receives and updates the shared state.
- **State**: A (TypedDict, dataclass, or Pydantic model) representing the data passed between nodes. Reducers can be used to control how updates are applied (e.g., append vs. overwrite).

### Subgraphs

- Subgraphs are graphs used as nodes in a parent graph.
- **Shared state**: Parent and subgraph communicate via shared keys (e.g., messages).
- **Different state**: Use a wrapper node to transform state in/out of the subgraph.

### Streaming

- **stream_mode="updates"**: Streams state updates after each node.
- **stream_mode="values"**: Streams the full state after each node.
- **stream_mode="messages"**: Streams LLM tokens as they are generated.
- **stream_mode="custom"**: Streams custom data from inside nodes/tools.

### Persistence & Memory

- **Checkpointer**: Saves state after each step for resuming, time travel, and human-in-the-loop.
- **Thread ID**: Used to scope memory/persistence to a conversation.
- **Store**: For long-term, cross-thread memory (e.g., user profiles, semantic search).

### Human-in-the-loop

- Use `interrupt()` to pause execution for human input/approval.
- Resume with a `Command(resume=...)` object.

---

## 3. Hierarchical Expertise Router Pattern

**Pattern:**
```
USER → ROUTER (LLM)
├─► GeoAgent
├─► CertAgent
├─► VulnAgent
└─► ...
└─► MERGE-ANSWER
```

- **Router**: Receives user input and data, decides which experts to invoke.
- **Experts**: Each is a subgraph/agent specialized in a topic, processes the same data, and returns a summary.
- **Merge Node**: Combines expert outputs into a final answer.

**Parallelization**: Experts can be run in parallel for performance.

**Streaming**: 
- Emit `router_decision` event.
- Stream `assistant_answer` chunks from each expert, tagged by expert_id.
- Emit `merged_summary` when done.

---

## 4. Example: Parallel Branching and Merging

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    summaries: Annotated[list[str], operator.add]

def router(state: State):
    # Decide which experts to call (e.g., based on user query)
    return ["geo", "cert", "vuln"]

def geo_expert(state: State):
    return {"summaries": ["Geo summary..."]}

def cert_expert(state: State):
    return {"summaries": ["Cert summary..."]}

def vuln_expert(state: State):
    return {"summaries": ["Vuln summary..."]}

def merge(state: State):
    return {"final_summary": "\n".join(state["summaries"])}

builder = StateGraph(State)
builder.add_node("router", router)
builder.add_node("geo", geo_expert)
builder.add_node("cert", cert_expert)
builder.add_node("vuln", vuln_expert)
builder.add_node("merge", merge)
builder.add_edge(START, "router")
builder.add_conditional_edges("router", lambda s: s["experts"], ["geo", "cert", "vuln"])
builder.add_edge(["geo", "cert", "vuln"], "merge")
builder.add_edge("merge", END)
graph = builder.compile()
```

---

## 5. Subgraphs: Shared vs. Different State

- **Shared state**: Add subgraph directly as a node if parent and subgraph share keys.
- **Different state**: Use a wrapper node to transform state in/out.

```python
def call_subgraph(state: ParentState):
    subgraph_output = subgraph.invoke({"bar": state["foo"]})
    return {"foo": subgraph_output["bar"]}
```

---

## 6. Streaming Outputs

- Use `.stream(inputs, stream_mode="updates", subgraphs=True)` to stream updates from both parent and subgraphs.
- Each chunk is a tuple: `(namespace, update)`, where `namespace` indicates the path (e.g., which expert/subgraph).

---

## 7. Tool Calling

- Tools are Python functions decorated with `@tool`.
- Use `ToolNode` to execute tools in a workflow.
- Tools can update state by returning a `Command(update={...})`.

---

## 8. Human-in-the-loop

- Use `interrupt()` in a node to pause for human input.
- Resume with `Command(resume=...)`.
- Example: Pause before merging summaries for human approval.

---

## 9. Error Handling & Retry

- Nodes can have custom retry policies via `RetryPolicy`.
- ToolNode can handle tool errors and return error messages to the LLM.

---

## 10. Persistence & Memory

- Use a checkpointer (e.g., `InMemorySaver`, `PostgresSaver`) to enable thread-level persistence.
- Use a Store (e.g., `InMemoryStore`) for long-term, cross-thread memory (e.g., user profiles, semantic search).

---

## 11. Configuration & Runtime Context

- Pass runtime config (e.g., model, user_id) via the `config` argument.
- Nodes can access config and context for dynamic behavior.

---

## 12. Functional API (Alternative)

- Use `@entrypoint` and `@task` decorators for a more Pythonic, function-based workflow.
- Supports the same features: persistence, streaming, human-in-the-loop, etc.

---

## 13. Example: Streaming SSE Contract

- Each backend request creates one SSE stream.
- Each SSE event is appended to Redux (frontend).
- On reload, UI fetches all messages for a conversation ID.
- SSE event types: tool call, data input, tool result, assistant answer, etc.

---

## 14. Useful Patterns

- **Parallel fan-out/fan-in**: Use reducers (e.g., `operator.add`) to accumulate results from parallel branches.
- **Conditional branching**: Use `add_conditional_edges` to route based on state.
- **Map-reduce**: Use `Send` to fan out to multiple nodes and aggregate results.

---

## 15. Streaming LangGraph to a React UI: End-to-End Pattern

### Backend: FastAPI + LangGraph + SSE

**Key Points:**
- Use FastAPI's `StreamingResponse` to stream events from LangGraph.
- Each event is a chunk (e.g., state update, tool call, custom event).
- Use `stream_mode` to control what is streamed (`"updates"`, `"messages"`, `"custom"`, etc.).
- For custom events, use a `StreamWriter` in your node/tool and `stream_mode="custom"`.

**Example:**

```python
from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, ToolMessage
from myapp.llm_flow import graph  # your compiled LangGraph graph

app = FastAPI()

def event_stream(query: str):
    initial_state = {"messages": [HumanMessage(content=query)]}
    for chunk in graph.stream(initial_state, stream_mode="updates"):
        for node_name, node_results in chunk.items():
            chunk_messages = node_results.get("messages", [])
            for message in chunk_messages:
                if not message.content:
                    continue
                if isinstance(message, ToolMessage):
                    event_str = "event: tool_event"
                else:
                    event_str = "event: ai_event"
                data_str = f"data: {message.content}"
                yield f"{event_str}\n{data_str}\n\n"

@app.post("/stream")
async def stream(query: str = Body(..., embed=True)):
    return StreamingResponse(event_stream(query), media_type="text/event-stream")
```

**Custom Events Example:**

```python
from langgraph.config import get_stream_writer

def my_node(state):
    writer = get_stream_writer()
    writer({"progress": "Step 1 complete"})
    # ... do work ...
    writer({"progress": "Step 2 complete"})
    return {"result": "done"}
```

---

### Frontend: React + fetch-event-source

**Key Points:**
- Use [@microsoft/fetch-event-source](https://www.npmjs.com/package/@microsoft/fetch-event-source) for POST-based SSE (native `EventSource` only supports GET).
- Each event is handled in the `onmessage` callback.
- You can branch on `ev.event` to handle different event types (e.g., tool calls, AI messages, errors, custom events).

**Example:**

```jsx
import React, { useEffect, useState } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";

function StreamComponent({ query }) {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    fetchEventSource("/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
      onmessage(ev) {
        if (ev.event === "error_event") {
          alert(`Error: ${ev.data}`);
        } else {
          setMessages((prev) => [...prev, ev.data]);
        }
      },
    });
  }, [query]);

  return (
    <div>
      {messages.map((msg, idx) => <div key={idx}>{msg}</div>)}
    </div>
  );
}
```

---

## 16. Streaming Tool Calls and LLM Tokens

**Streaming tool calls**: When using `stream_mode="messages"` or `"updates"`, tool calls are streamed as `tool_call_chunks` (raw, partial JSON) and then as parsed `tool_calls` (dicts) as the LLM output is parsed.

**Example:**

```python
async for chunk in llm_with_tools.astream(query):
    print(chunk.tool_call_chunks)  # raw, partial tool call args
    print(chunk.tool_calls)        # parsed, as soon as possible
```

**Accumulating tool call chunks:**

```python
first = True
async for chunk in llm_with_tools.astream(query):
    if first:
        gathered = chunk
        first = False
    else:
        gathered = gathered + chunk
    print(gathered.tool_call_chunks)
    print(gathered.tool_calls)
```

---

## 17. React Integration: useStream Hook

**Recommended for LangGraph Platform/Server deployments.**

- `useStream` from `@langchain/langgraph-sdk/react` abstracts away SSE, state, and branching.
- Handles loading, error, interrupts, branching, and message chunking.
- Supports custom events, thread management, and optimistic UI.

**Basic Example:**

```tsx
import { useStream } from "@langchain/langgraph-sdk/react";

export default function App() {
  const thread = useStream<{ messages: Message[] }>({
    apiUrl: "http://localhost:2024",
    assistantId: "agent",
    messagesKey: "messages",
  });

  return (
    <div>
      {thread.messages.map((message) => (
        <div key={message.id}>{message.content as string}</div>
      ))}
      <form onSubmit={e => {
        e.preventDefault();
        const message = new FormData(e.target).get("message") as string;
        thread.submit({ messages: [{ type: "human", content: message }] });
      }}>
        <input name="message" />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
```

**Advanced Features:**
- `onCustomEvent`: handle custom events from backend (e.g., progress bars).
- `interrupt`: handle human-in-the-loop pauses.
- `reconnectOnMount`: resume streams after refresh.
- `getMessagesMetadata`: for branching/versioning UI.

---

## 18. Custom Event Streaming (Backend to Frontend)

**Backend:**

```python
def my_node(state):
    writer = get_stream_writer()
    writer({"type": "progress", "payload": {"step": 1}})
    # ... do work ...
    writer({"type": "progress", "payload": {"step": 2}})
    return {"result": "done"}
```

**Frontend (React):**

```tsx
const thread = useStream({
  apiUrl: "...",
  assistantId: "...",
  onCustomEvent: (event) => {
    if (event.type === "progress") {
      // update progress bar, etc.
    }
  }
});
```

---

## 19. Error Handling in Streaming

**Backend:**

```python
from openai import RateLimitError

async def stream_with_errors(generator):
    try:
        async for chunk in generator:
            yield chunk
    except RateLimitError as e:
        yield f"event: error_event\ndata: {str(e)}\n\n"
    except Exception as e:
        yield f"event: error_event\ndata: An error occurred\n\n"
```

**Frontend:**

```jsx
onmessage(ev) {
  if (ev.event === "error_event") {
    alert(`Error: ${ev.data}`);
  } else {
    setMessages((prev) => [...prev, ev.data]);
  }
}
```

---

## 20. Manual SSE with EventSource (Alternative to useStream)

- Use the native `EventSource` API for GET-based SSE (no POST support).
- For POST, use `fetch-event-source` or similar.

**Example:**

```jsx
useEffect(() => {
  const es = new EventSource("/stream");
  es.onmessage = (ev) => {
    setMessages((prev) => [...prev, ev.data]);
  };
  return () => es.close();
}, []);
```

---

## 21. Best Practices

- Use `stream_mode="updates"` for stepwise progress, `"messages"` for LLM tokens, `"custom"` for arbitrary events.
- Use `get_stream_writer()` in nodes/tools for custom events.
- Use `useStream` for React UIs, or `fetch-event-source`/`EventSource` for custom implementations.
- For error handling, always yield a custom error event and handle it in the UI.
- For tool call streaming, accumulate `tool_call_chunks` and parse as soon as possible for responsive UIs.
