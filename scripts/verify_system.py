"""Verify that all system components are properly set up."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def check_files():
    """Check that all required files exist."""
    print("=" * 60)
    print("1. Checking Required Files...")
    print("=" * 60)
    
    required_files = [
        # Source code
        "src/federated_health_risk/data/federated_loader.py",
        "src/federated_health_risk/federated/client.py",
        "src/federated_health_risk/federated/server.py",
        "src/federated_health_risk/models/multimodal_model.py",
        "src/federated_health_risk/monitoring/drift_detector.py",
        "src/federated_health_risk/services/inference_api.py",
        
        # Docker
        "Dockerfile.api",
        "docker-compose.yml",
        
        # Dashboards
        "dashboards/authority_app/app.py",
        "dashboards/authority_app/Dockerfile",
        "dashboards/citizen_app/app.py",
        "dashboards/citizen_app/Dockerfile",
        
        # Monitoring
        "monitoring/prometheus.yml",
        "monitoring/alerts.yml",
        
        # CI/CD
        ".github/workflows/ci-cd.yml",
        
        # Model
        "models/federated_global_model.pth",
        
        # Documentation
        "DEPLOYMENT.md",
        "MLOPS_COMPLETE.md",
        "SYSTEM_READY.md",
    ]
    
    missing = []
    for file in required_files:
        if Path(file).exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - MISSING!")
            missing.append(file)
    
    if missing:
        print(f"\n❌ {len(missing)} files missing!")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files present!")
        return True


def check_imports():
    """Check that all modules can be imported."""
    print("\n" + "=" * 60)
    print("2. Checking Module Imports...")
    print("=" * 60)
    
    modules = [
        ("torch", "PyTorch"),
        ("flwr", "Flower"),
        ("fastapi", "FastAPI"),
        ("streamlit", "Streamlit"),
        ("prometheus_client", "Prometheus Client"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("sklearn", "scikit-learn"),
    ]
    
    failed = []
    for module, name in modules:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NOT INSTALLED!")
            failed.append(name)
    
    if failed:
        print(f"\n❌ {len(failed)} modules not installed!")
        return False
    else:
        print(f"\n✅ All {len(modules)} modules installed!")
        return True


def check_custom_modules():
    """Check that custom modules can be imported."""
    print("\n" + "=" * 60)
    print("3. Checking Custom Modules...")
    print("=" * 60)
    
    modules = [
        "federated_health_risk.data.federated_loader",
        "federated_health_risk.federated.client",
        "federated_health_risk.federated.server",
        "federated_health_risk.models.multimodal_model",
        "federated_health_risk.monitoring.drift_detector",
        "federated_health_risk.services.inference_api",
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module} - ERROR: {e}")
            failed.append(module)
    
    if failed:
        print(f"\n❌ {len(failed)} custom modules failed to import!")
        return False
    else:
        print(f"\n✅ All {len(modules)} custom modules imported successfully!")
        return True


def check_model():
    """Check that the trained model exists and can be loaded."""
    print("\n" + "=" * 60)
    print("4. Checking Trained Model...")
    print("=" * 60)
    
    model_path = Path("models/federated_global_model.pth")
    
    if not model_path.exists():
        print("  ✗ Model file not found!")
        return False
    
    print(f"  ✓ Model file exists ({model_path.stat().st_size / 1024:.1f} KB)")
    
    try:
        import torch
        checkpoint = torch.load(model_path, map_location="cpu")
        
        required_keys = ["model_state_dict", "vitals_dim", "air_dim", "weather_dim"]
        for key in required_keys:
            if key in checkpoint:
                print(f"  ✓ Checkpoint contains '{key}'")
            else:
                print(f"  ✗ Checkpoint missing '{key}'!")
                return False
        
        print(f"\n  Model dimensions:")
        print(f"    Vitals: {checkpoint['vitals_dim']}")
        print(f"    Air: {checkpoint['air_dim']}")
        print(f"    Weather: {checkpoint['weather_dim']}")
        
        print("\n✅ Model is valid and loadable!")
        return True
        
    except Exception as e:
        print(f"  ✗ Error loading model: {e}")
        return False


def check_data():
    """Check that processed data exists."""
    print("\n" + "=" * 60)
    print("5. Checking Processed Data...")
    print("=" * 60)
    
    data_files = [
        "data/processed/fitbit_daily.csv",
        "data/processed/air_daily.csv",
        "data/processed/weather_daily.csv",
    ]
    
    missing = []
    for file in data_files:
        if Path(file).exists():
            size = Path(file).stat().st_size / 1024
            print(f"  ✓ {file} ({size:.1f} KB)")
        else:
            print(f"  ✗ {file} - MISSING!")
            missing.append(file)
    
    if missing:
        print(f"\n❌ {len(missing)} data files missing!")
        return False
    else:
        print(f"\n✅ All {len(data_files)} data files present!")
        return True


def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("SYSTEM VERIFICATION")
    print("=" * 60)
    
    checks = [
        ("Files", check_files),
        ("Imports", check_imports),
        ("Custom Modules", check_custom_modules),
        ("Model", check_model),
        ("Data", check_data),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ Error in {name} check: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL CHECKS PASSED!")
        print("=" * 60)
        print("\nYour system is ready to run!")
        print("\nNext steps:")
        print("  1. Start services: make docker-up")
        print("  2. Test API: curl http://localhost:8000/health")
        print("  3. Open dashboards: http://localhost:8501 & http://localhost:8502")
        return 0
    else:
        print("❌ SOME CHECKS FAILED!")
        print("=" * 60)
        print("\nPlease fix the issues above before running the system.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
