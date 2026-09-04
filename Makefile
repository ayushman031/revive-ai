# =============================================================================
# REVIVE — Development Makefile
# =============================================================================
# Common workflows for local development. Run `make help` to see all targets.

.PHONY: help up down build test lint backend-dev frontend-dev health

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# -- Docker Compose -----------------------------------------------------------

up: ## Start all services (Postgres, Redis, Backend, Frontend)
	docker compose up --build -d

down: ## Stop all services and remove containers
	docker compose down

build: ## Rebuild all Docker images without starting
	docker compose build

logs: ## Tail logs from all services
	docker compose logs -f

# -- Backend ------------------------------------------------------------------

backend-dev: ## Run backend locally (requires .env and active venv)
	cd backend && uvicorn app.main:app --reload --port 8000

test: ## Run backend test suite
	cd backend && python -m pytest -v

lint: ## Run ruff linter on backend code
	cd backend && python -m ruff check .

# -- Frontend -----------------------------------------------------------------

frontend-dev: ## Run frontend locally
	cd frontend && npm run dev

# -- Health Check -------------------------------------------------------------

health: ## Hit the backend health endpoint
	curl -s http://localhost:8000/health | python -m json.tool
