"""Verify that federated learning setup is working correctly."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def check_data():
    """Check if processed data exists."""
    print("1. Checking processed data...")
    data_dir = Path("data/processed")
    
    required_files = ["fitbit_daily.csv", "air_daily.csv", "weather_daily.csv"]
    for file in required_files:
        filepath = data_dir / file
        if filepath.exists():
            print(f"   ✓ {file} exists")
        else:
            print(f"   ✗ {file} missing!")
            return False
    return True


def check_imports():
    """Check if all required modules can be imported."""
    print("\n2. Checking imports...")
    
    try:
        import torch
        print(f"   ✓ PyTorch {torch.__version__}")
    except ImportError:
        print("   ✗ PyTorch not installed!")
        return False
    
    try:
        import flwr
        print(f"   ✓ Flower {flwr.__version__}")
    except ImportError:
        print("   ✗ Flower not installed!")
        return False
    
    try:
        from federated_health_risk.models.multimodal_model import MultimodalRiskNet
        print("   ✓ MultimodalRiskNet")
    except ImportError as e:
        print(f"   ✗ Cannot import MultimodalRiskNet: {e}")
        return False
    
    try:
        from federated_health_risk.data.federated_loader import prepare_federated_data
        print("   ✓ FederatedDataPartitioner")
    except ImportError as e:
        print(f"   ✗ Cannot import FederatedDataPartitioner: {e}")
        return False
    
    return True


def check_data_loading():
    """Check if data can be loaded and partitioned."""
    print("\n3. Testing data loading...")
    
    try:
        from federated_health_risk.data.federated_loader import prepare_federated_data
        
        # Try to load data for 2 nodes
        node_loaders = prepare_federated_data(num_nodes=2, strategy="iid")
        
        if len(node_loaders) == 2:
            print(f"   ✓ Successfully created loaders for 2 nodes")
            
            # Check dimensions
            _, _, (v_dim, a_dim, w_dim) = node_loaders[0]
            print(f"   ✓ Dimensions: vitals={v_dim}, air={a_dim}, weather={w_dim}")
            return True
        else:
            print(f"   ✗ Expected 2 nodes, got {len(node_loaders)}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error loading data: {e}")
        return False


def check_model():
    """Check if model can be instantiated."""
    print("\n4. Testing model instantiation...")
    
    try:
        import torch
        from federated_health_risk.models.multimodal_model import MultimodalRiskNet
        
        model = MultimodalRiskNet(vitals_dim=6, air_dim=5, text_dim=4)
        
        # Test forward pass
        vitals = torch.randn(2, 6)
        air = torch.randn(2, 5)
        weather = torch.randn(2, 4)
        
        output = model(vitals, air, weather)
        
        if output.shape == (2, 1):
            print(f"   ✓ Model forward pass successful")
            print(f"   ✓ Total parameters: {sum(p.numel() for p in model.parameters()):,}")
            return True
        else:
            print(f"   ✗ Unexpected output shape: {output.shape}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error with model: {e}")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("Federated Learning Setup Verification")
    print("=" * 60)
    
    checks = [
        check_data(),
        check_imports(),
        check_data_loading(),
        check_model(),
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All checks passed! You're ready for federated training.")
        print("\nNext step: Run notebooks/05_federated_training_test.ipynb")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
