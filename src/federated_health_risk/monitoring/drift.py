"""Basic population stability index (PSI) drift detector."""

from __future__ import annotations

import numpy as np
import pandas as pd


def psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    quantiles = np.linspace(0, 1, bins + 1)
    breakpoints = expected.quantile(quantiles).values
    expected_counts, _ = np.histogram(expected, bins=breakpoints)
    actual_counts, _ = np.histogram(actual, bins=breakpoints)

    expected_perc = np.where(expected_counts == 0, 1e-4, expected_counts / expected_counts.sum())
    actual_perc = np.where(actual_counts == 0, 1e-4, actual_counts / actual_counts.sum())

    return float(((actual_perc - expected_perc) * np.log(actual_perc / expected_perc)).sum())


def check_feature_drift(
    baseline: pd.DataFrame,
    current: pd.DataFrame,
    features: list[str],
    threshold: float = 0.2,
) -> dict[str, float]:
    psi_scores = {}
    for feat in features:
        psi_scores[feat] = psi(baseline[feat].dropna(), current[feat].dropna())
    alerts = {feat: score for feat, score in psi_scores.items() if score > threshold}
    return {"scores": psi_scores, "alerts": alerts}

