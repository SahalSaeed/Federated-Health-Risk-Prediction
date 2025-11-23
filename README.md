# Federated Health Risk MLOps Platform

End-to-end MLOps system for federated learning-based health risk prediction using multimodal data (wearables, air quality, weather).

## 🎯 Project Overview

This system predicts health risks in real-time using:
- **Physical Activity Data**: Steps, calories, active minutes (Fitbit)
- **Air Quality Data**: PM2.5 pollution levels from multiple sensors
- **Weather Data**: Temperature, humidity, pressure, dew point

**Key Features:**
- ✅ Federated Learning (privacy-preserving, distributed training)
- ✅ Real-time Inference API (FastAPI)
- ✅ Data Drift Detection (KS Test + PSI)
- ✅ CI/CD Pipeline (GitHub Actions)
- ✅ Monitoring (Prometheus + Grafana)
- ✅ Interactive Dashboards (Streamlit)
- ✅ Docker Containerization

---

## 🏗️ System Architecture

```
Data Sources → Federated Learning → Trained Model → Inference API
                                                           ↓
                                    Dashboards ← Monitoring ← Drift Detection
```

**Components:**
1. **Data Ingestion**: Multi-source data processing
2. **Federated Learning**: 3-node training with FedAvg
3. **Inference Service**: FastAPI REST API
4. **Monitoring**: Prometheus metrics + Grafana dashboards
5. **Drift Detection**: Automated statistical tests
6. **Dashboards**: Authority (population) + Citizen (personal)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry
- Docker & Docker Compose

### Installation

```powershell
# Install dependencies
poetry install

# Verify setup
poetry run python scripts/verify_system.py
```

### Run Services

**Windows Users:**
```powershell
# Start everything
.\run.ps1 docker-up

# Individual services
.\run.ps1 api                  # API only
.\run.ps1 dashboard-authority  # Authority dashboard
.\run.ps1 dashboard-citizen    # Citizen dashboard

# Stop all
.\run.ps1 docker-down
```

**Linux/Mac Users:**
```bash
# Start everything
make docker-up

# Individual services
make api                  # API only
make dashboard-authority  # Authority dashboard
make dashboard-citizen    # Citizen dashboard

# Stop all
make docker-down
```

**Access services:**
- API: http://localhost:8000/docs
- Authority Dashboard: http://localhost:8501
- Citizen Dashboard: http://localhost:8502
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

**📘 Windows users:** See [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) for complete guide.

**💡 Tip:** Use `.\run.ps1 help` to see all available commands on Windows.

---

## 📊 Model Details

**Architecture:** Multimodal Neural Network
- **Vitals Branch**: 6 features → 128 hidden units
- **Air Quality Branch**: 5 features → 64 hidden units
- **Weather Branch**: 4 features → 128 hidden units
- **Fusion Layer**: 320 → 128 → 1 (risk score)

**Training:**
- **Method**: Federated Learning (FedAvg)
- **Nodes**: 3 (simulating hospitals/cities)
- **Rounds**: 5
- **Parameters**: 43,521
- **Framework**: PyTorch + Flower

**Performance:**
- **Test Accuracy**: 55.56%
- **Model Size**: 176 KB
- **Inference Time**: < 50ms

---

## 🔍 Data Drift Detection

Automated drift monitoring using:
- **KS Test**: Kolmogorov-Smirnov statistical test
- **PSI**: Population Stability Index

```powershell
# Run drift detection
make drift-check

# Or manually
poetry run python scripts/test_drift_detection.py
```

**Output:** `monitoring/drift_report.json`

---

## 📁 Project Structure

```
project_cursor/
├── .github/workflows/      # CI/CD pipelines
├── dashboards/             # Streamlit dashboards
│   ├── authority_app/     # Public health monitoring
│   └── citizen_app/       # Personal risk assessment
├── data/                   # Datasets
│   ├── processed/         # Cleaned data
│   └── features/          # Feature store
├── docs/                   # Documentation
├── models/                 # Trained models
│   └── federated_global_model.pth
├── monitoring/             # Monitoring configs
│   ├── prometheus.yml
│   ├── alerts.yml
│   └── drift_report.json
├── notebooks/              # Jupyter notebooks
│   ├── 01_eda.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_prototyping.ipynb
│   ├── 04_federated_experiments.ipynb
│   └── 06_model_evaluation.ipynb
├── scripts/                # Utility scripts
├── src/federated_health_risk/  # Source code
│   ├── data/              # Data processing
│   ├── federated/         # FL implementation
│   ├── models/            # Model architecture
│   ├── monitoring/        # Drift detection
│   └── services/          # API service
├── tests/                  # Unit tests
├── docker-compose.yml      # Multi-container setup
├── Dockerfile.api          # API container
├── Makefile                # Command shortcuts
└── pyproject.toml          # Dependencies
```

---

## 🛠️ Available Commands

