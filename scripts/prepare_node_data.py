"""
Prepare per-node data without centralization.
Clips all datasets to 940 rows and saves separate files for each node.
"""

from pathlib import Path
import numpy as np
import pandas as pd

# Configuration
MAX_ROWS = 940  # Clip all datasets to this many rows
NUM_NODES = 3   # Number of federated nodes

# Paths
repo_root = Path(__file__).parent.parent
data_dir = repo_root / "data"
processed_dir = data_dir / "processed"
processed_dir.mkdir(parents=True, exist_ok=True)

# Input paths
fitbit_path = data_dir / "fitbit" / "dailyActivity_merged.csv"
air_path = data_dir / "air_quality" / "ChengduPM20100101_20151231.csv"
weather_path = data_dir / "weather" / "DailyDelhiClimateTrain.csv"

print("=" * 70)
print("PREPARING PER-NODE DATA (NO CENTRALIZATION)")
print("=" * 70)
print(f"\nConfiguration:")
print(f"  Max rows per dataset: {MAX_ROWS}")
print(f"  Number of nodes: {NUM_NODES}")
print(f"  Output directory: {processed_dir}")

# ============================================================================
# 1. LOAD AND CLIP DATA
# ============================================================================
print(f"\n1. Loading and clipping data to {MAX_ROWS} rows...")

fitbit_df = pd.read_csv(fitbit_path).head(MAX_ROWS)
air_df = pd.read_csv(air_path).head(MAX_ROWS)
weather_df = pd.read_csv(weather_path).head(MAX_ROWS)

print(f"   ✓ Fitbit: {len(fitbit_df)} rows")
print(f"   ✓ Air Quality: {len(air_df)} rows")
print(f"   ✓ Weather: {len(weather_df)} rows")

# ============================================================================
# 2. PROCESS FITBIT DATA
# ============================================================================
print(f"\n2. Processing Fitbit data...")

fitbit_df["ActivityDate"] = pd.to_datetime(fitbit_df["ActivityDate"], errors="coerce", format="%m/%d/%Y")
fitbit_df = fitbit_df.dropna(subset=["ActivityDate"])
fitbit_df["date"] = fitbit_df["ActivityDate"]

# Rename columns to match expected format
fitbit_daily = fitbit_df.rename(columns={
    "TotalSteps": "total_steps",
    "VeryActiveMinutes": "active_minutes",
    "SedentaryMinutes": "sedentary_minutes",
    "Calories": "calories",
    "TotalDistance": "distance_km"
})[["date", "total_steps", "active_minutes", "sedentary_minutes", "calories", "distance_km"]]

# Add features
fitbit_daily["cardio_load"] = (
    fitbit_daily["total_steps"] / (fitbit_daily["active_minutes"].replace(0, np.nan) + 1)
)
fitbit_daily = fitbit_daily.replace([np.inf, -np.inf], np.nan)

# Ensure exactly 940 rows
fitbit_daily = fitbit_daily.head(MAX_ROWS)

print(f"   ✓ Processed to {len(fitbit_daily)} records")

# ============================================================================
# 3. PROCESS AIR QUALITY DATA
# ============================================================================
print(f"\n3. Processing Air Quality data...")

# Clean columns
air_df.columns = air_df.columns.str.strip()
air_df = air_df.replace({"NA": np.nan})

# PM columns
pm_cols = [c for c in ["PM_Caotangsi", "PM_Shahepu", "PM_US Post"] if c in air_df.columns]
if pm_cols:
    air_df[pm_cols] = air_df[pm_cols].apply(pd.to_numeric, errors="coerce")

# Build date
lower_map = {c.lower(): c for c in air_df.columns}
year_col = lower_map.get("year")
month_col = lower_map.get("month")
day_col = lower_map.get("day")

if year_col and month_col and day_col:
    air_df[[year_col, month_col, day_col]] = air_df[[year_col, month_col, day_col]].apply(pd.to_numeric, errors="coerce")
    air_df["date"] = pd.to_datetime(
        dict(
            year=air_df[year_col].astype("Int64"),
            month=air_df[month_col].astype("Int64"),
            day=air_df[day_col].astype("Int64")
        ),
        errors="coerce"
    )
else:
    possible_date_cols = [c for c in air_df.columns if "date" in c.lower() or "time" in c.lower()]
    if possible_date_cols:
        air_df["date"] = pd.to_datetime(air_df[possible_date_cols[0]], errors="coerce")

air_df = air_df.dropna(subset=["date"])

# Rename columns
rename_map = {}
if "PM_US Post" in air_df.columns:
    rename_map["PM_US Post"] = "pm_us_post"
if "PM_Caotangsi" in air_df.columns:
    rename_map["PM_Caotangsi"] = "pm_caotangsi"
