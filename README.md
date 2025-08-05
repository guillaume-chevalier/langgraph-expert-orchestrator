# LangGraph Expert Orchestrator

A full-stack, real-time, multi-agent AI demo for summarizing company infrastructure data.  
Built with **LangGraph**, **FastAPI**, **React**, and **OpenAI**.

---

## 📝 Project Overview

This project demonstrates an **agentic AI architecture** for summarizing structured company data. It features:

- **Parallel multi-agent orchestration** (LangGraph):  
  - 🖥️ Host-Infrastructure Expert  
  - 🔐 Certificate-Security Expert  
- **LLM-powered summarization**: Each expert analyzes records in parallel, then a final LLM call produces an executive summary.
- **Streaming UI**: Summaries stream live to the browser as soon as they're ready.
- **Extensible, testable, and easy to run**: Clean monorepo, Dockerized, and ready for extension.

---

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (recommended)  
  _or_ Python 3.10+ and Node.js 18+ for local development
- **OpenAI API key** (for LLM calls)
- **Sample dataset** (see below)

### Setup

1. **Add Dataset Files**

   ⚠️ **Important**: The dataset files are not committed to the repository. You need to add them manually:

   ```bash
   mkdir -p backend/dataset
   # Place your dataset files with these exact names:
   cp your_hosts.json backend/dataset/hosts_dataset.json
   cp your_web_props.json backend/dataset/web_properties_dataset.json
   ```

2. **Configure Environment**

   ```bash
   cp backend/.env.example backend/.env
   echo "OPENAI_API_KEY=sk-..." >> backend/.env
   # (Optional: tweak model/temperature in .env)
   ```

3. **Run the App**

   **With Docker (recommended):**
   ```bash
   make docker-build
   make docker-up
   # Visit http://localhost:3000
   ```

   **For local dev:**
   ```bash
   make run-backend
   # In another terminal:
   make run-frontend
   ```

### Try It Out

