"""Flower client abstraction wrapping the multimodal PyTorch model."""

from __future__ import annotations

import logging
import os
from argparse import ArgumentParser
from typing import Tuple

import flwr as fl
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

LOGGER = logging.getLogger(__name__)


class SimpleFlowerClient(fl.client.NumPyClient):
    def __init__(self, model: nn.Module, train_loader: DataLoader, eval_loader: DataLoader, device: torch.device):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.eval_loader = eval_loader
        self.device = device
        self.criterion = nn.BCELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)

    def get_parameters(self, *_):
        return [val.cpu().detach().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters) -> None:
        state_dict = self.model.state_dict()
        for (name, tensor), param in zip(state_dict.items(), parameters):
            state_dict[name] = torch.tensor(param)
        self.model.load_state_dict(state_dict)

    def fit(self, parameters, config):  # noqa: D401
        self.set_parameters(parameters)
        self.model.train()
        for _ in range(int(config.get("local_epochs", 1))):
            for batch in self.train_loader:
                vitals, air, text, y = [b.to(self.device) for b in batch]
                preds = self.model(vitals, air, text).squeeze()
                loss = self.criterion(preds, y)
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
        return self.get_parameters(), len(self.train_loader.dataset), {}

    def evaluate(self, parameters, config):  # noqa: D401
        self.set_parameters(parameters)
        self.model.eval()
        loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for batch in self.eval_loader:
                vitals, air, text, y = [b.to(self.device) for b in batch]
                preds = self.model(vitals, air, text).squeeze()
                loss += self.criterion(preds, y).item() * y.size(0)
                correct += ((preds > 0.5) == (y > 0.5)).sum().item()
                total += y.size(0)
        metrics = {"accuracy": correct / total if total else 0.0}
        LOGGER.info("Eval metrics: %s", metrics)
        return loss / total if total else 0.0, total, metrics


def start_client(server_address: str = "127.0.0.1:8080", node_id: int = 0, num_nodes: int = 3) -> None:
    """Start a Flower client with real data for a specific node."""
    from federated_health_risk.data.federated_loader import prepare_federated_data
    from federated_health_risk.models.multimodal_model import MultimodalRiskNet

    LOGGER.info("Starting client for node %d", node_id)
    
    # Load federated data partitions
    node_loaders = prepare_federated_data(num_nodes=num_nodes, strategy="iid")
    
    if node_id not in node_loaders:
        raise ValueError(f"Node {node_id} not found. Available nodes: {list(node_loaders.keys())}")
    
    train_loader, eval_loader, (vitals_dim, air_dim, weather_dim) = node_loaders[node_id]
    
    LOGGER.info("Node %d data loaded: vitals_dim=%d, air_dim=%d, weather_dim=%d", 
               node_id, vitals_dim, air_dim, weather_dim)
    
    # Initialize model with correct dimensions
    model = MultimodalRiskNet(vitals_dim=vitals_dim, air_dim=air_dim, text_dim=weather_dim)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    client = SimpleFlowerClient(model, train_loader, eval_loader, device)
    fl.client.start_numpy_client(server_address=server_address, client=client)


def _parse_args():
    parser = ArgumentParser(description="Start a Flower federated client")
    parser.add_argument("--server-address", default=os.getenv("SERVER_ADDRESS", "127.0.0.1:8080"))
    parser.add_argument("--node-id", type=int, required=True, help="Node ID (0, 1, 2, ...)")
    parser.add_argument("--num-nodes", type=int, default=3, help="Total number of nodes")
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = _parse_args()
    start_client(server_address=args.server_address, node_id=args.node_id, num_nodes=args.num_nodes)

