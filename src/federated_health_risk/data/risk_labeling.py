"""
Risk labeling strategies for health risk prediction.

Provides different methods to create balanced or imbalanced risk labels.
"""

import pandas as pd
import numpy as np


def create_risk_labels_balanced(
    df: pd.DataFrame,
    target_high_risk_ratio: float = 0.5
) -> pd.DataFrame:
    """
    Create balanced risk labels with specified high-risk ratio.
    
    Args:
        df: DataFrame with health features
        target_high_risk_ratio: Desired proportion of high-risk samples (0.5 = 50/50)
    
    Returns:
        DataFrame with 'risk_proxy' column added
    """
    # Calculate composite risk score
    df["cardio_load"] = (
        df["active_minutes"] * 0.5 + df["total_steps"] / 1000
    )
    df["pollution_load"] = df.filter(like="pm_").mean(axis=1)
    
    # Normalize to 0-1 range
    cardio_norm = (df["cardio_load"] - df["cardio_load"].min()) / (df["cardio_load"].max() - df["cardio_load"].min())
    pollution_norm = (df["pollution_load"] - df["pollution_load"].min()) / (df["pollution_load"].max() - df["pollution_load"].min())
    
    # Composite risk score: high pollution + low activity = high risk
    # Invert cardio (low activity = high risk)
    risk_score = (pollution_norm + (1 - cardio_norm)) / 2
    
    # Use quantile to get desired ratio
    threshold = df["risk_score"].quantile(1 - target_high_risk_ratio)
    df["risk_proxy"] = (risk_score > threshold).astype(float)
    
    return df


def create_risk_labels_threshold(
    df: pd.DataFrame,
    pollution_percentile: float = 0.60,
    cardio_percentile: float = 0.40,
    logic: str = "OR"
) -> pd.DataFrame:
    """
    Create risk labels using threshold-based logic.
    
    Args:
        df: DataFrame with health features
        pollution_percentile: Threshold for high pollution (e.g., 0.60 = top 40%)
        cardio_percentile: Threshold for low activity (e.g., 0.40 = bottom 40%)
        logic: "OR" (either condition) or "AND" (both conditions)
    
    Returns:
        DataFrame with 'risk_proxy' column added
    """
    # Calculate loads
    df["cardio_load"] = (
        df["active_minutes"] * 0.5 + df["total_steps"] / 1000
    )
    df["pollution_load"] = df.filter(like="pm_").mean(axis=1)
    
    # Calculate thresholds
    pollution_threshold = df["pollution_load"].quantile(pollution_percentile)
    cardio_threshold = df["cardio_load"].quantile(cardio_percentile)
    
    # Apply logic
    high_pollution = df["pollution_load"] > pollution_threshold
    low_activity = df["cardio_load"] < cardio_threshold
    
    if logic.upper() == "OR":
        df["risk_proxy"] = (high_pollution | low_activity).astype(float)
    elif logic.upper() == "AND":
        df["risk_proxy"] = (high_pollution & low_activity).astype(float)
    else:
        raise ValueError(f"Unknown logic: {logic}. Use 'OR' or 'AND'")
    
    return df


def create_risk_labels_multifactor(
    df: pd.DataFrame,
    weights: dict = None
) -> pd.DataFrame:
    """
    Create risk labels using weighted multi-factor approach.
    
    Args:
        df: DataFrame with health features
        weights: Dictionary of feature weights, e.g.:
                 {'pollution': 0.4, 'activity': 0.3, 'sedentary': 0.3}
    
    Returns:
        DataFrame with 'risk_proxy' column added
    """
    if weights is None:
        weights = {
            'pollution': 0.4,
            'activity': 0.3,
            'sedentary': 0.2,
            'calories': 0.1
        }
    
    # Calculate individual risk factors
    df["cardio_load"] = (
        df["active_minutes"] * 0.5 + df["total_steps"] / 1000
    )
    df["pollution_load"] = df.filter(like="pm_").mean(axis=1)
    
    # Normalize all factors to 0-1
    pollution_norm = (df["pollution_load"] - df["pollution_load"].min()) / \
                     (df["pollution_load"].max() - df["pollution_load"].min())
    
    # Invert activity (low activity = high risk)
    activity_norm = 1 - ((df["cardio_load"] - df["cardio_load"].min()) / \
                         (df["cardio_load"].max() - df["cardio_load"].min()))
    
    # Normalize sedentary (high sedentary = high risk)
    sedentary_norm = (df["sedentary_minutes"] - df["sedentary_minutes"].min()) / \
                     (df["sedentary_minutes"].max() - df["sedentary_minutes"].min())
    
    # Invert calories (low calories = high risk)
    calories_norm = 1 - ((df["calories"] - df["calories"].min()) / \
                         (df["calories"].max() - df["calories"].min()))
    
    # Weighted risk score
    risk_score = (
        pollution_norm * weights.get('pollution', 0.4) +
        activity_norm * weights.get('activity', 0.3) +
        sedentary_norm * weights.get('sedentary', 0.2) +
        calories_norm * weights.get('calories', 0.1)
    )
    
    # Use median as threshold for 50/50 split
    threshold = risk_score.median()
    df["risk_proxy"] = (risk_score > threshold).astype(float)
    
    return df


def print_label_distribution(df: pd.DataFrame, node_id: int = None):
    """Print distribution of risk labels."""
    total = len(df)
    high_risk = df["risk_proxy"].sum()
    low_risk = total - high_risk
    
    node_str = f"Node {node_id}: " if node_id is not None else ""
    print(f"{node_str}Risk Distribution:")
    print(f"  Low Risk (0):  {low_risk:4d} ({low_risk/total*100:5.1f}%)")
    print(f"  High Risk (1): {high_risk:4d} ({high_risk/total*100:5.1f}%)")
    print(f"  Total:         {total:4d}")
