"""Node-level feature engineering utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import pandas as pd


@dataclass
class FeatureStoreConfig:
    storage_uri: str
    table_name: str = "features"


def build_features(batch: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    wearables = batch["wearable"]
    air = batch["air_quality"]
    weather = batch["weather"]

    wearable_agg = (
        wearables.groupby("node_id")
        .agg(
            hr_mean=("heart_rate", "mean"),
            spo2_min=("spo2", "min"),
            temp_mean=("body_temp_c", "mean"),
            step_sum=("steps", "sum"),
        )
        .reset_index()
    )

    air_agg = (
        air.groupby("node_id")
        .agg(
            pm25_mean=("pm25", "mean"),
            pm10_mean=("pm10", "mean"),
            humidity_mean=("humidity", "mean"),
        )
        .reset_index()
    )

    weather_agg = (
        weather.groupby("node_id")
        .agg(
            temp_c_mean=("temp_c", "mean"),
            rel_humidity_mean=("rel_humidity", "mean"),
            wind_speed_mean=("wind_speed_mps", "mean"),
        )
        .reset_index()
    )

    features = wearable_agg.merge(air_agg, on="node_id").merge(weather_agg, on="node_id")
    features["risk_score_proxy"] = (
        0.4 * features["pm25_mean"]
        + 0.2 * features["humidity_mean"]
        + 0.2 * features["hr_mean"]
        + 0.2 * features["temp_c_mean"]
    ) / 100

    return features


def persist_features(df: pd.DataFrame, config: FeatureStoreConfig) -> None:
    if config.storage_uri.startswith("sqlite:///"):
        path = Path(config.storage_uri.replace("sqlite:///", ""))
        path.parent.mkdir(parents=True, exist_ok=True)
        from sqlalchemy import create_engine

        engine = create_engine(config.storage_uri)
        df.to_sql(config.table_name, engine, if_exists="append", index=False)
    else:
        raise NotImplementedError(f"Storage {config.storage_uri} not supported yet")

