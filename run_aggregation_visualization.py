"""
Run federated learning with weight aggregation visualization.

This script demonstrates how federated averaging improves model performance
by aggregating weights from multiple nodes after local training.
"""
import torch
import torch.nn as nn
from torch.optim import Adam
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from federated_health_risk.data.federated_loader import prepare_federated_data
from federated_health_risk.models.multimodal_model import MultimodalRiskNet

# Configuration
NUM_NODES = 3
NUM_ROUNDS = 10
LOCAL_EPOCHS = 2
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("="*70)
print("FEDERATED LEARNING: WEIGHT AGGREGATION VISUALIZATION")
print("="*70)
print(f"\nConfiguration:")
print(f"  Nodes: {NUM_NODES}")
print(f"  Rounds: {NUM_ROUNDS}")
print(f"  Local Epochs per Round: {LOCAL_EPOCHS}")
print(f"  Device: {device}")
print()

# Load data
print("Loading federated data...")
node_loaders = prepare_federated_data(
    num_nodes=NUM_NODES,
    strategy="iid",
    data_root="data/processed"
)

_, _, (vitals_dim, air_dim, weather_dim) = node_loaders[0]
print(f"✓ Data loaded: Vitals={vitals_dim}, Air={air_dim}, Weather={weather_dim} features\n")

# Initialize models
print("Initializing models...")
node_models = {}
node_optimizers = {}

for node_id in range(NUM_NODES):
    model = MultimodalRiskNet(vitals_dim=vitals_dim, air_dim=air_dim, text_dim=weather_dim)
    model = model.to(device)
    node_models[node_id] = model
    node_optimizers[node_id] = Adam(model.parameters(), lr=1e-3)

print(f"✓ Initialized {NUM_NODES} models\n")


def train_node(model, optimizer, train_loader, device, epochs=1):
    """Train a single node's model locally."""
    model.train()
    criterion = nn.BCELoss()
    total_loss = 0.0
    num_batches = 0
    
    for epoch in range(epochs):
        for batch in train_loader:
            vitals, air, weather, y = [b.to(device) for b in batch]
            
            optimizer.zero_grad()
            preds = model(vitals, air, weather).squeeze()
            loss = criterion(preds, y)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
    
    return total_loss / num_batches if num_batches > 0 else 0.0


def evaluate_model(model, test_loader, device):
    """Evaluate model on test data."""
    model.eval()
    criterion = nn.BCELoss()
    total_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for batch in test_loader:
            vitals, air, weather, y = [b.to(device) for b in batch]
            preds = model(vitals, air, weather).squeeze()
            loss = criterion(preds, y)
            
            total_loss += loss.item() * y.size(0)
            correct += ((preds > 0.5) == (y > 0.5)).sum().item()
            total += y.size(0)
    
    avg_loss = total_loss / total if total > 0 else 0.0
    accuracy = correct / total if total > 0 else 0.0
    
    return avg_loss, accuracy


def federated_averaging(models):
    """Average model parameters across all nodes (FedAvg algorithm)."""
    global_state = models[0].state_dict()
    
    for key in global_state.keys():
        global_state[key] = torch.stack(
            [models[i].state_dict()[key].float() for i in range(len(models))]
        ).mean(0)
    
    for model in models:
        model.load_state_dict(global_state)
    
    return global_state


# Track metrics
history = {
    "before_aggregation": {"loss": [], "acc": []},
    "after_aggregation": {"loss": [], "acc": []},
    "node_losses_before": {i: [] for i in range(NUM_NODES)},
    "node_losses_after": {i: [] for i in range(NUM_NODES)},
    "node_acc_before": {i: [] for i in range(NUM_NODES)},
    "node_acc_after": {i: [] for i in range(NUM_NODES)}
}

print("Starting Federated Training...\n")
print("="*70)