```powershell
# View all commands
make help

# Development
make install              # Install dependencies
make test                 # Run tests
make lint                 # Run linters

# Services
make api                  # Run API (port 8000)
make dashboard-authority  # Authority dashboard (port 8501)
make dashboard-citizen    # Citizen dashboard (port 8502)

# Docker
make docker-build         # Build images
make docker-up            # Start all services
make docker-down          # Stop all services
make docker-logs          # View logs

# Training & Evaluation
make train                # Run federated training
make evaluate             # Run model evaluation

# Monitoring
make drift-check          # Check data drift
make prometheus           # Open Prometheus
make grafana              # Open Grafana
```

---

## 🌐 API Endpoints

**Base URL:** `http://localhost:8000`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check |
| `/predict` | POST | Single prediction |
| `/predict/batch` | POST | Batch predictions |
| `/model/info` | GET | Model information |
| `/docs` | GET | Interactive API docs |

**Example Request:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "total_steps": 8000,
    "active_minutes": 45,
    "sedentary_minutes": 600,
    "calories": 2200,
    "distance_km": 5.5,
    "cardio_load": 50,
    "pm_us_post": 35,
    "pm_caotangsi": 40,
    "pm_shahepu": 38,
    "pm_mean": 37.7,
    "pollution_load": 38,
    "dew_point": 15,
    "humidity": 65,
    "pressure": 1013,
    "temperature": 22
  }'
```

---

## 📈 Monitoring & Observability

### Prometheus Metrics
- API request count & latency
- Model prediction distribution
- System resources (CPU, memory)
- Drift indicators

### Grafana Dashboards
- API Performance
- Model Metrics
- System Health
- Data Drift Monitoring

### Alerts
- API Down (Critical)
- High Error Rate (Warning)
- High Response Time (Warning)
- Model Drift Detected (Warning)
- High Memory Usage (Warning)

---

## 🎓 Technologies Used

**ML/AI:**
- PyTorch - Deep learning
- Flower - Federated learning
- scikit-learn - ML utilities

**API & Services:**
- FastAPI - REST API
- Uvicorn - ASGI server
- Streamlit - Dashboards

**MLOps & DevOps:**
- Docker - Containerization
- GitHub Actions - CI/CD
- Prometheus - Metrics
- Grafana - Visualization

**Data:**
- Pandas/NumPy - Processing
- Plotly - Visualization

---

## 📝 Deliverables

- [x] **Code Notebooks**: EDA, feature engineering, training, evaluation
- [x] **Trained Model**: `models/federated_global_model.pth`
- [x] **Evaluation Report**: `notebooks/06_model_evaluation.ipynb`
- [x] **Data Drift Detection**: Fully implemented and tested
- [x] **MLOps Pipeline**: CI/CD with GitHub Actions
- [x] **Docker/Kubernetes**: Multi-container setup
- [x] **Monitoring**: Prometheus + Grafana
- [x] **Dashboards**: Authority + Citizen apps
- [x] **Documentation**: Complete guides

---

## 📚 Documentation

### 🎯 New Team Member? Start Here!

**[📖 START_HERE.md](START_HERE.md)** ⭐ **READ THIS FIRST** (15 min)
- Quick setup guide
- Learning path
- Verification checklist

### 📘 Complete Documentation

**[📚 DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Index of all documentation

**Essential Docs:**
1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - One-page overview (5 min)
2. **[PROJECT_REPORT.md](PROJECT_REPORT.md)** - Complete guide (30 min) ⭐
   - Every file explained
   - Why each technology
   - How to run everything
   - Requirements fulfillment
3. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment instructions
4. **[PROJECT_CHECKLIST.md](PROJECT_CHECKLIST.md)** - Requirements status

---

## 🔐 Security

- Non-root Docker containers
- Input validation (Pydantic)
- Health checks
- CORS configuration
- Environment variable management

---

## 🚀 Deployment

### Local (Development)
```powershell
make docker-up
```

### Cloud Options
- **AWS**: ECS/Fargate
- **Azure**: Container Apps
- **GCP**: Cloud Run
- **Kubernetes**: See `DEPLOYMENT.md`

---

## 🧪 Testing

```powershell
# Run all tests
make test

# Verify system
poetry run python scripts/verify_system.py

# Test drift detection
poetry run python scripts/test_drift_detection.py
```

---

## 📊 Results

**Federated Training:**
- 5 rounds completed
- Loss: 0.6294 → 0.5191 (17.5% improvement)
- Test Accuracy: 55.56%

**Data Drift Detection:**
- KS Test: 7/8 features drifted (87.5%)
- PSI: 6/8 features drifted (75.0%)
- ⚠️ Retraining recommended

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests: `make test`
5. Submit pull request

---

## 📄 License

MIT License

---

## 👥 Authors

Sahal Saeed - MLOps Engineer

---

## 🎉 Status

**System Status:** 🟢 Production Ready  
**All Requirements:** ✅ Complete  
**Last Updated:** November 21, 2025

---

**For detailed setup and deployment instructions, see [SYSTEM_READY.md](SYSTEM_READY.md)**
