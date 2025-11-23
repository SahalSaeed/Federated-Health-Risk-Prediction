"""Test data drift detection with real data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
from federated_health_risk.monitoring.drift_detector import DataDriftDetector


def test_drift_detection():
    """Test drift detection on processed data."""
    print("=" * 70)
    print("DATA DRIFT DETECTION TEST")
    print("=" * 70)
    
    # Load reference data (training data)
    print("\n1. Loading reference data...")
    reference_data = pd.read_csv("data/processed/air_daily.csv")
    print(f"   Reference samples: {len(reference_data)}")
    
    # Simulate current data (take last 20% as "new" data)
    split_point = int(len(reference_data) * 0.8)
    reference = reference_data.iloc[:split_point]
    current = reference_data.iloc[split_point:]
    
    print(f"   Reference: {len(reference)} samples")
    print(f"   Current: {len(current)} samples")
    
    # Initialize drift detector
    print("\n2. Initializing drift detector...")
    detector = DataDriftDetector(reference, threshold=0.05)
    
    # Generate drift report
    print("\n3. Generating drift report...")
    report = detector.generate_drift_report(current)
    
    # Display results
    print("\n" + "=" * 70)
    print("DRIFT DETECTION RESULTS")
    print("=" * 70)
    
    print(f"\nOverall Drift Detected: {'YES ⚠️' if report['overall_drift_detected'] else 'NO ✓'}")
    
    print("\n--- KS Test Results ---")
    ks_results = report['ks_test']
    print(f"Total features checked: {ks_results['total_features']}")
    print(f"Drifted features: {ks_results['drifted_features']}")
    print(f"Drift percentage: {ks_results['drift_percentage']:.1f}%")
    
    if ks_results['drifted_feature_names']:
        print(f"\nDrifted features (KS Test):")
        for feature in ks_results['drifted_feature_names']:
            details = ks_results['details'][feature]
            print(f"  • {feature}: p-value={details['p_value']:.4f}")
    
    print("\n--- PSI Test Results ---")
    psi_results = report['psi_test']
    print(f"Total features checked: {psi_results['total_features']}")
    print(f"Drifted features: {psi_results['drifted_features']}")
    print(f"Drift percentage: {psi_results['drift_percentage']:.1f}%")
    
    if psi_results['drifted_feature_names']:
        print(f"\nDrifted features (PSI):")
        for feature in psi_results['drifted_feature_names']:
            details = psi_results['details'][feature]
            print(f"  • {feature}: PSI={details['psi']:.4f} ({details['drift_level']})")
    
    # Save report
    print("\n4. Saving drift report...")
    detector.save_report(report, "monitoring/drift_report.json")
    print("   Report saved to: monitoring/drift_report.json")
    
    print("\n" + "=" * 70)
    print("✅ DRIFT DETECTION TEST COMPLETE")
    print("=" * 70)
    
    return report


if __name__ == "__main__":
    test_drift_detection()
