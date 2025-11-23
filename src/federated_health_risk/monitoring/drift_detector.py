"""Data drift detection for health risk prediction model."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

LOGGER = logging.getLogger(__name__)


class DataDriftDetector:
    """Detect data drift using statistical tests."""

    def __init__(self, reference_data: pd.DataFrame, threshold: float = 0.05):
        """
        Initialize drift detector with reference data.

        Args:
            reference_data: Training/reference dataset
            threshold: P-value threshold for drift detection (default: 0.05)
        """
        self.reference_data = reference_data
        self.threshold = threshold
        self.reference_stats = self._compute_statistics(reference_data)

    def _compute_statistics(self, data: pd.DataFrame) -> Dict:
        """Compute statistical properties of data."""
        stats_dict = {}
        for col in data.select_dtypes(include=[np.number]).columns:
            stats_dict[col] = {
                "mean": data[col].mean(),
                "std": data[col].std(),
                "min": data[col].min(),
                "max": data[col].max(),
                "median": data[col].median(),
                "q25": data[col].quantile(0.25),
                "q75": data[col].quantile(0.75),
            }
        return stats_dict

    def detect_drift_ks_test(
        self, current_data: pd.DataFrame, columns: Optional[List[str]] = None
    ) -> Dict:
        """
        Detect drift using Kolmogorov-Smirnov test.

        Args:
            current_data: Current/production data
            columns: Columns to check (default: all numeric columns)

        Returns:
            Dictionary with drift detection results
        """
        if columns is None:
            columns = self.reference_data.select_dtypes(include=[np.number]).columns

        drift_results = {}
        drifted_features = []

        for col in columns:
            if col not in current_data.columns:
                LOGGER.warning(f"Column {col} not found in current data")
                continue

            # Perform KS test
            statistic, p_value = stats.ks_2samp(
                self.reference_data[col].dropna(), current_data[col].dropna()
            )

            is_drifted = p_value < self.threshold

            drift_results[col] = {
                "statistic": float(statistic),
                "p_value": float(p_value),
                "is_drifted": is_drifted,
                "threshold": self.threshold,
            }

            if is_drifted:
                drifted_features.append(col)
                LOGGER.warning(
                    f"Drift detected in {col}: p-value={p_value:.4f} < {self.threshold}"
                )

        summary = {
            "total_features": len(columns),
            "drifted_features": len(drifted_features),
            "drift_percentage": len(drifted_features) / len(columns) * 100,
            "drifted_feature_names": drifted_features,
            "details": drift_results,
        }

        return summary

    def detect_drift_psi(
        self, current_data: pd.DataFrame, columns: Optional[List[str]] = None, bins: int = 10
    ) -> Dict:
        """
        Detect drift using Population Stability Index (PSI).

        PSI < 0.1: No significant change
        0.1 <= PSI < 0.2: Moderate change
        PSI >= 0.2: Significant change

        Args:
            current_data: Current/production data
            columns: Columns to check
            bins: Number of bins for discretization

        Returns:
            Dictionary with PSI results
        """
        if columns is None:
            columns = self.reference_data.select_dtypes(include=[np.number]).columns

        psi_results = {}
        drifted_features = []

        for col in columns:
            if col not in current_data.columns:
                continue

            ref_data = self.reference_data[col].dropna()
            curr_data = current_data[col].dropna()

            # Create bins based on reference data
            _, bin_edges = np.histogram(ref_data, bins=bins)

            # Calculate distributions
            ref_counts, _ = np.histogram(ref_data, bins=bin_edges)
            curr_counts, _ = np.histogram(curr_data, bins=bin_edges)

            # Normalize to get percentages
            ref_percents = ref_counts / len(ref_data)
            curr_percents = curr_counts / len(curr_data)

            # Avoid division by zero
            ref_percents = np.where(ref_percents == 0, 0.0001, ref_percents)
            curr_percents = np.where(curr_percents == 0, 0.0001, curr_percents)

            # Calculate PSI
            psi = np.sum((curr_percents - ref_percents) * np.log(curr_percents / ref_percents))

            # Determine drift level
            if psi >= 0.2:
                drift_level = "significant"
                is_drifted = True
            elif psi >= 0.1:
                drift_level = "moderate"
                is_drifted = True
            else:
                drift_level = "none"
                is_drifted = False

            psi_results[col] = {
                "psi": float(psi),
                "drift_level": drift_level,
                "is_drifted": is_drifted,
            }

            if is_drifted:
                drifted_features.append(col)
                LOGGER.warning(f"Drift detected in {col}: PSI={psi:.4f} ({drift_level})")

        summary = {
            "total_features": len(columns),
            "drifted_features": len(drifted_features),
            "drift_percentage": len(drifted_features) / len(columns) * 100,
            "drifted_feature_names": drifted_features,
            "details": psi_results,
        }

        return summary

    def generate_drift_report(self, current_data: pd.DataFrame) -> Dict:
        """
        Generate comprehensive drift report.

        Args:
            current_data: Current/production data

        Returns:
            Complete drift analysis report
        """
        LOGGER.info("Generating drift report...")

        # Run both tests
        ks_results = self.detect_drift_ks_test(current_data)
        psi_results = self.detect_drift_psi(current_data)

        # Compare statistics
        current_stats = self._compute_statistics(current_data)

        report = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "reference_samples": len(self.reference_data),
            "current_samples": len(current_data),
            "ks_test": ks_results,
            "psi_test": psi_results,
            "statistics_comparison": {
                "reference": self.reference_stats,
                "current": current_stats,
            },
        }

        # Overall drift status
        overall_drifted = (
            ks_results["drifted_features"] > 0 or psi_results["drifted_features"] > 0
        )
        report["overall_drift_detected"] = overall_drifted

        if overall_drifted:
            LOGGER.warning("⚠️  Data drift detected! Consider retraining the model.")
        else:
            LOGGER.info("✓ No significant data drift detected.")

        return report

    def save_report(self, report: Dict, output_path: str | Path) -> None:
        """Save drift report to JSON file."""
        import json

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert numpy types to Python types for JSON serialization
        def convert_to_json_serializable(obj):
            if isinstance(obj, dict):
                return {k: convert_to_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_json_serializable(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        serializable_report = convert_to_json_serializable(report)

        with open(output_path, "w") as f:
            json.dump(serializable_report, f, indent=2)

        LOGGER.info(f"Drift report saved to {output_path}")


def monitor_drift_from_files(
    reference_path: str, current_path: str, output_path: str = "monitoring/drift_report.json"
) -> Dict:
    """
    Monitor drift between reference and current data files.

    Args:
        reference_path: Path to reference data CSV
        current_path: Path to current data CSV
        output_path: Path to save drift report

    Returns:
        Drift report dictionary
    """
    # Load data
    reference_data = pd.read_csv(reference_path)
    current_data = pd.read_csv(current_path)

    # Initialize detector
    detector = DataDriftDetector(reference_data, threshold=0.05)

    # Generate report
    report = detector.generate_drift_report(current_data)

    # Save report
    detector.save_report(report, output_path)

    return report
