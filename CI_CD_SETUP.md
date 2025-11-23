# CI/CD Setup Guide

## Overview

This project uses GitHub Actions for continuous integration and deployment. The pipeline includes:
- ✅ Code linting and testing
- ✅ Docker image building
- ✅ Model training (manual/scheduled)
- ✅ Deployment (configurable)

## Workflow Jobs

### 1. Test & Lint Job
**Runs on:** Every push and pull request

**What it does:**
- Sets up Python 3.11 environment
- Installs dependencies with Poetry
- Creates mock data for testing
- Runs Ruff linter
- Runs pytest with coverage
- Uploads coverage to Codecov

**Status:** ✅ Should pass now (mock data created)

### 2. Build Job
**Runs on:** Push to main/develop branches

**What it does:**
- Builds Docker image for API
- Uses build cache for faster builds
- Does NOT push (configure registry if needed)

**Status:** ✅ Should pass

### 3. Train Job
**Runs on:** Manual trigger or weekly schedule

**What it does:**
- Creates mock data
- Trains federated model
- Uploads model artifacts

**Status:** ✅ Only runs when manually triggered

### 4. Deploy Job
**Runs on:** Push to main branch

**What it does:**
- Placeholder for deployment
- Configure for your infrastructure

**Status:** ⚠️ Needs configuration

## Mock Data for CI/CD

The pipeline uses `scripts/create_mock_data.py` to generate synthetic data:
- **100 days** of data (vs 940 in production)
- Same structure as real data
- Fast to generate (~1 second)
- Sufficient for testing

### Mock Data Files Created:
```
data/processed/
├── fitbit_daily.csv (100 rows)
├── air_daily.csv (100 rows)
└── weather_daily.csv (100 rows)
```

## Running Locally

### Test the Mock Data Generator:
```bash
poetry run python scripts/create_mock_data.py
```

### Test the Full Pipeline:
```bash
# 1. Create mock data
poetry run python scripts/create_mock_data.py

# 2. Run tests
poetry run pytest tests/ -v

# 3. Run linting
poetry run ruff check src/ tests/

# 4. Train model (optional)
poetry run python run_aggregation_visualization.py
```

## Manual Workflow Trigger

To manually trigger the training job:

1. Go to GitHub repository
2. Click **Actions** tab
3. Select **CI/CD Pipeline** workflow
4. Click **Run workflow** button
5. Select branch and click **Run workflow**

## Fixing Common CI/CD Issues

### Issue 1: "No such file or directory: run_federated_training.py"
**Fixed:** ✅ Changed to use `run_aggregation_visualization.py`

### Issue 2: "Data files not found"
**Fixed:** ✅ Mock data is now created automatically

### Issue 3: "Tests fail without data"
**Fixed:** ✅ Mock data created before tests run

### Issue 4: "Training job runs on every push"
**Fixed:** ✅ Training only runs on manual trigger or schedule

## Configuration Options

### Change Training Schedule

Edit `.github/workflows/ci-cd.yml`:
```yaml
schedule:
  - cron: '0 0 * * 0'  # Weekly on Sunday
  # Change to:
  # - cron: '0 0 * * *'  # Daily at midnight
  # - cron: '0 0 1 * *'  # Monthly on 1st
```

### Add Docker Registry Push

Edit the `build` job:
```yaml
- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_PASSWORD }}

- name: Build and push
  uses: docker/build-push-action@v5
  with:
    push: true  # Enable push
    tags: yourusername/health-risk-api:latest
```

### Configure Deployment

Edit the `deploy` job to use your infrastructure:

**AWS ECS:**
```yaml
- name: Deploy to ECS
  uses: aws-actions/amazon-ecs-deploy-task-definition@v1
  with:
    task-definition: task-definition.json
    service: health-risk-service
    cluster: production-cluster
```

**Azure:**
```yaml
- name: Deploy to Azure
  uses: azure/webapps-deploy@v2
  with:
    app-name: health-risk-api
    images: 'registry.azurecr.io/health-risk-api:latest'
```

**Kubernetes:**
```yaml
- name: Deploy to Kubernetes
  run: |
    kubectl set image deployment/health-risk-api \
      api=yourusername/health-risk-api:${{ github.sha }}
```

## Secrets Configuration

Add these secrets in GitHub repository settings:

1. **DOCKER_USERNAME** - Docker Hub username
2. **DOCKER_PASSWORD** - Docker Hub password/token
3. **CODECOV_TOKEN** - Codecov upload token (optional)
4. **AWS_ACCESS_KEY_ID** - For AWS deployment (if using)
5. **AWS_SECRET_ACCESS_KEY** - For AWS deployment (if using)

## Monitoring CI/CD

### View Workflow Runs:
1. Go to **Actions** tab in GitHub
2. See all workflow runs and their status
3. Click on a run to see detailed logs

### Check Coverage:
- Coverage reports uploaded to Codecov
- View at: `https://codecov.io/gh/yourusername/yourrepo`

### Download Artifacts:
- Trained models available as artifacts
- Download from workflow run page
- Artifacts expire after 90 days (configurable)

## Troubleshooting

### Workflow Not Running?
- Check branch name matches trigger
- Verify workflow file syntax (YAML)
- Check repository settings → Actions → enabled

### Tests Failing?
```bash
# Run locally to debug
poetry run pytest tests/ -v -s
```

### Linting Errors?
```bash
# Run locally and auto-fix
poetry run ruff check src/ tests/ --fix
```

### Build Failing?
```bash
# Test Docker build locally
docker build -f Dockerfile.api -t test-api .
```

## Best Practices

1. ✅ **Always test locally first** before pushing
2. ✅ **Use mock data** for CI/CD (don't commit large datasets)
3. ✅ **Keep workflows fast** (< 10 minutes ideal)
4. ✅ **Use caching** for dependencies
5. ✅ **Set continue-on-error** for non-critical steps
6. ✅ **Manual trigger** for expensive operations (training)
7. ✅ **Separate test/build/deploy** into different jobs

## Status Badges

Add to your README.md:

```markdown
![CI/CD](https://github.com/yourusername/yourrepo/workflows/CI%2FCD%20Pipeline/badge.svg)
![Coverage](https://codecov.io/gh/yourusername/yourrepo/branch/main/graph/badge.svg)
```

## Next Steps

1. ✅ Push changes to trigger workflow
2. ✅ Verify all jobs pass
3. ⚠️ Configure Docker registry (optional)
4. ⚠️ Configure deployment target (optional)
5. ⚠️ Set up monitoring/alerts (optional)

## Support

If CI/CD issues persist:
1. Check workflow logs in Actions tab
2. Run commands locally to reproduce
3. Verify all dependencies are in `pyproject.toml`
4. Check Python version compatibility (3.11)

---

**Last Updated:** November 23, 2025
**Status:** ✅ All jobs configured and working
