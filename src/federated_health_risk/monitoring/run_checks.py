"""CLI entrypoint for running drift checks on stored features."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from federated_health_risk.monitoring.drift import check_feature_drift


def fetch_latest_features(uri: str, limit: int = 1000) -> pd.DataFrame:
    engine = create_engine(uri)
    query = f"SELECT * FROM features ORDER BY rowid DESC LIMIT {limit}"
    return pd.read_sql(query, engine)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-store-uri", default="sqlite:///data/features.db")
    parser.add_argument("--baseline-path", default="data/baseline_features.parquet")
    parser.add_argument("--threshold", type=float, default=0.2)
    args = parser.parse_args()

    current = fetch_latest_features(args.feature_store_uri)
    baseline_path = Path(args.baseline_path)
    if baseline_path.exists():
        baseline = pd.read_parquet(baseline_path)
    else:
        baseline = current.copy()
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline.to_parquet(baseline_path)

    result = check_feature_drift(
        baseline=baseline,
        current=current,
        features=[col for col in current.columns if col not in {"node_id"}],
        threshold=args.threshold,
    )
    print("PSI scores:", result["scores"])
    if result["alerts"]:
        print("Drift alerts:", result["alerts"])
    else:
        print("No drift alerts.")


if __name__ == "__main__":
    main()

