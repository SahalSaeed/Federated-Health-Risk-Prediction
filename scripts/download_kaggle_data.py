"""Utility script to download Kaggle datasets required for the project.

Usage:
    poetry run python scripts/download_kaggle_data.py

Prerequisites:
    1. Install kagglehub (comes with project dependencies).
    2. Place your kaggle.json API key under %USERPROFILE%/.kaggle/ with 600 perms.
"""

from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path

import kagglehub

OUTPUT_ROOT = Path("downloaded_datasets")
DATASETS = {
    "weather": "sumanthvrao/daily-climate-time-series-data",
    "air_quality": "uciml/pm25-data-for-five-chinese-cities",
    "fitbit": "arashnic/fitbit",
}


def ensure_kaggle_token() -> None:
    token_path = Path.home() / ".kaggle" / "kaggle.json"
    if not token_path.exists():
        raise FileNotFoundError(
            "Kaggle API token not found. Download kaggle.json from "
            "https://www.kaggle.com/settings/account and place it in ~/.kaggle/."
        )
    os.chmod(token_path, 0o600)


def copy_csvs(src_root: Path, dst_root: Path) -> int:
    count = 0
    for file in src_root.rglob("*.csv"):
        target = dst_root / file.name
        shutil.copy(file, target)
        print(f"Copied {target}")
        count += 1
    return count


def download_dataset(alias: str, kaggle_id: str) -> None:
    print(f"\n=== Downloading {alias} ({kaggle_id}) ===")
    download_path = Path(kagglehub.dataset_download(kaggle_id))
    print(f"Dataset downloaded to {download_path}")

    target_folder = OUTPUT_ROOT / alias
    target_folder.mkdir(parents=True, exist_ok=True)

    if download_path.suffix == ".zip":
        with zipfile.ZipFile(download_path, "r") as zip_ref:
            zip_ref.extractall(target_folder)
        source_root = target_folder
        print(f"Extracted zip contents into {target_folder}")
    else:
        source_root = download_path

    csv_total = copy_csvs(source_root, target_folder)
    print(f"Total CSV files saved for {alias}: {csv_total}")


def main() -> None:
    ensure_kaggle_token()
    OUTPUT_ROOT.mkdir(exist_ok=True)
    for alias, kaggle_id in DATASETS.items():
        download_dataset(alias, kaggle_id)


if __name__ == "__main__":
    main()

