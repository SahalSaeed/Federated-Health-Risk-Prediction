"""Simple test of federated learning with simulation (no multiprocessing)."""

import logging

import flwr as fl
import torch

from federated_health_risk.data.federated_loader import prepare_federated_data
from federated_health_risk.federated.client import SimpleFlowerClient
from federated_health_risk.models.multimodal_model import MultimodalRiskNet

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger(__name__)


def run_simulation(num_nodes: int = 3, num_rounds: int = 3):
    """Run federated learning simulation using Flower's simulation mode."""
    
    LOGGER.info("=" * 60)
    LOGGER.info("Federated Learning Simulation")
    LOGGER.info("Nodes: %d | Rounds: %d", num_nodes, num_rounds)
    LOGGER.info("=" * 60)
    
    # Prepare data for all nodes
    LOGGER.info("Preparing federated data...")
    node_loaders = prepare_federated_data(num_nodes=num_nodes, strategy="iid")
    
    # Get dimensions from first node
    _, _, (vitals_dim, air_dim, weather_dim) = node_loaders[0]
    LOGGER.info("Model dimensions: vitals=%d, air=%d, weather=%d", vitals_dim, air_dim, weather_dim)
    
    # Create client function for simulation
    def client_fn(cid: str) -> fl.client.Client:
        """Create a Flower client for simulation."""
        node_id = int(cid)
        train_loader, eval_loader, _ = node_loaders[node_id]
        
        model = MultimodalRiskNet(vitals_dim=vitals_dim, air_dim=air_dim, text_dim=weather_dim)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        return SimpleFlowerClient(model, train_loader, eval_loader, device)
    
    # Configure strategy
    strategy = fl.server.strategy.FedAvg(
        fraction_fit=1.0,  # Use all clients
        min_fit_clients=num_nodes,
        min_available_clients=num_nodes,
        min_evaluate_clients=num_nodes,
    )
    
    # Run simulation
    LOGGER.info("Starting simulation...")
    history = fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=num_nodes,
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy,
        client_resources={"num_cpus": 1, "num_gpus": 0.0},
    )
    
    LOGGER.info("=" * 60)
    LOGGER.info("Simulation Complete!")
    LOGGER.info("=" * 60)
    
    # Print results
    if history.metrics_distributed:
        LOGGER.info("\nFinal Results:")
        for metric_name, values in history.metrics_distributed.items():
            if values:
                final_round, final_value = values[-1]
                LOGGER.info(f"  {metric_name}: {final_value:.4f} (round {final_round})")
    
    return history


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-nodes", type=int, default=3)
    parser.add_argument("--num-rounds", type=int, default=3)
    args = parser.parse_args()
    
    run_simulation(num_nodes=args.num_nodes, num_rounds=args.num_rounds)
