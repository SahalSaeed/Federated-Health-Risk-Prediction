import pandas as pd

from federated_health_risk.pipelines.feature_builder import build_features


def test_build_features_creates_risk_score():
    batch = {
        "wearable": pd.DataFrame(
            {
                "node_id": ["a", "a"],
                "heart_rate": [80, 82],
                "spo2": [98, 99],
                "body_temp_c": [36.5, 36.7],
                "steps": [1000, 2000],
            }
        ),
        "air_quality": pd.DataFrame(
            {
                "node_id": ["a", "a"],
                "pm25": [30, 35],
                "pm10": [40, 45],
                "humidity": [50, 55],
            }
        ),
        "weather": pd.DataFrame(
            {
                "node_id": ["a", "a"],
                "temp_c": [20, 21],
                "rel_humidity": [45, 46],
                "wind_speed_mps": [3, 4],
            }
        ),
    }

    features = build_features(batch)
    assert "risk_score_proxy" in features.columns
    assert features["risk_score_proxy"].notnull().all()

