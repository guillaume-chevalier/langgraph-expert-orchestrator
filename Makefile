VENV_DIR := backend/venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip

PROMPT_DIR := docs/prompts
PROMPT_SYSTEM := $(PROMPT_DIR)/system.md
PROMPT_PLAN := $(PROMPT_DIR)/plan.md
PROMPT_LANGGRAPH_SHORT := $(PROMPT_DIR)/langgraph-llms-short.md
PROMPT_LANGGRAPHJS_SHORT := $(PROMPT_DIR)/langgraphjs-llms-short.md


.PHONY: help venv install install-test run-backend run-frontend test test-frontend pytest pytest-unit pytest-integration clean format lint docker-build docker-up docker-down docker-logs docker-clean docker-clean-all docker-restart docker-shell-backend docker-shell-frontend docker-status prompt-backend prompt-frontend prompt-o3-pro

help:
	@echo "🚀 LangGraph Expert Orchestrator AI Project - Available Commands:"
	@echo
	@echo "📋 Development:"
	@echo "  venv              Create Python venv in $(VENV_DIR)"
	@echo "  install           Install backend Python deps into venv"
	@echo "  install-test      Install backend test and dev dependencies"
	@echo "  run-backend       Run FastAPI backend (with venv)"
	@echo "  run-frontend      Run React frontend (with yarn)"
	@echo
	@echo "🧪 Testing:"
	@echo "  test              Run all tests (backend + frontend)"
	@echo "  test-frontend     Run frontend tests only"
	@echo "  pytest            Run all backend tests (unit + integration)"
	@echo "  pytest-unit       Run backend unit tests only"
	@echo "  pytest-integration Run backend integration tests only"
	@echo
	@echo "🎨 Code Quality:"
	@echo "  format            Format all code (Python: black, isort | Frontend: prettier)"
	@echo "  lint              Lint all code (Python: flake8, pylint | Frontend: eslint)"
	@echo
	@echo "🐳 Docker:"
	@echo "  docker-build      Build Docker images"
	@echo "  docker-up         Start services with Docker Compose"
	@echo "  docker-down       Stop Docker services"
	@echo "  docker-logs       Show Docker logs (follow mode)"
	@echo "  docker-restart    Restart Docker services"
	@echo "  docker-clean      Clean project Docker resources"
	@echo "  docker-clean-all  Complete Docker reset (containers, images, volumes)"
	@echo "  docker-shell-backend  Open shell in backend container"
	@echo "  docker-shell-frontend Open shell in frontend container"
	@echo "  docker-status     Check Docker Compose availability"
	@echo
	@echo "🧹 Cleanup:"
	@echo "  clean             Complete cleanup: Deletes backend/venv, node_modules, Docker containers/images"
	@echo "  docker-clean      Clean Docker containers and volumes only"
	@echo "  docker-clean-all  Clean ALL project Docker resources (containers, images, networks)"
	@echo
	@echo "📋 Development Assistance:"
	@echo "  prompt-backend    Copy backend code + docs to clipboard for LLM assistance"
	@echo "  prompt-frontend   Copy frontend code + docs to clipboard for LLM assistance"
	@echo "  prompt-o3-pro     Copy complete codebase + compressed docs for o3-pro analysis"

venv:  # Python 3.10.14
	@test -d $(VENV_DIR) || python3 -m venv $(VENV_DIR)
	@echo "Python venv created at $(VENV_DIR)"

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ./backend

install-test: install
	@echo "Installing test and dev dependencies..."
	@$(PIP) install -e './backend[test,dev]' > /dev/null 2>&1 || $(PIP) install -e './backend[test,dev]'

run-backend: install
	@echo "Starting backend (FastAPI)..."
	@bash -c "cd backend && source .env && source venv/bin/activate && uvicorn app.main:app --reload --app-dir ."

run-frontend:
	cd frontend && yarn install && yarn start

test: pytest test-frontend
	@echo "✅ All tests completed successfully!"

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && yarn test --watchAll=false

pytest: install-test
	@echo "Running all backend tests..."
	@bash -c "cd backend && source venv/bin/activate && pytest -v -n 10"

pytest-unit: install-test
	@echo "Running backend unit tests..."
	@bash -c "cd backend && source venv/bin/activate && pytest tests/unit/ -v -n 4"

pytest-integration: install-test
	@echo "Running backend integration tests..."
	@bash -c "cd backend && source venv/bin/activate && pytest tests/integration/ -v -n 8"

# Docker Compose detection - supports both docker-compose and docker compose
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; elif docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo ""; fi)

# Docker commands
docker-build:
	@echo "Building Docker images..."
	@if [ -z "$(DOCKER_COMPOSE)" ]; then echo "Error: Neither 'docker-compose' nor 'docker compose' found"; exit 1; fi
	$(DOCKER_COMPOSE) build

docker-up:
	@echo "Starting services with Docker Compose..."
	@if [ -z "$(DOCKER_COMPOSE)" ]; then echo "Error: Neither 'docker-compose' nor 'docker compose' found"; exit 1; fi
	$(DOCKER_COMPOSE) up -d

docker-logs:
	@echo "Showing Docker logs..."
	@if [ -z "$(DOCKER_COMPOSE)" ]; then echo "Error: Neither 'docker-compose' nor 'docker compose' found"; exit 1; fi
	$(DOCKER_COMPOSE) logs -f

docker-down:
	@echo "Stopping Docker services..."
	@if [ -z "$(DOCKER_COMPOSE)" ]; then echo "Error: Neither 'docker-compose' nor 'docker compose' found"; exit 1; fi
	$(DOCKER_COMPOSE) down

