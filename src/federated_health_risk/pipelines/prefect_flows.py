"""Prefect flows orchestrating ingestion → feature → federated training."""

from __future__ import annotations

from pathlib import Path

from prefect import flow, task

from federated_health_risk.data.simulators import build_nodes, mix_modalities
from federated_health_risk.pipelines.feature_builder import FeatureStoreConfig, build_features, persist_features
from federated_health_risk.utils.config import load_yaml


@task
def load_node_configs(path: str):
    return build_nodes(load_yaml(Path(path)))


@task
def simulate_node_batch(node_config):
    return mix_modalities(node_config)


@task
def feature_engineering(batch, feature_store_uri: str):
    features = build_features(batch)
    persist_features(features, FeatureStoreConfig(storage_uri=feature_store_uri))
    return features


@flow(name="federated-health-risk-ingest")
def ingestion_flow(node_config_path: str = "conf/nodes/demo_nodes.yaml", feature_store_uri: str = "sqlite:///data/features.db"):
    nodes = load_node_configs(node_config_path)
    for node in nodes:
        batch = simulate_node_batch(node)
        feature_engineering(batch, feature_store_uri)


if __name__ == "__main__":
    ingestion_flow()

