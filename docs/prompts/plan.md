# Hierarchical Expertise Router – Full Project Blueprint  
*(o3-pro, high-reasoning edition — single source of truth for every reload of a coding assistant)*

---

## Table of Contents  
1. **Project Vision & Scope**  
2. **Monorepo Structure & Naming**  
3. **Environment & Secrets Management**  
4. **Backend Overview**  
    4.1. Architecture & Flow  
    4.2. Folder Structure  
    4.3. Models & Types  
    4.4. LangGraph Design  
    4.5. API & Streaming  
    4.6. Observability & Logging  
    4.7. Testing (Python)  
5. **Frontend Overview**  
    5.1. Architecture & Flow  
    5.2. Folder Structure  
    5.3. Types & Contracts  
    5.4. Redux & State Management  
    5.5. Streaming & Data Flow  
    5.6. UI Components  
    5.7. Testing (JS)  
6. **Makefile & Developer Workflow**  
7. **How to Run, Test, and Develop**  
8. **What’s Out of Scope (and Why)**  
9. **Appendix: Best Practices & Troubleshooting**  

---

## 1. Project Vision & Scope  

**Goal**  
A minimal open-source demo that showcases a *parallel map-reduce* agent workflow using LangGraph, FastAPI, and a React UI.  
Two domain experts (“host” and “certificate”) analyse sample JSON datasets in parallel; per-record results stream live to the browser; a merge node produces an executive summary.

**Key Points**  
* Real-time SSE streaming  
* Parallel fan-out per record (Send → sub-graph)  
* Clean, type-safe, testable code  
* Zero proprietary names or secrets in code or docs  

---

## 2. Monorepo Structure & Naming  

```
repo/
├── backend/
│   ├── app/
│   │   ├── infrastructure/
│   │   │   └── dataset_repository.py
│   │   ├── langgraph/
│   │   │   ├── experts/
│   │   │   │   ├── host.py  # KIND="host"
│   │   │   │   └── cert.py  # KIND="cert"
│   │   │   ├── map_subgraphs.py
│   │   │   ├── router.py
│   │   │   └── graph.py
│   │   ├── models.py
│   │   ├── sse.py
│   │   └── main.py
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── pyproject.toml
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── features/
│   │   │   └── chat/
│   │   │       ├── chatSlice.ts
│   │   │       ├── useChat.ts
│   │   │       └── ChatWindow.tsx
│   │   ├── types.ts
│   │   └── App.tsx
│   ├── tests/
│   ├── package.json
│   ├── .env.example
│   └── README.md
├── Makefile
```

**Naming rules**  
Python = snake_case files, PascalCase classes.  
TypeScript = camelCase vars, PascalCase types.  
Absolute imports inside each package.

---

## 3. Environment & Secrets Management  

`.env.example` (root of backend):  
```
OPENAI_API_KEY=your-key
```
No real secrets ever committed.

---

## 4. Backend Overview  

### 4.1. Architecture & Flow  

1. Client POSTs `/v1/stream` with `{thread_id?, message, host_limit?, cert_limit?}`  
2. Endpoint loads **sample records** via the existing `dataset_repository`.  
3. Initial LangGraph state:  
   ```
   {
     thread_id,
     records=[...HostRecord | CertificateRecord...],
     summaries=[]
   }
   ```  
4. Router splits records → lists `host_records`, `cert_records`, returns `"host_fan"` / `"cert_fan"` in `router_decision`.  
5. `host_fan` and `cert_fan` wrap each record in a `Send(...)` to their respective sub-graph (`host_map_graph`, `cert_map_graph`).  
6. Each sub-graph runs its expert on **one** record. When done it appends a summary dict (includes `record_id`).  
7. SSE layer emits `record_done` for every new summary.  
8. Merge node aggregates summaries → `final_summary` + `stats` (counts).  
9. SSE `final_summary` event closes stream.

### 4.2. Folder Structure  

Already listed above;

### 4.3. Models & Types  

*Use models from `dataset_repository`* – no duplicates.  
AgentState (in `app/models.py`) holds:

