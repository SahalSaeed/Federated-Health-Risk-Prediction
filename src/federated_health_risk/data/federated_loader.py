"""Data loader for federated learning - partitions data across nodes."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

LOGGER = logging.getLogger(__name__)


class FederatedDataPartitioner:
    """Partitions multimodal health data across federated nodes."""

    def __init__(self, data_root: str = "data/processed"):
        self.data_root = Path(data_root)
        self.scaler = StandardScaler()

    def load_and_merge(self) -> pd.DataFrame:
        """Load all data sources and create synthetic merged dataset."""
        LOGGER.info("Loading processed data from %s", self.data_root)
        
        # Load individual sources
        fitbit = pd.read_csv(self.data_root / "fitbit_daily.csv", parse_dates=["date"])
        air = pd.read_csv(self.data_root / "air_daily.csv", parse_dates=["date"])
        weather = pd.read_csv(self.data_root / "weather_daily.csv", parse_dates=["date"])
        
        LOGGER.info("Loaded: Fitbit=%d, Air=%d, Weather=%d rows", len(fitbit), len(air), len(weather))
        
        # Since dates don't overlap, create synthetic dataset by repeating patterns
        # Use Fitbit dates as base (smallest dataset)
        base_dates = fitbit[["date"]].copy()
        
        # For air and weather, sample randomly to match Fitbit length
        air_sample = air.drop(columns=["date"]).sample(n=len(fitbit), replace=True, random_state=42).reset_index(drop=True)
        weather_sample = weather.drop(columns=["date"]).sample(n=len(fitbit), replace=True, random_state=42).reset_index(drop=True)
        
        # Combine all features
        merged = pd.concat([
            base_dates,
            fitbit.drop(columns=["date"]).reset_index(drop=True),
            air_sample,
            weather_sample
        ], axis=1)
        
        LOGGER.info("Synthetic merged dataset: %d rows, %d columns", len(merged), len(merged.columns))
        
        # Create target variable (risk_proxy) using composite risk score
        # Calculate individual risk factors
        merged["cardio_load"] = (
            merged["active_minutes"] * 0.5 + merged["total_steps"] / 1000
        )
        merged["pollution_load"] = merged.filter(like="pm_").mean(axis=1)
        
        # Handle NaN values in pollution_load
        merged["pollution_load"] = merged["pollution_load"].fillna(merged["pollution_load"].median())
        
        # Normalize factors to 0-1 range (with safety checks)
        pollution_min = merged["pollution_load"].min()
        pollution_max = merged["pollution_load"].max()
        pollution_range = pollution_max - pollution_min
        if pollution_range > 0:
            pollution_norm = (merged["pollution_load"] - pollution_min) / pollution_range
        else:
            pollution_norm = 0.5  # Default if no variation
        
        # Normalize cardio load
        cardio_min = merged["cardio_load"].min()
        cardio_max = merged["cardio_load"].max()
        cardio_range = cardio_max - cardio_min
        if cardio_range > 0:
            cardio_norm = (merged["cardio_load"] - cardio_min) / cardio_range
            activity_risk = 1 - cardio_norm  # Invert: low activity = high risk
        else:
            activity_risk = 0.5  # Default if no variation
        
        # Composite risk score (weighted average)
        # 50% pollution, 50% activity
        risk_score = (pollution_norm * 0.5 + activity_risk * 0.5)
        
        # Use median as threshold for balanced 50/50 split
        risk_threshold = risk_score.median()
        merged["risk_proxy"] = (risk_score > risk_threshold).astype(float)
        
        LOGGER.info("Risk distribution: %.2f%% high-risk samples", merged["risk_proxy"].mean() * 100)
        
        return merged

    def partition_by_nodes(
        self, 
        df: pd.DataFrame, 
        num_nodes: int = 3,
        strategy: str = "iid"
    ) -> Dict[int, pd.DataFrame]:
        """
        Partition data across nodes.
        
        Args:
            df: Merged dataframe
            num_nodes: Number of federated nodes (hospitals/cities)
            strategy: 'iid' (random split) or 'non_iid' (by date ranges to simulate geographic/temporal differences)
        """
        if strategy == "iid":
            # Random shuffle and split
            df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
            splits = np.array_split(df_shuffled, num_nodes)
            partitions = {i: splits[i] for i in range(num_nodes)}
            
        elif strategy == "non_iid":
            # Split by date ranges (simulates different cities with temporal patterns)
            df_sorted = df.sort_values("date").reset_index(drop=True)
            splits = np.array_split(df_sorted, num_nodes)
            partitions = {i: splits[i] for i in range(num_nodes)}
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        for node_id, node_df in partitions.items():
            LOGGER.info(
                "Node %d: %d samples, risk=%.2f%%", 
                node_id, len(node_df), node_df["risk_proxy"].mean() * 100
            )
        
        return partitions

    def create_dataloaders(
        self,
        node_data: pd.DataFrame,
        batch_size: int = 32,
        test_size: float = 0.2
    ) -> Tuple[DataLoader, DataLoader]:
        """Convert node dataframe to PyTorch dataloaders."""
        
        # Define feature groups
        vitals_cols = ["total_steps", "active_minutes", "sedentary_minutes", "calories", "distance_km", "cardio_load"]
        air_cols = [c for c in node_data.columns if "pm_" in c or c == "pollution_load"]
        # Updated weather column names to match actual data
        weather_cols = ["delhi_meantemp", "delhi_humidity", "delhi_wind_speed", "delhi_meanpressure"]
        
        # Handle missing columns gracefully
        vitals_cols = [c for c in vitals_cols if c in node_data.columns]
        air_cols = [c for c in air_cols if c in node_data.columns]
        weather_cols = [c for c in weather_cols if c in node_data.columns]
        
        X_vitals = node_data[vitals_cols].fillna(0).values
        X_air = node_data[air_cols].fillna(0).values
        X_weather = node_data[weather_cols].fillna(0).values
        y = node_data["risk_proxy"].values
        
        # Normalize features
        X_vitals = self.scaler.fit_transform(X_vitals)
        X_air = self.scaler.fit_transform(X_air)
        X_weather = self.scaler.fit_transform(X_weather)
        
        # Train/test split
        indices = np.arange(len(node_data))
        train_idx, test_idx = train_test_split(indices, test_size=test_size, random_state=42, stratify=y)
        
        # Create tensors
        train_dataset = TensorDataset(
            torch.FloatTensor(X_vitals[train_idx]),
            torch.FloatTensor(X_air[train_idx]),
            torch.FloatTensor(X_weather[train_idx]),
            torch.FloatTensor(y[train_idx])
        )
        
        test_dataset = TensorDataset(
            torch.FloatTensor(X_vitals[test_idx]),
            torch.FloatTensor(X_air[test_idx]),
            torch.FloatTensor(X_weather[test_idx]),
            torch.FloatTensor(y[test_idx])
        )
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
        
        return train_loader, test_loader, (len(vitals_cols), len(air_cols), len(weather_cols))


def prepare_federated_data(
    num_nodes: int = 3,
    strategy: str = "iid",
    data_root: str = "data/processed"
) -> Dict[int, Tuple[DataLoader, DataLoader, Tuple[int, int, int]]]:
    """
    Main function to prepare federated data for all nodes.
    
    Returns:
        Dictionary mapping node_id -> (train_loader, test_loader, (vitals_dim, air_dim, weather_dim))
    """
    partitioner = FederatedDataPartitioner(data_root)
    
    # Load and merge data
    merged_df = partitioner.load_and_merge()
    
    # Partition across nodes
    node_partitions = partitioner.partition_by_nodes(merged_df, num_nodes, strategy)
    
    # Create dataloaders for each node
    node_loaders = {}
    for node_id, node_df in node_partitions.items():
        train_loader, test_loader, dims = partitioner.create_dataloaders(node_df)
        node_loaders[node_id] = (train_loader, test_loader, dims)
        LOGGER.info("Node %d ready: %d train batches, %d test batches", 
                   node_id, len(train_loader), len(test_loader))
    
    return node_loaders