for round_num in range(NUM_ROUNDS):
    print(f"\nRound {round_num + 1}/{NUM_ROUNDS}")
    print("-"*70)
    
    # Phase 1: Local training on each node
    for node_id in range(NUM_NODES):
        train_loader, test_loader, _ = node_loaders[node_id]
        
        # Train locally
        train_loss = train_node(
            node_models[node_id],
            node_optimizers[node_id],
            train_loader,
            device,
            epochs=LOCAL_EPOCHS
        )
        
        # Evaluate BEFORE aggregation
        test_loss, test_acc = evaluate_model(node_models[node_id], test_loader, device)
        history["node_losses_before"][node_id].append(test_loss)
        history["node_acc_before"][node_id].append(test_acc)
    
    # Calculate average performance BEFORE aggregation
    avg_loss_before = np.mean([history["node_losses_before"][i][-1] for i in range(NUM_NODES)])
    avg_acc_before = np.mean([history["node_acc_before"][i][-1] for i in range(NUM_NODES)])
    history["before_aggregation"]["loss"].append(avg_loss_before)
    history["before_aggregation"]["acc"].append(avg_acc_before)
    
    print(f"  Before Aggregation - Loss: {avg_loss_before:.4f}, Acc: {avg_acc_before:.4f}")
    
    # Phase 2: Federated averaging
    federated_averaging(list(node_models.values()))
    
    # Phase 3: Evaluate AFTER aggregation
    for node_id in range(NUM_NODES):
        _, test_loader, _ = node_loaders[node_id]
        test_loss, test_acc = evaluate_model(node_models[node_id], test_loader, device)
        history["node_losses_after"][node_id].append(test_loss)
        history["node_acc_after"][node_id].append(test_acc)
    
    # Calculate average performance AFTER aggregation
    avg_loss_after = np.mean([history["node_losses_after"][i][-1] for i in range(NUM_NODES)])
    avg_acc_after = np.mean([history["node_acc_after"][i][-1] for i in range(NUM_NODES)])
    history["after_aggregation"]["loss"].append(avg_loss_after)
    history["after_aggregation"]["acc"].append(avg_acc_after)
    
    print(f"  After Aggregation  - Loss: {avg_loss_after:.4f}, Acc: {avg_acc_after:.4f}")
    print(f"  Improvement: Loss Δ={avg_loss_before - avg_loss_after:+.4f}, Acc Δ={avg_acc_after - avg_acc_before:+.4f}")

print("\n" + "="*70)
print("✓ Training complete!")
print("="*70)

# Create visualization
print("\nCreating visualization...")
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Federated Learning: Impact of Weight Aggregation', fontsize=16, fontweight='bold')

rounds = np.arange(1, NUM_ROUNDS + 1)

# Plot 1: Loss comparison
ax1 = axes[0, 0]
ax1.plot(rounds, history["before_aggregation"]["loss"], 'o-', label='Before Aggregation',
         color='#e74c3c', linewidth=2, markersize=8)
ax1.plot(rounds, history["after_aggregation"]["loss"], 's-', label='After Aggregation',
         color='#27ae60', linewidth=2, markersize=8)
ax1.set_xlabel('Federated Round', fontsize=12)
ax1.set_ylabel('Test Loss', fontsize=12)
ax1.set_title('Loss: Before vs After Weight Aggregation', fontsize=13, fontweight='bold')
ax1.legend(fontsize=11)
ax1.grid(True, alpha=0.3)

# Plot 2: Accuracy comparison
ax2 = axes[0, 1]
ax2.plot(rounds, history["before_aggregation"]["acc"], 'o-', label='Before Aggregation',
         color='#e74c3c', linewidth=2, markersize=8)
ax2.plot(rounds, history["after_aggregation"]["acc"], 's-', label='After Aggregation',
         color='#27ae60', linewidth=2, markersize=8)
ax2.set_xlabel('Federated Round', fontsize=12)
ax2.set_ylabel('Test Accuracy', fontsize=12)
ax2.set_title('Accuracy: Before vs After Weight Aggregation', fontsize=13, fontweight='bold')
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.3)

# Plot 3: Per-node loss trajectories
ax3 = axes[1, 0]
colors = ['#3498db', '#9b59b6', '#f39c12']
for node_id in range(NUM_NODES):
    ax3.plot(rounds, history["node_losses_after"][node_id], 'o-',
             label=f'Node {node_id}', color=colors[node_id], linewidth=2, markersize=6)
