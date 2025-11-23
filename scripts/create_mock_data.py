"""Create mock data for CI/CD testing.

This script generates synthetic data that mimics the structure of real data
but is small enough for CI/CD pipelines.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# Output directory
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Creating mock data for CI/CD testing...")
print("="*70)

# Generate 100 days of mock data (small for CI)
NUM_DAYS = 100
start_date = datetime(2016, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(NUM_DAYS)]

# 1. Fitbit data
print("\n1. Creating fitbit_daily.csv...")
fitbit_data = {
    'date': dates,
    'total_steps': np.random.randint(2000, 15000, NUM_DAYS),
    'active_minutes': np.random.randint(10, 90, NUM_DAYS),
    'sedentary_minutes': np.random.randint(300, 900, NUM_DAYS),
    'calories': np.random.randint(1500, 3000, NUM_DAYS),
    'distance_km': np.random.uniform(1.0, 10.0, NUM_DAYS).round(2),
    'cardio_load': np.random.uniform(10, 100, NUM_DAYS).round(2),
}
fitbit_df = pd.DataFrame(fitbit_data)
fitbit_df.to_csv(OUTPUT_DIR / "fitbit_daily.csv", index=False)
print(f"   [OK] Created {len(fitbit_df)} rows")

# 2. Air quality data
print("\n2. Creating air_daily.csv...")
air_data = {
    'date': dates,
    'pm_us_post': np.random.uniform(20, 200, NUM_DAYS).round(1),
    'pm_caotangsi': np.random.uniform(20, 200, NUM_DAYS).round(1),
    'pm_shahepu': np.random.uniform(20, 200, NUM_DAYS).round(1),
    'dewp': np.random.uniform(-10, 25, NUM_DAYS).round(1),
    'humi': np.random.uniform(30, 90, NUM_DAYS).round(1),
    'pres': np.random.uniform(990, 1030, NUM_DAYS).round(1),
    'temp': np.random.uniform(-5, 35, NUM_DAYS).round(1),
}
# Calculate mean PM2.5
air_data['pm_mean'] = (
    (air_data['pm_us_post'] + air_data['pm_caotangsi'] + air_data['pm_shahepu']) / 3
).round(1)

air_df = pd.DataFrame(air_data)
air_df.to_csv(OUTPUT_DIR / "air_daily.csv", index=False)
print(f"   [OK] Created {len(air_df)} rows")

# 3. Weather data
print("\n3. Creating weather_daily.csv...")
weather_data = {
    'date': dates,
    'delhi_meantemp': np.random.uniform(5, 35, NUM_DAYS).round(1),
    'delhi_humidity': np.random.uniform(30, 90, NUM_DAYS).round(1),
    'delhi_wind_speed': np.random.uniform(0, 15, NUM_DAYS).round(1),
    'delhi_meanpressure': np.random.uniform(990, 1030, NUM_DAYS).round(1),
}
weather_df = pd.DataFrame(weather_data)
weather_df.to_csv(OUTPUT_DIR / "weather_daily.csv", index=False)
print(f"   [OK] Created {len(weather_df)} rows")

print("\n" + "="*70)
print("[SUCCESS] Mock data created successfully!")
print(f"Location: {OUTPUT_DIR.absolute()}")
print(f"Total samples: {NUM_DAYS}")
print("\nFiles created:")
print(f"  - fitbit_daily.csv ({len(fitbit_df)} rows)")
print(f"  - air_daily.csv ({len(air_df)} rows)")
print(f"  - weather_daily.csv ({len(weather_df)} rows)")
print("="*70)
