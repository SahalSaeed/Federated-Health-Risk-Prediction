"""Data validation utilities leveraging Great Expectations-like tests."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd
import yaml


class SchemaValidationError(Exception):
    """Raised when a dataframe fails schema checks."""


def load_schema(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_dataframe(df: pd.DataFrame, schema: Dict) -> None:
    missing_cols = set(field["name"] for field in schema["fields"]) - set(df.columns)
    if missing_cols:
        raise SchemaValidationError(f"Missing columns: {missing_cols}")

    for field in schema["fields"]:
        name = field["name"]
        if field.get("required") and df[name].isna().any():
            raise SchemaValidationError(f"{name} has nulls but is required")
        constraints = field.get("constraints", {})
        if "min" in constraints and (df[name] < constraints["min"]).any():
            raise SchemaValidationError(f"{name} below min {constraints['min']}")
        if "max" in constraints and (df[name] > constraints["max"]).any():
            raise SchemaValidationError(f"{name} above max {constraints['max']}")


def apply_contract(df: pd.DataFrame, schema_path: str) -> pd.DataFrame:
    schema = load_schema(Path(schema_path))
    validate_dataframe(df, schema)
    return df

