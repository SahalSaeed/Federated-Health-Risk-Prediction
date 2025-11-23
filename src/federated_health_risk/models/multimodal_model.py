"""Simple multimodal PyTorch model for fused health risk scoring."""

from __future__ import annotations

import torch
from torch import nn


class MultimodalRiskNet(nn.Module):
    """Combines vitals (time-series), air-quality, and text embeddings."""

    def __init__(
        self,
        vitals_dim: int,
        air_dim: int,
        text_dim: int,
        hidden_dim: int = 128,
    ) -> None:
        super().__init__()
        self.vitals_branch = nn.Sequential(
            nn.Linear(vitals_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
        )
        self.air_branch = nn.Sequential(
            nn.Linear(air_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim // 2),
        )
        self.text_branch = nn.Sequential(
            nn.Linear(text_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
        )
        fusion_dim = hidden_dim * 2 + hidden_dim // 2
        self.head = nn.Sequential(
            nn.Linear(fusion_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

    def forward(self, vitals_x: torch.Tensor, air_x: torch.Tensor, text_x: torch.Tensor) -> torch.Tensor:
        vitals_feat = self.vitals_branch(vitals_x)
        air_feat = self.air_branch(air_x)
        text_feat = self.text_branch(text_x)
        fused = torch.cat([vitals_feat, air_feat, text_feat], dim=-1)
        return self.head(fused)

