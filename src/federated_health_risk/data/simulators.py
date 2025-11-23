"""Data simulators for wearable, air-quality, and weather streams.

These simulators stand in for real devices / APIs and can be scheduled per node.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, Iterator, List

import numpy as np
import pandas as pd

RNG = np.random.default_rng()


@dataclass
class NodeConfig:
    """Lightweight representation of a participating node."""

    node_id: str
    wearable_topic: str
    air_quality_topic: str
    weather_grid: str


def build_nodes(config: Dict) -> List[NodeConfig]:
    """Parse yaml dictionary into typed configs."""

    nodes = []
    for entry in config.get("nodes", []):
        nodes.append(
            NodeConfig(
                node_id=entry["id"],
                wearable_topic=entry["data_sources"]["wearable_topic"],
                air_quality_topic=entry["data_sources"]["air_quality_topic"],
                weather_grid=entry["data_sources"]["weather_grid"],
            )
        )
    return nodes


def simulate_wearable_batch(node_id: str, n: int = 256) -> pd.DataFrame:
    """Simulate wearable vitals for a node."""

    timestamp = datetime.now(tz=timezone.utc)
    df = pd.DataFrame(
        {
            "reading_id": [f"{node_id}-wear-{i}-{timestamp.timestamp()}" for i in range(n)],
            "node_id": node_id,
            "device_id": [f"{node_id}-dev-{i%32}" for i in range(n)],
            "heart_rate": RNG.normal(loc=75, scale=12, size=n).clip(40, 190),
            "spo2": RNG.normal(loc=97, scale=1.5, size=n).clip(80, 100),
            "body_temp_c": RNG.normal(loc=36.6, scale=0.4, size=n).clip(34, 40),
            "steps": RNG.poisson(lam=20, size=n),
            "recorded_at": pd.date_range(timestamp, periods=n, freq="5s"),
        }
    )
    return df


def simulate_air_quality_batch(node_id: str, n: int = 120) -> pd.DataFrame:
    """Simulate air-quality readings per node/city."""

    timestamp = datetime.now(tz=timezone.utc)
    df = pd.DataFrame(
        {
            "sample_id": [f"{node_id}-air-{i}-{timestamp.timestamp()}" for i in range(n)],
            "station_id": [f"{node_id}-station-{i%8}" for i in range(n)],
            "pm25": RNG.normal(loc=35, scale=10, size=n).clip(2, 300),
            "pm10": RNG.normal(loc=60, scale=15, size=n).clip(5, 400),
            "no2": RNG.normal(loc=30, scale=8, size=n).clip(1, 200),
            "so2": RNG.normal(loc=5, scale=2, size=n).clip(0, 80),
            "co": RNG.normal(loc=0.4, scale=0.1, size=n).clip(0, 5),
            "o3": RNG.normal(loc=25, scale=7, size=n).clip(0, 200),
            "temperature_c": RNG.normal(loc=22, scale=6, size=n).clip(-20, 50),
            "humidity": RNG.normal(loc=55, scale=15, size=n).clip(5, 100),
            "captured_at": pd.date_range(timestamp, periods=n, freq="1min"),
            "node_id": node_id,
        }
    )
    return df


def simulate_weather_batch(node_id: str, n: int = 24) -> pd.DataFrame:
    """Simulate weather forecasts / readings."""

    timestamp = datetime.now(tz=timezone.utc)
    df = pd.DataFrame(
        {
            "record_id": [f"{node_id}-wx-{i}-{timestamp.timestamp()}" for i in range(n)],
            "grid_id": node_id,
            "temp_c": RNG.normal(loc=20, scale=10, size=n).clip(-30, 45),
            "dewpoint_c": RNG.normal(loc=10, scale=5, size=n),
            "rel_humidity": RNG.normal(loc=60, scale=20, size=n).clip(2, 100),
            "wind_speed_mps": RNG.normal(loc=5, scale=2, size=n).clip(0, 40),
            "wind_dir_deg": RNG.uniform(low=0, high=360, size=n),
            "precipitation_mm": RNG.exponential(scale=1.0, size=n).clip(0, 200),
            "weather_desc": RNG.choice(["clear", "cloudy", "rain", "storm", "smog"], size=n),
            "observed_at": pd.date_range(timestamp, periods=n, freq="1h"),
            "node_id": node_id,
        }
    )
    return df


def stream_batches(generator: callable, *args, **kwargs) -> Iterator[pd.DataFrame]:
    """Yield infinite batches from a simulator."""

    while True:
        yield generator(*args, **kwargs)


def mix_modalities(node: NodeConfig) -> Dict[str, pd.DataFrame]:
    """Generate a synced snapshot of all modalities for a node."""

    return {
        "wearable": simulate_wearable_batch(node.node_id),
        "air_quality": simulate_air_quality_batch(node.node_id),
        "weather": simulate_weather_batch(node.node_id),
    }