docker-clean:
	@echo "Cleaning up project Docker resources..."
	@if [ -z "$(DOCKER_COMPOSE)" ]; then echo "Error: Neither 'docker-compose' nor 'docker compose' found"; exit 1; fi
	$(DOCKER_COMPOSE) down -v --rmi local --remove-orphans

docker-clean-all:
	@echo "🧹 Completely resetting ALL project Docker resources..."
	@if [ -z "$(DOCKER_COMPOSE)" ]; then echo "Error: Neither 'docker-compose' nor 'docker compose' found"; exit 1; fi
	@echo "Stopping and removing containers..."
	-$(DOCKER_COMPOSE) down -v --remove-orphans
	@echo "Removing project images..."
	-docker rmi agentic-backend agentic-frontend 2>/dev/null || true
	@echo "Removing project network..."
	-docker network rm agentic-ai-network 2>/dev/null || true
	@echo "Removing project volumes..."
	-docker volume rm agentic-ai-backend-cache 2>/dev/null || true
	@echo "✅ All project Docker resources cleaned!"

# Code Quality Commands
format:
	@echo "🎨 Formatting all code..."
	@echo "📝 Formatting Python code (black + isort)..."
	@bash -c "cd backend && source venv/bin/activate && black --line-length 120 --exclude venv . && isort --profile black --line-length 120 --skip-glob venv ."
	@echo "📝 Formatting Frontend code (prettier)..."
	@cd frontend && yarn prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}" || true
	@echo "✅ All code formatted!"

lint:
	@echo "🔍 Linting all code..."
	@echo "🐍 Linting Python code..."
	@bash -c "cd backend && source venv/bin/activate && flake8 --max-line-length 120 --extend-ignore E203,W503 --exclude=venv . && pylint --max-line-length 120 --disable=C0114,C0115,C0116 app/ || true"
	@echo "⚛️ Linting Frontend code..."
	@cd frontend && yarn eslint "src/**/*.{ts,tsx}" --max-warnings 0 || true
	@echo "✅ All code linted!"

clean: docker-clean-all
	@echo "🧹 Full cleanup: Docker + local artifacts..."
	rm -rf $(VENV_DIR) __pycache__ backend/__pycache__ backend/app/__pycache__ frontend/node_modules .pytest_cache
	@echo "✅ Complete cleanup finished!"

docker-restart:
	@echo "Restarting Docker services..."
	@if [ -z "$(DOCKER_COMPOSE)" ]; then echo "Error: Neither 'docker-compose' nor 'docker compose' found"; exit 1; fi
	$(DOCKER_COMPOSE) restart

docker-shell-backend:
	@echo "Opening shell in backend container..."
	@if [ -z "$(DOCKER_COMPOSE)" ]; then echo "Error: Neither 'docker-compose' nor 'docker compose' found"; exit 1; fi
	$(DOCKER_COMPOSE) exec backend /bin/bash

docker-shell-frontend:
	@echo "Opening shell in frontend container..."
	@if [ -z "$(DOCKER_COMPOSE)" ]; then echo "Error: Neither 'docker-compose' nor 'docker compose' found"; exit 1; fi
	$(DOCKER_COMPOSE) exec frontend /bin/sh

docker-status:
	@echo "Docker Compose command detected: $(DOCKER_COMPOSE)"
	@if [ -n "$(DOCKER_COMPOSE)" ]; then echo "✅ Ready to use Docker Compose"; else echo "❌ Docker Compose not available"; fi

prompt-backend:
	@echo "Copying system.md, plan.md, langgraph-llms-short.md, Makefile, and all backend .py files to clipboard"
	@bash -c 'content=$$(cat $(PROMPT_SYSTEM); echo -e "\n\n"; cat $(PROMPT_PLAN); echo -e "\n\n"; cat $(PROMPT_LANGGRAPH_SHORT); echo -e "\n\n"; echo "# Makefile"; echo; cat Makefile; echo -e "\n\n"; find backend -name "*.py" -not -path "*/venv/*" -exec cat {} +); echo "$$content" | xclip -selection c; echo "Lines copied: $$(echo "$$content" | wc -l)"'

prompt-frontend:
	@echo "Copying system.md, plan.md, langgraphjs-llms-short.md, Makefile, and all frontend .ts/.tsx files to clipboard"
	@bash -c 'content=$$(cat $(PROMPT_SYSTEM); echo -e "\n\n"; cat $(PROMPT_PLAN); echo -e "\n\n"; cat $(PROMPT_LANGGRAPHJS_SHORT); echo -e "\n\n"; echo "# Makefile"; echo; cat Makefile; echo -e "\n\n"; find frontend/src -name "*.ts" -o -name "*.tsx" -exec cat {} +); echo "$$content" | xclip -selection c; echo "Lines copied: $$(echo "$$content" | wc -l)"'

prompt-o3-pro:
	@echo "Copying all backend and frontend code files + compressed docs + Makefile for o3-pro analysis"
	@bash -c 'content=$$(echo "# Compressed Documentation"; echo; \
		cat docs/prompts/compressed_docs.md; echo -e "\n\n"; \
		echo "# System Prompt"; echo; cat $(PROMPT_SYSTEM); echo -e "\n\n"; \
		echo "# Plan Prompt"; echo; cat $(PROMPT_PLAN); echo -e "\n\n"; \
		echo "# Makefile"; echo; cat Makefile; echo -e "\n\n"; \
		echo "# Backend Python Files"; echo; \
		find backend -name "*.py" -not -path "*/venv/*" -exec cat {} +; echo -e "\n\n"; \
		echo "# Frontend TypeScript/React Files"; echo; \
		find frontend/src -name "*.ts" -o -name "*.tsx" -exec cat {} +); \
		echo "$$content" | xclip -selection c; echo "Lines copied: $$(echo "$$content" | wc -l)"; \
		echo "Complete codebase + compressed docs + Makefile copied for o3-pro analysis"'