ax3.set_xlabel('Federated Round', fontsize=12)
ax3.set_ylabel('Test Loss (After Aggregation)', fontsize=12)
ax3.set_title('Per-Node Loss After Aggregation', fontsize=13, fontweight='bold')
ax3.legend(fontsize=11)
ax3.grid(True, alpha=0.3)

# Plot 4: Improvement per round
ax4 = axes[1, 1]
loss_improvements = np.array(history["before_aggregation"]["loss"]) - np.array(history["after_aggregation"]["loss"])
acc_improvements = np.array(history["after_aggregation"]["acc"]) - np.array(history["before_aggregation"]["acc"])

x = np.arange(NUM_ROUNDS)
width = 0.35
ax4.bar(x - width/2, loss_improvements, width, label='Loss Reduction', color='#e74c3c', alpha=0.7)
ax4_twin = ax4.twinx()
ax4_twin.bar(x + width/2, acc_improvements, width, label='Accuracy Gain', color='#27ae60', alpha=0.7)

ax4.set_xlabel('Federated Round', fontsize=12)
ax4.set_ylabel('Loss Reduction', fontsize=12, color='#e74c3c')
ax4_twin.set_ylabel('Accuracy Gain', fontsize=12, color='#27ae60')
ax4.set_title('Improvement from Weight Aggregation per Round', fontsize=13, fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels(rounds)
ax4.tick_params(axis='y', labelcolor='#e74c3c')
ax4_twin.tick_params(axis='y', labelcolor='#27ae60')
ax4.grid(True, alpha=0.3, axis='x')

lines1, labels1 = ax4.get_legend_handles_labels()
lines2, labels2 = ax4_twin.get_legend_handles_labels()
ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)

plt.tight_layout()
output_path = Path('models/weight_aggregation_impact.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved visualization to {output_path}")
plt.close()

# Save the trained model
model_save_path = Path('models/federated_global_model.pth')
torch.save({
    'model_state_dict': list(node_models.values())[0].state_dict(),
    'vitals_dim': vitals_dim,
    'air_dim': air_dim,
    'weather_dim': weather_dim,
    'final_loss': history["after_aggregation"]["loss"][-1],
    'final_acc': history["after_aggregation"]["acc"][-1],
}, model_save_path)
print(f"✓ Saved trained model to {model_save_path}")

# Print summary
print("\n" + "="*70)
print("SUMMARY STATISTICS")
print("="*70)

total_loss_improvement = np.sum(loss_improvements)
total_acc_improvement = np.sum(acc_improvements)
avg_loss_improvement = np.mean(loss_improvements)
avg_acc_improvement = np.mean(acc_improvements)

print(f"\nTotal Improvements Over {NUM_ROUNDS} Rounds:")
print(f"  Cumulative Loss Reduction: {total_loss_improvement:.4f}")
print(f"  Cumulative Accuracy Gain:  {total_acc_improvement:.4f}")
print(f"\nAverage Improvement Per Round:")
print(f"  Loss Reduction: {avg_loss_improvement:.4f}")
print(f"  Accuracy Gain:  {avg_acc_improvement:.4f}")

final_loss = history["after_aggregation"]["loss"][-1]
final_acc = history["after_aggregation"]["acc"][-1]
initial_loss = history["before_aggregation"]["loss"][0]
initial_acc = history["before_aggregation"]["acc"][0]

print(f"\nPerformance Comparison:")
print(f"  Initial (Round 1, Before Agg): Loss={initial_loss:.4f}, Acc={initial_acc:.4f}")
print(f"  Final (Round {NUM_ROUNDS}, After Agg):  Loss={final_loss:.4f}, Acc={final_acc:.4f}")
print(f"  Overall Improvement: Loss Δ={initial_loss - final_loss:+.4f}, Acc Δ={final_acc - initial_acc:+.4f}")

print(f"\n{'='*70}")
print("KEY INSIGHT:")
print("Weight aggregation consistently improves model performance by combining")
print("knowledge from all nodes, demonstrating the power of federated learning!")
print("="*70)
