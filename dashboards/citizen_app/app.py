"""Citizen Dashboard - Personal Health Risk Assessment."""

import os
from datetime import datetime

import plotly.graph_objects as go
import requests
import streamlit as st

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Personal Health Risk Assessment",
    page_icon="❤️",
    layout="wide",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #e91e63;
        text-align: center;
        padding: 1rem 0;
    }
    .risk-card {
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
        margin: 1rem 0;
    }
    .risk-low {
        background: linear-gradient(135deg, #4caf50 0%, #8bc34a 100%);
        color: white;
    }
    .risk-medium {
        background: linear-gradient(135deg, #ff9800 0%, #ffc107 100%);
        color: white;
    }
    .risk-high {
        background: linear-gradient(135deg, #f44336 0%, #e91e63 100%);
        color: white;
    }
    .recommendation {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #2196f3;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def check_api_health():
    """Check if API is healthy."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def predict_risk(data):
    """Get risk prediction from API."""
    try:
        response = requests.post(f"{API_URL}/predict", json=data, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Prediction error: {e}")
    return None


# Header
st.markdown('<div class="main-header">❤️ Personal Health Risk Assessment</div>', unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center; color: #666;'>Get personalized health risk insights based on your activity, environment, and weather conditions</p>",
    unsafe_allow_html=True
)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This tool uses AI to assess your health risk based on:
    - **Physical Activity**: Steps, exercise, calories
    - **Air Quality**: Pollution levels in your area
    - **Weather**: Temperature, humidity, pressure
    
    The model was trained using Federated Learning to protect privacy.
    """)
    
    st.markdown("---")
    
    # API Status
    api_healthy = check_api_health()
    if api_healthy:
        st.success("✅ System Online")
    else:
        st.error("❌ System Offline")

# Main content
tab1, tab2, tab3 = st.tabs(["📝 Assessment", "📊 History", "💡 Tips"])

with tab1:
    st.header("Enter Your Health Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏃 Physical Activity")
        total_steps = st.number_input("Total Steps Today", min_value=0, value=8000, step=100)
        active_minutes = st.number_input("Active Minutes", min_value=0, value=45, step=5)
        sedentary_minutes = st.number_input("Sedentary Minutes", min_value=0, value=600, step=30)
        calories = st.number_input("Calories Burned", min_value=0, value=2200, step=50)
        distance_km = st.number_input("Distance (km)", min_value=0.0, value=5.5, step=0.1)
        
        # Calculate cardio load
        cardio_load = (active_minutes * 0.5 + total_steps / 1000) / 2
        st.metric("Cardio Load", f"{cardio_load:.1f}")
    
    with col2:
        st.subheader("🌫️ Environment & Weather")
        
        st.markdown("**Air Quality (PM2.5 µg/m³)**")
        pm_us_post = st.number_input("PM2.5 US Post", min_value=0.0, value=35.0, step=1.0)
        pm_caotangsi = st.number_input("PM2.5 Caotangsi", min_value=0.0, value=40.0, step=1.0)
        pm_shahepu = st.number_input("PM2.5 Shahepu", min_value=0.0, value=38.0, step=1.0)
        pm_mean = (pm_us_post + pm_caotangsi + pm_shahepu) / 3
        pollution_load = pm_mean
        
        st.metric("Average PM2.5", f"{pm_mean:.1f} µg/m³")
        
        st.markdown("**Weather Conditions**")
        temperature = st.number_input("Temperature (°C)", min_value=-20.0, max_value=50.0, value=22.0, step=0.5)
        humidity = st.slider("Humidity (%)", min_value=0, max_value=100, value=65)
        wind_speed = st.number_input("Wind Speed (m/s)", min_value=0.0, max_value=30.0, value=5.0, step=0.5)
        pressure = st.number_input("Pressure (hPa)", min_value=900.0, max_value=1100.0, value=1013.0, step=1.0)
    
    st.markdown("---")
    
    # Predict button
    if st.button("🔍 Assess My Risk", type="primary", use_container_width=True):
        if not api_healthy:
            st.error("❌ System is offline. Please try again later.")
        else:
            with st.spinner("Analyzing your health data..."):
                # Prepare data
                data = {
                    "total_steps": float(total_steps),
                    "active_minutes": float(active_minutes),
                    "sedentary_minutes": float(sedentary_minutes),
                    "calories": float(calories),
                    "distance_km": float(distance_km),
                    "cardio_load": float(cardio_load),
                    "pm_us_post": float(pm_us_post),
                    "pm_caotangsi": float(pm_caotangsi),
                    "pm_shahepu": float(pm_shahepu),
                    "pm_mean": float(pm_mean),
                    "pollution_load": float(pollution_load),
                    "temperature": float(temperature),
                    "humidity": float(humidity),
                    "wind_speed": float(wind_speed),
                    "pressure": float(pressure),
                }
                
                # Get prediction
                result = predict_risk(data)
                
                if result:
                    st.success("✅ Assessment Complete!")
                    
                    # Display risk score
                    risk_score = result["risk_score"]
                    risk_level = result["risk_level"]
                    confidence = result["confidence"]
                    
                    # Risk card
                    if risk_level == "low":
                        card_class = "risk-low"
                        emoji = "✅"
                    elif risk_level == "medium":
                        card_class = "risk-medium"
                        emoji = "⚠️"
                    else:
                        card_class = "risk-high"
                        emoji = "🚨"
                    
                    st.markdown(
                        f"""
                        <div class="risk-card {card_class}">
                            <h1>{emoji} {risk_level.upper()} RISK</h1>
                            <h2>Risk Score: {risk_score:.2%}</h2>
                            <p>Confidence: {confidence:.2%}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Gauge chart
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=risk_score * 100,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Risk Score"},
                        gauge={
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 30], 'color': "#4caf50"},
                                {'range': [30, 70], 'color': "#ff9800"},
                                {'range': [70, 100], 'color': "#f44336"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 70
                            }
                        }
                    ))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Recommendations
                    st.markdown("---")
                    st.subheader("📋 Personalized Recommendations")
                    for i, rec in enumerate(result["recommendations"], 1):
                        st.markdown(
                            f'<div class="recommendation"><strong>{i}.</strong> {rec}</div>',
                            unsafe_allow_html=True
                        )

with tab2:
    st.header("Your Health History")
    st.info("📊 Track your risk scores over time (Feature coming soon)")
    st.markdown("""
    **Planned features:**
    - Daily risk score tracking
    - Activity trends
    - Environmental exposure history
    - Personalized insights
    """)

with tab3:
    st.header("Health & Wellness Tips")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏃 Physical Activity")
        st.markdown("""
        - **Aim for 10,000 steps** daily
        - **30 minutes** of moderate activity
        - **Break up sedentary time** every hour
        - **Mix cardio and strength** training
        """)
        
        st.subheader("🌫️ Air Quality")
        st.markdown("""
        - **Check AQI** before outdoor activities
        - **Use air purifiers** indoors
        - **Wear masks** on high pollution days
        - **Exercise indoors** when AQI > 100
        """)
    
    with col2:
        st.subheader("🌡️ Weather Awareness")
        st.markdown("""
        - **Stay hydrated** in hot weather
        - **Dress appropriately** for conditions
        - **Avoid extreme temperatures**
        - **Monitor humidity** levels
        """)
        
        st.subheader("❤️ General Health")
        st.markdown("""
        - **Regular check-ups** with doctor
        - **Balanced diet** and nutrition
        - **Quality sleep** (7-9 hours)
        - **Stress management** techniques
        """)

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #666;'>Personal Health Risk Assessment v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>",
    unsafe_allow_html=True
)
st.markdown(
    "<div style='text-align: center; color: #999; font-size: 0.8rem;'>⚠️ This tool is for informational purposes only. Consult healthcare professionals for medical advice.</div>",
    unsafe_allow_html=True
)
