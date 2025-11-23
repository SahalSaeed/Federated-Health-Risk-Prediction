"""Helper utilities for loading yaml/dotenv configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


@lru_cache(maxsize=None)
def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def init_env(env_file: str = ".env") -> None:
    load_dotenv(env_file, override=False)

