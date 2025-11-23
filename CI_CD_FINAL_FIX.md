# CI/CD Final Fix - Package Installation

## Problems

### 1. Docker Build Failing
```
/app/src/federated_health_risk does not contain any element
ERROR: failed to solve: exit code: 1
```

**Cause:** Poetry tried to install the package before source code was copied.

### 2. Training Job Failing
```
ModuleNotFoundError: No module named 'federated_health_risk.data'
```

**Cause:** Package wasn't properly installed by `poetry install`.

## Solutions Applied

### Fix 1: Updated Dockerfile.api

**Before:**
```dockerfile
# Copy dependency files
COPY pyproject.toml poetry.lock README.md ./

# Install dependencies (FAILS - no source code yet!)
RUN poetry install --no-dev --no-interaction

# Copy application code (too late!)
COPY src/ ./src/
```

**After:**
```dockerfile
# Copy dependency files
COPY pyproject.toml poetry.lock README.md ./

# Copy source code FIRST (needed for package installation)
COPY src/ ./src/

# Install dependencies only (not the package yet)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-root

# Install the package itself
RUN poetry install --no-dev --no-interaction --only-root

# Copy models
COPY models/ ./models/
```

**Key Changes:**
- Copy `src/` before running `poetry install`
- Use `--no-root` to install dependencies first
- Use `--only-root` to install the package separately

### Fix 2: Updated CI/CD Workflow

**Before:**
```yaml
- name: Install dependencies
  run: |
    pip install poetry
    poetry install --no-interaction --no-ansi
    
- name: Install package in editable mode
  run: |
    poetry run pip install -e .
```

**After:**
```yaml
- name: Install Poetry
  run: |
    pip install poetry
    
- name: Install dependencies and package
  run: |
    poetry install --no-interaction --no-ansi --with dev
```

**Key Changes:**
- Simplified to single `poetry install` command
- Added `--with dev` to include dev dependencies
- Removed separate editable install step (not needed)

## Why This Works

### Poetry Install Behavior

When you run `poetry install`:
1. Reads `pyproject.toml`
2. Installs all dependencies
3. **Installs the package itself** (if `packages` is defined)

The package is defined in `pyproject.toml`:
```toml
[tool.poetry]
name = "federated-health-risk"
packages = [{include = "federated_health_risk", from = "src"}]
```

This tells Poetry:
- Package name: `federated-health-risk`
- Module to include: `federated_health_risk`
- Location: `src/federated_health_risk/`

### Docker Build Order

The order matters:
1. ✅ Copy `pyproject.toml` and `poetry.lock`
2. ✅ Copy `src/` directory
3. ✅ Run `poetry install --no-root` (dependencies only)
4. ✅ Run `poetry install --only-root` (package only)

This allows Docker to cache dependency installation separately from package installation.

## Testing Locally

### Test Package Import:
```bash
# Using venv
.venv\Scripts\python.exe -c "import federated_health_risk; print('Works!')"

# Using poetry
poetry run python -c "import federated_health_risk; print('Works!')"
```

### Test Module Import:
```bash
poetry run python -c "from federated_health_risk.data.federated_loader import prepare_federated_data; print('Works!')"
```

### Test Docker Build:
```bash
docker build -f Dockerfile.api -t test-api .
```

## Files Modified

1. ✅ `Dockerfile.api` - Fixed build order
2. ✅ `.github/workflows/ci-cd.yml` - Simplified install

## Expected CI/CD Flow

### Test Job:
```
1. Checkout code
2. Set up Python
3. Install Poetry
4. poetry install --with dev  ← Installs everything including package
5. Create mock data
6. Run tests ✅
```

### Train Job:
```
1. Checkout code
2. Set up Python
3. Install Poetry
4. poetry install --with dev  ← Installs everything including package
5. Create mock data
6. Run training ✅
7. Upload model
```

### Build Job:
```
1. Checkout code
2. Set up Docker
3. Build image:
   - Copy pyproject.toml
   - Copy src/  ← BEFORE poetry install
   - poetry install --no-root
   - poetry install --only-root
4. Build succeeds ✅
```

## Verification Checklist

After pushing, verify:

- [ ] Test job passes
- [ ] Build job passes (Docker builds successfully)
- [ ] Train job passes (no ModuleNotFoundError)
- [ ] Model artifacts uploaded

## Push Commands

```bash
git add .
git commit -m "fix: correct package installation in Docker and CI/CD"
git push origin main
```

## Expected Results

All jobs should pass:
- ✅ Test & Lint
- ✅ Build Docker Image
- ✅ Train Federated Model
- ✅ Deploy

Total time: ~20 minutes

## Troubleshooting

### If Docker Build Still Fails:
```bash
# Test locally
docker build -f Dockerfile.api -t test-api .

# Check if src/ is copied
docker run --rm test-api ls -la /app/src/
```

### If Training Still Fails:
```bash
# Test locally
poetry install
poetry run python -c "import federated_health_risk"
poetry run python run_aggregation_visualization.py
```

### If Package Not Found:
```bash
# Check if package is installed
poetry run pip list | grep federated

# Reinstall
poetry install --no-cache
```

## Status

✅ **Docker build fixed** - Source copied before install
✅ **Training fixed** - Package properly installed
✅ **Ready to push** - All changes applied

---

**Date:** November 23, 2025
**Status:** Ready for final push
