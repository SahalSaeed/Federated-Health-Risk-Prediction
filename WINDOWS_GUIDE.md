# 🪟 Windows User Guide

## Quick Start for Windows

Since `make` is not available on Windows by default, use the PowerShell script instead.

---

## 🚀 Quick Start (3 Steps)

```powershell
# 1. Install dependencies
.\run.ps1 install

# 2. Verify system
.\run.ps1 verify

# 3. Start all services
.\run.ps1 docker-up
```

---

## 📋 Available Commands

```powershell
# View all commands
.\run.ps1 help

# Development
.\run.ps1 install              # Install dependencies
.\run.ps1 test                 # Run tests
.\run.ps1 lint                 # Run linters
.\run.ps1 format               # Format code

# Services
.\run.ps1 api                  # Run API (port 8000)
.\run.ps1 dashboard-authority  # Authority dashboard (port 8501)
.\run.ps1 dashboard-citizen    # Citizen dashboard (port 8502)

# Docker
.\run.ps1 docker-build         # Build images
.\run.ps1 docker-up            # Start all services
.\run.ps1 docker-down          # Stop all services
.\run.ps1 docker-logs          # View logs

# Training & Testing
.\run.ps1 train                # Run training
.\run.ps1 evaluate             # Run evaluation
.\run.ps1 drift-check          # Check drift
.\run.ps1 verify               # Verify system

# Monitoring
.\run.ps1 prometheus           # Open Prometheus
.\run.ps1 grafana              # Open Grafana

# Cleanup
.\run.ps1 clean                # Clean temp files
```

---

## 🔧 Alternative: Direct Commands

If you prefer, you can run commands directly:

```powershell
# Install
poetry install

# Verify
poetry run python scripts\verify_system.py

# Start API
poetry run python -m uvicorn federated_health_risk.services.inference_api:app --reload

# Start dashboards
poetry run streamlit run dashboards\authority_app\app.py --server.port 8501
poetry run streamlit run dashboards\citizen_app\app.py --server.port 8502

# Docker
docker-compose up -d
docker-compose down
docker-compose logs -f

# Training
poetry run python scripts\run_federated_training.py

# Drift check
poetry run python scripts\test_drift_detection.py
```

---

## ✅ Verification

```powershell
.\run.ps1 verify
```

Expected output: ✅ ALL CHECKS PASSED

---

## 🌐 Access Services

After running `.\run.ps1 docker-up`:

- API: http://localhost:8000/docs
- Authority Dashboard: http://localhost:8501
- Citizen Dashboard: http://localhost:8502
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

---

## 🐛 Troubleshooting

### PowerShell Execution Policy

If you get "script execution is disabled":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Already in Use

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F
```

---

**For complete documentation, see [PROJECT_REPORT.md](PROJECT_REPORT.md)**
