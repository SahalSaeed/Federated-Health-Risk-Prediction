# Model Card – Multimodal Risk Net

## Overview
- **Use case**: Predict pollution-related health risk score (0-1) for nodes or individuals.
- **Architecture**: Multimodal PyTorch network combining vitals, air-quality summaries, and text embeddings.

## Training Data
- Wearable vitals (simulated / federated node data)
- Air-quality sensors (EPA-style)
- Weather (NOAA-style)
- Optional clinical text summaries (de-identified)

## Evaluation Metrics
- AUROC, AUPRC, calibration error, latency.

## Ethical & Privacy Considerations
- Data never leaves node storage; only model updates shared.
- Support for differential privacy and secure aggregation (todo).

## Limitations
- Simulated data until real partnerships available.
- Model assumes consistent sensor quality across nodes.

## Maintenance
- Monitor drift using PSI/Kolmogorov tests.
- Retrain via automated Prefect flow on trigger breaches or monthly schedule.
