"""Flower server configuration for federated training."""

from __future__ import annotations

import logging
from typing import Dict

import flwr as fl

LOGGER = logging.getLogger(__name__)


def start_server(config: Dict | None = None) -> None:
    """Start Flower federated learning server."""
    config = config or {}
    
    strategy = fl.server.strategy.FedAvg(
        fraction_fit=config.get("fraction_fit", 1.0),  # Use all available clients
        min_fit_clients=config.get("min_fit_clients", 2),
        min_available_clients=config.get("min_available_clients", 2),
    )

    server_address = config.get("address", "[::]:8080")
    num_rounds = config.get("num_rounds", 5)
    
    LOGGER.info("Starting Flower server at %s for %d rounds", server_address, num_rounds)
    LOGGER.info("Strategy: FedAvg with min_fit_clients=%d", config.get("min_fit_clients", 2))
    
    fl.server.start_server(
        server_address=server_address,
        strategy=strategy,
        config=fl.server.ServerConfig(num_rounds=num_rounds),
    )
    
    LOGGER.info("Federated training completed!")



if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    
    # Parse simple config from command line
    config = {
        "address": "[::]:8080",
        "num_rounds": int(sys.argv[1]) if len(sys.argv) > 1 else 5,
        "min_fit_clients": int(sys.argv[2]) if len(sys.argv) > 2 else 2,
        "min_available_clients": int(sys.argv[3]) if len(sys.argv) > 3 else 2,
    }
    
    start_server(config)