if "PM_Shahepu" in air_df.columns:
    rename_map["PM_Shahepu"] = "pm_shahepu"
for col in ["DEWP", "HUMI", "PRES", "TEMP"]:
    if col in air_df.columns:
        rename_map[col] = col.lower()

air_daily = air_df.rename(columns=rename_map)

# Select relevant columns
keep_cols = ["date"] + [c for c in ["pm_us_post", "pm_caotangsi", "pm_shahepu", "dewp", "humi", "pres", "temp"] if c in air_daily.columns]
air_daily = air_daily[keep_cols]

# Add features
available_pm = [c for c in ["pm_us_post", "pm_caotangsi", "pm_shahepu"] if c in air_daily.columns]
if available_pm:
    air_daily["pm_mean"] = air_daily[available_pm].mean(axis=1, skipna=True)
else:
    air_daily["pm_mean"] = np.nan

air_daily = air_daily.replace([np.inf, -np.inf], np.nan)

# Ensure exactly 940 rows
air_daily = air_daily.head(MAX_ROWS)

print(f"   ✓ Processed to {len(air_daily)} records")

# ============================================================================
# 4. PROCESS WEATHER DATA
# ============================================================================
print(f"\n4. Processing Weather data...")

# Try common date column names
weather_df['date'] = pd.to_datetime(weather_df.get('date', weather_df.get('Date', None)), errors='coerce')

# If that fails, try year/month/day
if weather_df['date'].isna().all():
    for col in ['year', 'Year']:
        if col in weather_df.columns:
            weather_df['year'] = pd.to_numeric(weather_df[col], errors='coerce')
    for col in ['month', 'Month']:
        if col in weather_df.columns:
            weather_df['month'] = pd.to_numeric(weather_df[col], errors='coerce')
    for col in ['day', 'Day']:
        if col in weather_df.columns:
            weather_df['day'] = pd.to_numeric(weather_df[col], errors='coerce')
    if {'year', 'month', 'day'}.issubset(weather_df.columns):
        weather_df['date'] = pd.to_datetime(
            dict(year=weather_df['year'], month=weather_df['month'], day=weather_df['day']),
            errors='coerce'
        )

weather_df = weather_df.dropna(subset=['date'])

# Normalize column names
lower_map = {c.lower(): c for c in weather_df.columns}
rename_map = {}
if 'meantemp' in lower_map:
    rename_map[lower_map['meantemp']] = 'delhi_meantemp'
if 'humidity' in lower_map:
    rename_map[lower_map['humidity']] = 'delhi_humidity'
if 'wind_speed' in lower_map:
    rename_map[lower_map['wind_speed']] = 'delhi_wind_speed'
if 'meanpressure' in lower_map:
    rename_map[lower_map['meanpressure']] = 'delhi_meanpressure'
if rename_map:
    weather_df = weather_df.rename(columns=rename_map)

# Select relevant columns
keep_cols = ["date"] + [c for c in ["delhi_meantemp", "delhi_humidity", "delhi_wind_speed", "delhi_meanpressure"] if c in weather_df.columns]
weather_daily = weather_df[keep_cols]

# Ensure exactly 940 rows
weather_daily = weather_daily.head(MAX_ROWS)

print(f"   ✓ Processed to {len(weather_daily)} records")

# ============================================================================
# 5. SAVE PER-NODE DATA (NO MERGING!)
# ============================================================================
print(f"\n5. Saving per-node data (NO centralization)...")

# Save Fitbit data
fitbit_output = processed_dir / "fitbit_daily.csv"
fitbit_daily.to_csv(fitbit_output, index=False)
print(f"   ✓ Saved Fitbit: {fitbit_output} ({len(fitbit_daily)} rows)")

# Save Air Quality data
air_output = processed_dir / "air_daily.csv"
air_daily.to_csv(air_output, index=False)
print(f"   ✓ Saved Air Quality: {air_output} ({len(air_daily)} rows)")

# Save Weather data
weather_output = processed_dir / "weather_daily.csv"
weather_daily.to_csv(weather_output, index=False)
print(f"   ✓ Saved Weather: {weather_output} ({len(weather_daily)} rows)")

# ============================================================================
# 6. SUMMARY
# ============================================================================
print(f"\n" + "=" * 70)
print("✅ DATA PREPARATION COMPLETE")
print("=" * 70)
print(f"\nSummary:")
print(f"  • Each dataset clipped to {MAX_ROWS} rows")
print(f"  • NO centralized merging (data stays separate)")
print(f"  • Ready for federated learning across {NUM_NODES} nodes")
print(f"\nOutput files:")
print(f"  • {fitbit_output}")
print(f"  • {air_output}")
print(f"  • {weather_output}")
print(f"\nNext step: Run federated training")
print(f"  Command: .\\run.ps1 train")
print("=" * 70)
