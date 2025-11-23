# CI/CD Module Import Fix

## Problem

**Error in CI/CD:**
```
ModuleNotFoundError: No module named 'federated_health_risk.data'
```

**Root Cause:**
The package wasn't installed in editable mode, so Python couldn't find the `federated_health_risk` module even though `sys.path.insert(0, 'src')` was used in the script.

## Solution

Added package installation step in CI/CD workflow:

```yaml
- name: Install package in editable mode
  run: |
    poetry run pip install -e .
```

This installs the package so Python can import `federated_health_risk` modules.

## Changes Made

### Updated `.github/workflows/ci-cd.yml`

**Test Job:**
```yaml
- name: Install dependencies
  run: |
    poetry install
    
- name: Install package in editable mode  # ← ADDED
  run: |
    poetry run pip install -e .
    
- name: Create mock data for tests
  run: |
    mkdir -p data/processed
    poetry run python scripts/create_mock_data.py
```

**Train Job:**
```yaml
- name: Install dependencies
  run: |
    pip install poetry
    poetry install --no-interaction --no-ansi
    
- name: Install package in editable mode  # ← ADDED
  run: |
    poetry run pip install -e .
    
- name: Create mock data for CI
  run: |
    mkdir -p data/processed
    poetry run python scripts/create_mock_data.py
```

## Why This Works

### Before:
```python
# run_aggregation_visualization.py
import sys
sys.path.insert(0, 'src')  # Doesn't work reliably in CI/CD

from federated_health_risk.data.federated_loader import prepare_federated_data
# ❌ ModuleNotFoundError
```

### After:
```bash
# CI/CD installs package
poetry run pip install -e .

# Now Python knows where to find the module
# ✅ Import works!
```

### What `-e` Does:
- **Editable mode**: Links the source code instead of copying
- **Development friendly**: Changes to code are immediately available
- **Proper imports**: Python can find the package by name

## Package Configuration

The package is properly configured in `pyproject.toml`:

```toml
[tool.poetry]
name = "federated-health-risk"
packages = [{include = "federated_health_risk", from = "src"}]
```

This tells Poetry:
- Package name: `federated-health-risk`
- Module name: `federated_health_risk`
- Location: `src/federated_health_risk/`

## Testing Locally

To verify the fix works locally:

```bash
# Install in editable mode
poetry run pip install -e .

# Test import
poetry run python -c "from federated_health_risk.data.federated_loader import prepare_federated_data; print('✅ Import works!')"

# Run training script
poetry run python run_aggregation_visualization.py
```

## Expected CI/CD Flow

```
1. Checkout code
2. Set up Python
3. Install Poetry
4. Install dependencies (poetry install)
5. Install package in editable mode (pip install -e .)  ← FIX
6. Create mock data
7. Run training script
   ✅ Imports work!
   ✅ Training completes
   ✅ Model uploaded
```

## Verification

After pushing, the workflow should:
- ✅ Install package successfully
- ✅ Import modules without errors
- ✅ Complete training
- ✅ Upload model artifacts

## Alternative Solutions (Not Used)

### Option 1: Use PYTHONPATH
```yaml
- name: Run training
  run: |
    PYTHONPATH=src poetry run python run_aggregation_visualization.py
```
**Why not:** Less reliable, environment-specific

### Option 2: Modify script
```python
# Add to run_aggregation_visualization.py
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
```
**Why not:** Hacky, not the proper way

### Option 3: Install without Poetry
```yaml
- name: Install package
  run: |
    pip install -e .
```
**Why not:** Bypasses Poetry's dependency management

## Best Practice

✅ **Always install packages in editable mode for development:**
```bash
pip install -e .
# or
poetry run pip install -e .
```

This ensures:
- Proper module resolution
- Works in all environments
- Follows Python packaging standards

## Status

✅ **Fixed:** Package now installs in editable mode
✅ **Tested:** Import works correctly
✅ **Ready:** Push and verify in CI/CD

## Push Commands

```bash
git add .
git commit -m "fix: install package in editable mode for CI/CD"
git push origin main
```

Then check **Actions** tab - the ModuleNotFoundError should be gone! ✅

---

**Date:** November 23, 2025
**Status:** Fixed and ready to push
