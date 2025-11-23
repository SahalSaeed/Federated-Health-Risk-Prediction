"""FastAPI inference service for health risk prediction."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from federated_health_risk.models.multimodal_model import MultimodalRiskNet
from sklearn.preprocessing import StandardScaler
import numpy as np

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Federated Health Risk Prediction API",
    description="Real-time health risk prediction using federated learning model",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model variable
model = None
device = None
model_config = None
scaler_vitals = None
scaler_air = None
scaler_weather = None


class HealthData(BaseModel):
    """Input data schema for health risk prediction."""

    # Vitals data
    total_steps: float = Field(..., description="Total steps taken", ge=0)
    active_minutes: float = Field(..., description="Active minutes", ge=0)
    sedentary_minutes: float = Field(..., description="Sedentary minutes", ge=0)
    calories: float = Field(..., description="Calories burned", ge=0)
    distance_km: float = Field(..., description="Distance in km", ge=0)
    cardio_load: float = Field(..., description="Cardiovascular load", ge=0)

    # Air quality data
    pm_us_post: float = Field(..., description="PM2.5 US Post", ge=0)
    pm_caotangsi: float = Field(..., description="PM2.5 Caotangsi", ge=0)
    pm_shahepu: float = Field(..., description="PM2.5 Shahepu", ge=0)
    pm_mean: float = Field(..., description="Mean PM2.5", ge=0)
    pollution_load: float = Field(..., description="Pollution load index", ge=0)

    # Weather data (matching training data format)
    delhi_meantemp: float = Field(..., description="Mean temperature", alias="temperature")
    delhi_humidity: float = Field(..., description="Humidity percentage", ge=0, le=100, alias="humidity")
    delhi_wind_speed: float = Field(default=5.0, description="Wind speed", alias="wind_speed")
    delhi_meanpressure: float = Field(..., description="Mean atmospheric pressure", alias="pressure")

    class Config:
        schema_extra = {
            "example": {
                "total_steps": 8000.0,
                "active_minutes": 45.0,
                "sedentary_minutes": 600.0,
                "calories": 2200.0,
                "distance_km": 5.5,
                "cardio_load": 50.0,
                "pm_us_post": 35.0,
                "pm_caotangsi": 40.0,
                "pm_shahepu": 38.0,
                "pm_mean": 37.7,
                "pollution_load": 38.0,
                "temperature": 22.0,
                "humidity": 65.0,
                "wind_speed": 5.0,
                "pressure": 1013.0,
            }
        }


class PredictionResponse(BaseModel):
    """Response schema for predictions."""

    risk_score: float = Field(..., description="Risk probability (0-1)")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    confidence: float = Field(..., description="Model confidence")
    recommendations: List[str] = Field(..., description="Health recommendations")


class HealthStatus(BaseModel):
    """API health check response."""

    status: str
    model_loaded: bool
    model_version: str
    device: str


def load_model(model_path: str = "models/federated_global_model.pth") -> None:
    """Load the trained federated model."""
    global model, device, model_config, scaler_vitals, scaler_air, scaler_weather

    LOGGER.info(f"Loading model from {model_path}")

    # Load checkpoint
    checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)

    # Extract configuration
    vitals_dim = checkpoint["vitals_dim"]
    air_dim = checkpoint["air_dim"]
    weather_dim = checkpoint["weather_dim"]

    model_config = {
        "vitals_dim": vitals_dim,
        "air_dim": air_dim,
        "weather_dim": weather_dim,
        "version": "1.0.0",
    }

    # Initialize model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MultimodalRiskNet(vitals_dim=vitals_dim, air_dim=air_dim, text_dim=weather_dim)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    # Initialize scalers with approximate statistics from training data
    # These are rough estimates - ideally should be saved with the model
    scaler_vitals = StandardScaler()
    scaler_vitals.mean_ = np.array([7500, 35, 650, 2100, 5.0, 42.5])
    scaler_vitals.scale_ = np.array([3500, 20, 200, 400, 2.5, 20])
    
    scaler_air = StandardScaler()
    scaler_air.mean_ = np.array([80, 85, 82, 82.3, 82.3])
    scaler_air.scale_ = np.array([50, 50, 50, 50, 50])
    
    scaler_weather = StandardScaler()
    scaler_weather.mean_ = np.array([15, 60, 5, 1013])
    scaler_weather.scale_ = np.array([10, 20, 3, 15])

    LOGGER.info(f"Model loaded successfully on {device}")


@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    try:
        load_model()
    except Exception as e:
        LOGGER.error(f"Failed to load model: {e}")
        raise


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Federated Health Risk Prediction API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthStatus, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthStatus(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        model_version=model_config.get("version", "unknown") if model_config else "unknown",
        device=str(device) if device else "unknown",
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(data: HealthData):
    """
    Predict health risk based on input data.

    Args:
        data: Health data including vitals, air quality, and weather

    Returns:
        Risk prediction with recommendations
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Prepare input arrays
        vitals_raw = np.array([[
            data.total_steps,
            data.active_minutes,
            data.sedentary_minutes,
            data.calories,
            data.distance_km,
            data.cardio_load,
        ]])

        air_raw = np.array([[
            data.pm_us_post,
            data.pm_caotangsi,
            data.pm_shahepu,
            data.pm_mean,
            data.pollution_load,
        ]])

        weather_raw = np.array([[
            data.delhi_meantemp,
            data.delhi_humidity,
            data.delhi_wind_speed,
            data.delhi_meanpressure
        ]])

        # Scale inputs (CRITICAL: model was trained on scaled data)
        vitals_scaled = scaler_vitals.transform(vitals_raw)
        air_scaled = scaler_air.transform(air_raw)
        weather_scaled = scaler_weather.transform(weather_raw)

        # Convert to tensors
        vitals = torch.tensor(vitals_scaled, dtype=torch.float32).to(device)
        air = torch.tensor(air_scaled, dtype=torch.float32).to(device)
        weather = torch.tensor(weather_scaled, dtype=torch.float32).to(device)

        # Make prediction
        with torch.no_grad():
            risk_score = model(vitals, air, weather).squeeze().item()

        # Determine risk level
        if risk_score < 0.3:
            risk_level = "low"
            recommendations = [
                "Maintain current healthy lifestyle",
                "Continue regular physical activity",
                "Monitor air quality when outdoors",
            ]
        elif risk_score < 0.7:
            risk_level = "medium"
            recommendations = [
                "Increase physical activity if possible",
                "Monitor air quality closely",
                "Consider indoor exercise on high pollution days",
                "Stay hydrated and maintain good sleep",
            ]
        else:
            risk_level = "high"
            recommendations = [
                "Consult healthcare provider",
                "Avoid outdoor activities during high pollution",
                "Increase physical activity gradually",
                "Monitor symptoms closely",
                "Consider air purifier for indoor spaces",
            ]

        # Calculate confidence (distance from decision boundary)
        confidence = abs(risk_score - 0.5) * 2

        return PredictionResponse(
            risk_score=float(risk_score),
            risk_level=risk_level,
            confidence=float(confidence),
            recommendations=recommendations,
        )

    except Exception as e:
        LOGGER.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch", tags=["Prediction"])
async def predict_batch(data_list: List[HealthData]):
    """
    Batch prediction endpoint.

    Args:
        data_list: List of health data samples

    Returns:
        List of predictions
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    predictions = []
    for data in data_list:
        try:
            pred = await predict(data)
            predictions.append(pred)
        except Exception as e:
            LOGGER.error(f"Batch prediction error: {e}")
            predictions.append({"error": str(e)})

    return {"predictions": predictions, "count": len(predictions)}


@app.get("/model/info", tags=["Model"])
async def model_info():
    """Get model information."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "model_type": "MultimodalRiskNet",
        "framework": "PyTorch",
        "training_method": "Federated Learning (FedAvg)",
        "input_dimensions": model_config,
        "total_parameters": sum(p.numel() for p in model.parameters()),
        "device": str(device),
    }


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the FastAPI server."""
    uvicorn.run("federated_health_risk.services.inference_api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    start_server(reload=True)
