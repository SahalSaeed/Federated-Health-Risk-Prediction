# PowerShell script for Windows users (alternative to Makefile)
# Usage: .\run.ps1 <command>

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host "Federated Health Risk MLOps - Available Commands" -ForegroundColor Cyan
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\run.ps1 <command>" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Development:" -ForegroundColor Green
    Write-Host "  install              Install dependencies with Poetry"
    Write-Host "  test                 Run tests with coverage"
    Write-Host "  lint                 Run linters (Ruff)"
    Write-Host "  format               Format code (Black + Ruff)"
    Write-Host ""
    Write-Host "Services (Local):" -ForegroundColor Green
    Write-Host "  api                  Run FastAPI inference service (port 8000)"
    Write-Host "  dashboard-authority  Run authority dashboard (port 8501)"
    Write-Host "  dashboard-citizen    Run citizen dashboard (port 8502)"
    Write-Host ""
    Write-Host "Docker (All Services):" -ForegroundColor Green
    Write-Host "  docker-build         Build all Docker images"
    Write-Host "  docker-up            Start all services"
    Write-Host "  docker-down          Stop all services"
    Write-Host "  docker-logs          View logs from all containers"
    Write-Host "  docker-restart       Restart all services"
    Write-Host ""
    Write-Host "Training & Evaluation:" -ForegroundColor Green
    Write-Host "  train                Run federated training"
    Write-Host "  evaluate             Run model evaluation notebook"
    Write-Host "  visualize-aggregation Visualize weight aggregation impact"
    Write-Host ""
    Write-Host "Monitoring:" -ForegroundColor Green
    Write-Host "  drift-check          Check for data drift"
    Write-Host "  prometheus           Open Prometheus"
    Write-Host "  grafana              Open Grafana"
    Write-Host ""
    Write-Host "Cleanup:" -ForegroundColor Green
    Write-Host "  clean                Clean temporary files and caches"
    Write-Host ""
    Write-Host "Data Preparation:" -ForegroundColor Green
    Write-Host "  prepare-data         Prepare per-node data (clip to 940 rows, no centralization)"
    Write-Host ""
    Write-Host "Verification:" -ForegroundColor Green
    Write-Host "  verify               Verify system setup"
    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Cyan
}

switch ($Command.ToLower()) {
    "help" {
        Show-Help
    }
    
    "install" {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        poetry install
    }
    
    "test" {
        Write-Host "Running tests..." -ForegroundColor Yellow
        poetry run pytest tests/ -v --cov=src --cov-report=term-missing
    }
    
    "lint" {
        Write-Host "Running linters..." -ForegroundColor Yellow
        poetry run ruff check src/ tests/
    }
    
    "format" {
        Write-Host "Formatting code..." -ForegroundColor Yellow
        poetry run black src/ tests/
        poetry run ruff check --fix src/ tests/
    }
    
    "api" {
        Write-Host "Starting FastAPI service on http://localhost:8000" -ForegroundColor Green
        Write-Host "API docs available at http://localhost:8000/docs" -ForegroundColor Green
        poetry run python -m uvicorn federated_health_risk.services.inference_api:app --reload --host 0.0.0.0 --port 8000
    }
    
    "dashboard-authority" {
        Write-Host "Starting Authority Dashboard on http://localhost:8501" -ForegroundColor Green
        poetry run streamlit run dashboards/authority_app/app.py --server.port 8501
    }
    
    "dashboard-citizen" {
        Write-Host "Starting Citizen Dashboard on http://localhost:8502" -ForegroundColor Green
        poetry run streamlit run dashboards/citizen_app/app.py --server.port 8502
    }
    
    "docker-build" {
        Write-Host "Building Docker images..." -ForegroundColor Yellow
        docker-compose build
    }
    
    "docker-up" {
        Write-Host "Starting all services..." -ForegroundColor Green
        Write-Host "  - API: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "  - Authority Dashboard: http://localhost:8501" -ForegroundColor Cyan
        Write-Host "  - Citizen Dashboard: http://localhost:8502" -ForegroundColor Cyan
        Write-Host "  - Prometheus: http://localhost:9090" -ForegroundColor Cyan
        Write-Host "  - Grafana: http://localhost:3000 (admin/admin)" -ForegroundColor Cyan
        docker-compose up -d
    }
    
    "docker-down" {
        Write-Host "Stopping all services..." -ForegroundColor Yellow
        docker-compose down
    }
    
    "docker-logs" {
        Write-Host "Viewing logs..." -ForegroundColor Yellow
        docker-compose logs -f
    }
    
    "docker-restart" {
        Write-Host "Restarting services..." -ForegroundColor Yellow
        docker-compose restart
    }
    
    "train" {
        Write-Host "Running federated training..." -ForegroundColor Yellow
        poetry run python scripts/run_federated_training.py
    }
    
    "evaluate" {
        Write-Host "Running model evaluation..." -ForegroundColor Yellow
        poetry run jupyter nbconvert --execute --to notebook notebooks/06_model_evaluation.ipynb
    }
    
    "visualize-aggregation" {
        Write-Host "Running weight aggregation visualization..." -ForegroundColor Yellow
        Write-Host "This will train a federated model and show how aggregation improves performance" -ForegroundColor Cyan
        poetry run python run_aggregation_visualization.py
    }
    
    "drift-check" {
        Write-Host "Checking for data drift..." -ForegroundColor Yellow
        poetry run python scripts/test_drift_detection.py
    }
    
    "prometheus" {
        Write-Host "Opening Prometheus..." -ForegroundColor Green
        Start-Process "http://localhost:9090"
    }
    
    "grafana" {
        Write-Host "Opening Grafana (admin/admin)..." -ForegroundColor Green
        Start-Process "http://localhost:3000"
    }
    
    "clean" {
        Write-Host "Cleaning temporary files..." -ForegroundColor Yellow
        Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Include *.pyc -Recurse -Force | Remove-Item -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Include *.egg-info -Recurse -Force | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Include .pytest_cache -Recurse -Force | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Include .ruff_cache -Recurse -Force | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
        Write-Host "Cleanup complete!" -ForegroundColor Green
    }
    
    "verify" {
        Write-Host "Verifying system setup..." -ForegroundColor Yellow
        poetry run python scripts/verify_system.py
    }
    
    "prepare-data" {
        Write-Host "Preparing per-node data (no centralization)..." -ForegroundColor Yellow
        poetry run python scripts/prepare_node_data.py
    }
    
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
    }
}
