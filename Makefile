.PHONY: help install test lint format clean docker-build docker-up docker-down api dashboard-authority dashboard-citizen train

help:
	@echo "==================================================================="
	@echo "Federated Health Risk MLOps - Available Commands"
	@echo "==================================================================="
	@echo ""
	@echo "Development:"
	@echo "  make install              Install dependencies with Poetry"
	@echo "  make test                 Run tests with coverage"
	@echo "  make lint                 Run linters (Ruff)"
	@echo "  make format               Format code (Black + Ruff)"
	@echo ""
	@echo "Services (Local):"
	@echo "  make api                  Run FastAPI inference service (port 8000)"
	@echo "  make dashboard-authority  Run authority dashboard (port 8501)"
	@echo "  make dashboard-citizen    Run citizen dashboard (port 8502)"
	@echo ""
	@echo "Docker (All Services):"
	@echo "  make docker-build         Build all Docker images"
	@echo "  make docker-up            Start all services (API + Dashboards + Monitoring)"
	@echo "  make docker-down          Stop all services"
	@echo "  make docker-logs          View logs from all containers"
	@echo "  make docker-restart       Restart all services"
	@echo ""
	@echo "Training & Evaluation:"
	@echo "  make train                Run federated training"
	@echo "  make evaluate             Run model evaluation notebook"
	@echo ""
	@echo "Monitoring:"
	@echo "  make drift-check          Check for data drift"
	@echo "  make prometheus           Open Prometheus (http://localhost:9090)"
	@echo "  make grafana              Open Grafana (http://localhost:3000)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                Clean temporary files and caches"
	@echo "==================================================================="

install:
	poetry install

test:
	poetry run pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	poetry run ruff check src/ tests/

format:
	poetry run black src/ tests/
	poetry run ruff check --fix src/ tests/

# Run services locally
api:
	@echo "Starting FastAPI service on http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"
	poetry run python -m uvicorn federated_health_risk.services.inference_api:app --reload --host 0.0.0.0 --port 8000

dashboard-authority:
	@echo "Starting Authority Dashboard on http://localhost:8501"
	poetry run streamlit run dashboards/authority_app/app.py --server.port 8501

dashboard-citizen:
	@echo "Starting Citizen Dashboard on http://localhost:8502"
	poetry run streamlit run dashboards/citizen_app/app.py --server.port 8502

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting all services..."
	@echo "  - API: http://localhost:8000"
	@echo "  - Authority Dashboard: http://localhost:8501"
	@echo "  - Citizen Dashboard: http://localhost:8502"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"
	docker-compose up -d

docker-down:
	@echo "Stopping all services..."
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

# Training
train:
	@echo "Running federated training..."
	poetry run python scripts/run_federated_training.py

evaluate:
	@echo "Running model evaluation..."
	poetry run jupyter nbconvert --execute --to notebook notebooks/06_model_evaluation.ipynb

# Monitoring
drift-check:
	@echo "Checking for data drift..."
	poetry run python -m federated_health_risk.monitoring.drift_detector

prometheus:
	@echo "Opening Prometheus..."
	@start http://localhost:9090 || open http://localhost:9090 || xdg-open http://localhost:9090

grafana:
	@echo "Opening Grafana (admin/admin)..."
	@start http://localhost:3000 || open http://localhost:3000 || xdg-open http://localhost:3000

# Cleanup
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup complete!"