```python
class AgentState(TypedDict, total=False):
    thread_id: str
    records: list[Any]                # HostRecord | CertificateRecord
    host_records: list[Any]
    cert_records: list[Any]
    router_decision: list[str]        # ["host_fan","cert_fan"]
    summaries: Annotated[list[dict], operator.add]
    stats: dict
    final_summary: str
```

SSE envelope already exists; add `"record_done"` to `EventName`.

### 4.4. LangGraph Design  

```
START
  └─ router_node
        ├─ host_fan ─► host_map_graph (one per host)
        └─ cert_fan ─► cert_map_graph (one per cert)
                     ╲_______________________________╱
                                │
                             merge_node
                                │
                               END
```

Sub-graphs contain a **single** expert node; compiled once and inserted as a node.

### 4.5. API & Streaming  

`POST /v1/stream`  
* Loads records (`repo.get_all_hosts()[:limit]`, etc.)  
* Generates SSE stream:  
  * `router_decision`  
  * many `record_done`  
  * `final_summary`  
* SSE frames follow `id/event/data` contract.

### 4.6. Observability & Logging  

* `LOG_LEVEL` env var; default INFO.  
* Log every SSE envelope JSON (helpful in dev).  
* Uncaught exceptions → SSE `error` + HTTP 500.

### 4.7. Testing (Python)  

Unit:  
* Dataset repository returns >0 hosts/certs.  
* Router splits correctly.  

Integration (mock llm):  
* POST `/v1/stream` with 2 hosts + 1 cert → expect 3 `record_done` and `final_summary`.  

---

## 5. Frontend Overview  

### 5.1. Architecture & Flow  
Sends POST, listens for SSE, feeds Redux.

### 5.2. Folder Structure  
Already listed.

### 5.3. Types & Contracts  

`types.ts` mirrors backend SseEnvelope. Include `"record_done"`.

### 5.4. Redux & State Management  

Store:  
```
{
  experts: { [expertType]: { completed, inProgress } },
  records: { [record_id]: summary },
  finalSummary: string | null
}
```
Update on `record_done` and `final_summary`.

### 5.5. Streaming & Data Flow  

Use `@microsoft/fetch-event-source`.  
Auto-reconnect optional.

### 5.6. UI Components  

* Global progress bar = processed / total records.  
* Collapsible per-record panels showing summaries.  

### 5.7. Testing (JS)  

Reducer tests + simple component render; no E2E required.

---

## 6. Makefile & Developer Workflow  

```
run-backend:
	cd backend && uvicorn app.main:app --reload

run-frontend:
	cd frontend && yarn dev   # vite

test:
	cd backend && pytest -q
	cd frontend && yarn test --watchAll=false
```

---

## 7. How to Run, Test, and Develop  

1. `cp backend/.env.example backend/.env` → add your OpenAI key.  
1. `cp frontend/.env.example frontend/.env` → add your OpenAI key.  
2. `pip install -e backend`  
3. `cd frontend && yarn install`  
4. `make run-backend`  
5. `make run-frontend`  
6. Open `http://localhost:3000`, pick record limits, submit.  
7. `make test` to run all tests.

---

## 8. What’s Out of Scope (and Why)  

* No DB or persistence  
* CI pipelines  
* No authentication  
* No extra experts (beyond host & cert) for the demo  

These can be added later if desired.

---

## 9. Appendix: Best Practices & Troubleshooting  

* **One source of truth for models** – always import `HostRecord` / `CertificateRecord` from `dataset_repository`.  
* If SSE seems silent, check CORS and ensure `X-Accel-Buffering: no` header is present (nginx).  
* Keep reducer functions (`operator.add`) on list fields to avoid accidental overwrite in parallel steps.  
* For large fan-outs, consider chunked sub-batches to avoid hitting LLM token limits.  
* When adding new event types, update both backend `EventName` literal and frontend `types.ts`.  

---

**This plan supersedes any earlier drafts; it is complete, self-consistent, and free of organisation-specific references.  Use it as the canonical guide while developing.  Good luck!**
