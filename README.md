# LangGraph Expert Orchestrator

Multi-agent AI orchestration platform using LangGraph and React with real-time streaming.

## Quick Start

```bash
# Setup
cp backend/.env.example backend/.env
# Add your OPENAI_API_KEY to backend/.env

# Run
make install
make run-backend  # Port 8000
make run-frontend # Port 3000
```

There is more! Do `make help` to see all available commands.

## Stack

- **Backend**: LangGraph + FastAPI + SSE streaming
- **Frontend**: React + Redux + TypeScript
- **AI**: Multi-expert parallel processing with specialized analysis agents
- **Data**: Real-time streaming with Server-Sent Events

## Architecture

```
User Query → Router → Parallel Experts → SSE Stream → React UI
```

Demonstrates modern patterns for building real-time multi-agent AI applications.