Visit [http://localhost:3000](http://localhost:3000) and ask questions like:
- "Analyse this dataset for suspicious hosts"
- "What certificate security issues do you see?"
- "Show me geographic patterns in the data"

Watch the expert analyses stream live in real-time!

---

## 🖥️ How It Works

1. **User asks a question** (e.g., "Find suspicious hosts")
2. **Router agent** (LLM) decides which expert(s) to run
3. **Parallel fan-out**: Each expert analyzes one record at a time (all in parallel)
4. **Streaming**: Each summary is streamed to the UI as soon as it's ready
5. **Merge node**: LLM writes a concise executive summary from all expert outputs

**Architecture Diagram:**
```
USER QUESTION + DATA
        │
        ▼
   [Router Agent]
        │
   ┌────┴────┐
   │         │
 [Host]   [Cert]  (Uses N parallel workers per record)
   │         │
   └────┬────┘
        ▼
   [Executive Summary]
        │
        ▼
     React UI (SSE)
```

---

## 🧠 AI Techniques

- **Agentic orchestration**: LangGraph splits work between specialized LLM agents, each with domain-specific prompts.
- **Prompt engineering**: Each expert uses a tailored system prompt for its domain; the summary node uses a concise, executive-style prompt.
- **Data preprocessing**: Only relevant, pruned JSON part is sent to each expert to fit within LLM context limits, along with the user's contextual question.
- **Parallelization**: Each record is analyzed in its own thread for maximum throughput.
- **Streaming**: Partial results are sent to the UI as soon as available.

---

## 🖼️ User Interface

- **Live streaming**: See expert analyses and progress as they complete.
- **Markdown rendering**: Summaries are formatted for readability.
- **Progress bar**: Visual feedback for analysis status.

---

## 🧪 Testing

- **Manual**:  
  - Start the app, ask questions, and verify summaries stream in real time.
  - Try malformed questions or missing data to see error handling.
- **Automated**:  
  - Run `make pytest` for backend tests
    - Unit tests will test with a mocked LLM, runs fast
    - Integration tests will run with the real LLM and checks answer's content, runs slower
  - Run `make test-frontend` for React unit tests.

---

## 🛠️ Developer Workflow

**Common Tasks:**
```bash
make help               # Show all available commands
make format             # Format code (black, isort, prettier)
make lint               # Lint code (flake8, eslint)
make test               # Run all tests
make clean              # Clean build artifacts
```

**Docker Development:**
```bash
make docker-build       # Build images
make docker-up          # Start services
make docker-logs        # Follow logs
make docker-down        # Stop services
make docker-clean       # Clean Docker resources
```

---

## 🛡️ Assumptions

- The provided datasets are potentially huge but can be map-reduced to a manageable size.
- The provided datasets are small enough to fit in memory and within LLM context limits after splitting in parts.
- OpenAI API is available and accessible from your environment.
- No persistent database is required; all state is in-memory or file-based.

---

## 🧩 Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── langgraph/
│   │   │   ├── experts/
│   │   │   │   ├── host.py      # Host expert prompt (Python string)
│   │   │   │   ├── cert.py      # Certificate expert prompt (Python string)
│   │   │   ├── graph.py         # Executive summary prompt (Python string)
│   │   ├── ...                  # API, models, infra
│   ├── dataset/                 # (git-ignored) sample JSON files (add manually)
│   ├── tests/
│   │   ├── integration/         # Integration tests (API, LLM, streaming)
│   │   └── unit/                # Unit tests (experts, router, dataset)
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/                     # React UI, Redux, SSE, components
│   ├── public/                  # Static assets, index.html
│   ├── Dockerfile
│   └── .env.example
├── docs/
│   └── prompts/
│       ├── plan.md              # Prompt planning notes
│       ├── system.md            # System prompt docs
│       ├── langgraph-llms-*.md  # Prompt variants and experiments
│       └── ...                  # Other prompt engineering docs/scripts
├── Makefile                     # all commands (see `make help`)
├── docker-compose.yml           # Multi-service orchestration
└── README.md
```

**Files containing prompts:**

- [`backend/app/langgraph/experts/host.py`](backend/app/langgraph/experts/host.py)
  Host expert prompt

- [`backend/app/langgraph/experts/cert.py`](backend/app/langgraph/experts/cert.py)
  Certificate expert prompt

- [`backend/app/langgraph/graph.py`](backend/app/langgraph/graph.py)
  Executive summary prompt

- Prompt documentation and experiments (usable through the Makefile:
  `make prompt-o3-pro`, `make prompt-frontend`, `make prompt-backend` for development assistance):
  - [`docs/prompts/plan.md`](docs/prompts/plan.md)
  - [`docs/prompts/system.md`](docs/prompts/system.md)
  - [`docs/prompts/langgraph-llms-full.md`](docs/prompts/langgraph-llms-full.md)
  - [`docs/prompts/langgraph-llms-short.md`](docs/prompts/langgraph-llms-short.md)
  - [`docs/prompts/langgraphjs-llms-full.md`](docs/prompts/langgraphjs-llms-full.md)
  - [`docs/prompts/langgraphjs-llms-short.md`](docs/prompts/langgraphjs-llms-short.md)

---

## 🛡️ Error Handling

- Exceptions are caught and streamed as human-readable error messages to the UI.
- Invalid/missing data or API errors are surfaced clearly for debugging.
- Typed error codes help distinguish different failure types.

---

## 📋 Evaluation Checklist

| Criterion             | How Addressed                                  |
|-----------------------|------------------------------------------------|
| Functional Correctness| Integration tests + manual demo                |
| Agentic Orchestration | LangGraph parallel fan-out per record, merge summary      |
| Prompt Engineering    | Domain-specific system prompts for pretty results         |
| Error Handling        | SSE error events, readable messages            |
| Data Preprocessing    | Splitted JSON, bullet digests                  |
| Parallelization       | Per-record workers, async event streaming      |
| Code Quality          | Typed, modular, Makefile for all tasks, linter, formatter |
| Data Modeling         | Pydantic (Python) / TypeScript (frontend)      |
| Documentation         | This README, in-code docstrings, docs/prompts useable in Makefile |
| Extensibility         | Add experts via new modules, update router     |

---

## 🚀 Future Enhancements List

If given more time to work on this project, here are the key enhancements I would implement:

1. **Token-Level Streaming**
   - Stream LLM responses token-by-token as they generate (currently streams complete analyses)
   - Add visual typing effect in UI for more engaging real-time experience
   - Implementation: Use `llm.astream()` in expert nodes with `expert_token` SSE events

2. **Cross-Expert Context Sharing**
   - Enhance expert prompts with dataset overview and peer expert insights
   - Each expert gets context about patterns found by other experts
   - Implementation: Build shared context object passed to all expert prompts

3. **Fixed-Point Iterative Analysis**
   - Multi-pass analysis where experts refine findings based on collective insights
   - Continue iterations until analysis converges on stable patterns
   - Deep research approach to multi-agent AI collaboration

4. **Dynamic Expert Spawning**
   - Route records to most appropriate expert combinations: self-adapting analysis pipeline
   - Geographic clustering and risk correlation analysis could help share context in fixed point iterations
   - Time-series event correlation could also help share context in fixed point iterations


---

## 📚 Further Info

- **Version info**: Python 3.10+, Node 18+, Yarn v1, React 18, Docker Compose
- **License**: MIT (see `LICENSE`)
- **All commands**: `make help`. See below for a summary of available commands.

```shell
$ make help
🚀 LangGraph Expert Orchestrator AI Project - Available Commands:

📋 Development:
  venv              Create Python venv in backend/venv
  install           Install backend Python deps into venv
  install-test      Install backend test and dev dependencies
  run-backend       Run FastAPI backend (with venv)
  run-frontend      Run React frontend (with yarn)

🧪 Testing:
  test              Run all tests (backend + frontend)
  test-frontend     Run frontend tests only
  pytest            Run all backend tests (unit + integration)
  pytest-unit       Run backend unit tests only
  pytest-integration Run backend integration tests only

🎨 Code Quality:
  format            Format all code (Python: black, isort | Frontend: prettier)
  lint              Lint all code (Python: flake8, pylint | Frontend: eslint)

🐳 Docker:
  docker-build      Build Docker images
  docker-up         Start services with Docker Compose
  docker-down       Stop Docker services
  docker-logs       Show Docker logs (follow mode)
  docker-restart    Restart Docker services
  docker-clean      Clean project Docker resources
  docker-clean-all  Complete Docker reset (containers, images, volumes)
  docker-shell-backend  Open shell in backend container
  docker-shell-frontend Open shell in frontend container
  docker-status     Check Docker Compose availability

🧹 Cleanup:
  clean             Complete cleanup: Deletes backend/venv, node_modules, Docker containers/images
  docker-clean      Clean Docker containers and volumes only
  docker-clean-all  Clean ALL project Docker resources (containers, images, networks)

📋 Development Assistance:
  prompt-backend    Copy backend code + docs to clipboard for LLM assistance
  prompt-frontend   Copy frontend code + docs to clipboard for LLM assistance
  prompt-o3-pro     Copy complete codebase + compressed docs for o3-pro analysis
```

## 🤖 About AI-Assisted Coding

My workflow was to use `make prompt-o3-pro` to copy the entire codebase and compressed docs to the clipboard, then paste that into [o3-pro](https://platform.openai.com/chat/edit?models=o3-pro) for analysis. This allows me to get AI assistance on the entire project context, while also copying custom prompts such as the [`docs/prompts/plan.md`](docs/prompts/plan.md) for the preliminary architectural design (initial brainstorm done with o3-pro and problem statement). The copy command also copies the [`docs/prompts/system.md`](docs/prompts/system.md) file that can be updated on a rolling basis depending on the task and state at hand, such as with instructions and wishes, in which you can maintain a rolling custom prompt, such as "You are an expert react, redux, monorepo, and full stack developer AI agent helping an expert AI Engineer create a project that also happens to be an open-source demo.".

I also used Roo Code (VS Code extension) to use both the Makefile prompts and the results from o3-pro. I find it best to use Claude 4 models through an API key in Roo Code to code and debug, while using o3-pro for high-level reasoning and planning to feed that Roo Code's Claude instance. I also used the `prompt-backend` and `prompt-frontend` commands in the Makefile to copy the code and docs to the clipboard for use in Roo Code or o3-pro when the tasks were very focused on just one part.

To give an idea, I spawned this entire project with about a bit more than 150$ of usage on both platforms combined.

Using o3-pro in high reasoning effort to steer Claude is a great way to get the best of both worlds, as o3-pro is very good at reasoning about the code and architecture, while Claude 4 is very good at coding and debugging. I believe this is the state of the art in AI-assisted coding at the moment (August 2025).

---

**Built with ❤️ & LangGraph**  
by Guillaume Chevalier

---

MIT License
