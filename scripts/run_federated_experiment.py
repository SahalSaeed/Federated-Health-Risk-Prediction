"""Run a federated learning experiment with multiple nodes."""

import logging
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger(__name__)


def run_federated_experiment(num_nodes: int = 3, num_rounds: int = 5):
    """
    Run federated learning experiment by starting server and multiple clients.
    
    Args:
        num_nodes: Number of federated nodes (hospitals/cities)
        num_rounds: Number of federated training rounds
    """
    LOGGER.info("=" * 60)
    LOGGER.info("Starting Federated Learning Experiment")
    LOGGER.info("Nodes: %d | Rounds: %d", num_nodes, num_rounds)
    LOGGER.info("=" * 60)
    
    # Start server in background
    LOGGER.info("Starting Flower server...")
    server_cmd = [
        sys.executable, "-m", "federated_health_risk.federated.server",
        str(num_rounds), str(num_nodes), str(num_nodes)
    ]
    
    server_process = subprocess.Popen(
        server_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Give server time to start
    time.sleep(3)
    LOGGER.info("Server started (PID: %d)", server_process.pid)
    
    # Start clients
    client_processes = []
    for node_id in range(num_nodes):
        LOGGER.info("Starting client for Node %d...", node_id)
        client_cmd = [
            sys.executable, "-m", "federated_health_risk.federated.client",
            "--node-id", str(node_id),
            "--num-nodes", str(num_nodes),
            "--server-address", "127.0.0.1:8080"
        ]
        
        client_process = subprocess.Popen(
            client_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        client_processes.append((node_id, client_process))
        time.sleep(1)  # Stagger client starts
    
    LOGGER.info("All clients started. Waiting for training to complete...")
    
    # Monitor server output
    try:
        for line in server_process.stdout:
            print(f"[SERVER] {line.strip()}")
            if "completed" in line.lower():
                break
    except KeyboardInterrupt:
        LOGGER.warning("Interrupted by user")
    
    # Wait for server to finish
    server_process.wait(timeout=300)
    LOGGER.info("Server finished")
    
    # Terminate clients
    for node_id, client_process in client_processes:
        client_process.terminate()
        client_process.wait(timeout=5)
        LOGGER.info("Client %d terminated", node_id)
    
    LOGGER.info("=" * 60)
    LOGGER.info("Federated Learning Experiment Completed!")
    LOGGER.info("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run federated learning experiment")
    parser.add_argument("--num-nodes", type=int, default=3, help="Number of federated nodes")
    parser.add_argument("--num-rounds", type=int, default=5, help="Number of training rounds")
    args = parser.parse_args()
    
    run_federated_experiment(num_nodes=args.num_nodes, num_rounds=args.num_rounds)
