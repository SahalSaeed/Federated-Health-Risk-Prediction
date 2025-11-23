"""Authority Dashboard - Health Risk Monitoring for Public Health Officials."""

import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Authority Dashboard - Health Risk Monitoring",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 0.5rem 0;
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


def get_model_info():
    """Get model information from API."""
    try:
        response = requests.get(f"{API_URL}/model/info", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None


def generate_sample_data():
    """Generate sample population data for demonstration."""
    dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
    
    data = {
        "date": dates,
        "high_risk_count": [50 + i * 2 + (i % 7) * 5 for i in range(30)],
        "medium_risk_count": [120 + i * 3 + (i % 5) * 10 for i in range(30)],
        "low_risk_count": [300 - i * 2 + (i % 3) * 15 for i in range(30)],
        "avg_pollution": [35 + (i % 10) * 3 for i in range(30)],
        "avg_temperature": [20 + (i % 15) * 0.5 for i in range(30)],
    }
    
    return pd.DataFrame(data)


# Header
st.markdown('<div class="main-header">🏥 Public Health Authority Dashboard</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Status
    api_healthy = check_api_health()
    if api_healthy:
        st.success("✅ API Connected")
    else:
        st.error("❌ API Disconnected")
    
    st.markdown("---")
    
    # Filters
    st.subheader("Filters")
    time_range = st.selectbox(
        "Time Range",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days"],
        index=1
    )
    
    region_filter = st.multiselect(
        "Regions",
        ["All", "North", "South", "East", "West"],
        default=["All"]
    )
    
    risk_threshold = st.slider(
        "Risk Alert Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.8,
        step=0.05
    )
    
    st.markdown("---")
    
    # Model Info
    if api_healthy:
        model_info = get_model_info()
        if model_info:
            st.subheader("🤖 Model Info")
            st.text(f"Type: {model_info.get('model_type', 'N/A')}")
            st.text(f"Method: Federated Learning")
            st.text(f"Parameters: {model_info.get('total_parameters', 'N/A'):,}")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🗺️ Risk Map", "📈 Trends", "⚠️ Alerts"])

# Generate sample data
df = generate_sample_data()

with tab1:
    st.header("Population Health Overview")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_monitored = df.iloc[-1][["high_risk_count", "medium_risk_count", "low_risk_count"]].sum()
        st.metric(
            "Total Monitored",
            f"{int(total_monitored):,}",
            delta=f"+{int(total_monitored - df.iloc[-2][['high_risk_count', 'medium_risk_count', 'low_risk_count']].sum())}",
        )
    
    with col2:
        high_risk = int(df.iloc[-1]["high_risk_count"])
        st.metric(
            "High Risk",
            f"{high_risk:,}",
            delta=f"+{int(high_risk - df.iloc[-2]['high_risk_count'])}",
            delta_color="inverse",
        )
    
    with col3:
        medium_risk = int(df.iloc[-1]["medium_risk_count"])
        st.metric(
            "Medium Risk",
            f"{medium_risk:,}",
            delta=f"+{int(medium_risk - df.iloc[-2]['medium_risk_count'])}",
        )
    
    with col4:
        avg_pollution = df.iloc[-1]["avg_pollution"]
        st.metric(
            "Avg Pollution (PM2.5)",
            f"{avg_pollution:.1f} µg/m³",
            delta=f"{avg_pollution - df.iloc[-2]['avg_pollution']:.1f}",
            delta_color="inverse",
        )
    
    st.markdown("---")
    
    # Risk Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Distribution (Current)")
        latest = df.iloc[-1]
        fig = go.Figure(data=[go.Pie(
            labels=["High Risk", "Medium Risk", "Low Risk"],
            values=[latest["high_risk_count"], latest["medium_risk_count"], latest["low_risk_count"]],
            marker=dict(colors=["#f44336", "#ff9800", "#4caf50"]),
            hole=0.4
        )])
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Risk Trend (30 Days)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["date"], y=df["high_risk_count"], name="High Risk", line=dict(color="#f44336")))
        fig.add_trace(go.Scatter(x=df["date"], y=df["medium_risk_count"], name="Medium Risk", line=dict(color="#ff9800")))
        fig.add_trace(go.Scatter(x=df["date"], y=df["low_risk_count"], name="Low Risk", line=dict(color="#4caf50")))
        fig.update_layout(height=300, xaxis_title="Date", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Geographic Risk Distribution")
    st.info("🗺️ Interactive map showing risk levels by region (Demo - requires real geographic data)")
    
    # Placeholder for map
    st.markdown("""
    **Features to implement:**
    - Heat map of risk levels by region
    - Cluster markers for high-risk areas
    - Filterable by time period
    - Click for detailed regional statistics
    """)

with tab3:
    st.header("Trend Analysis")
    
    # Pollution vs Risk
    st.subheader("Pollution Levels vs High Risk Cases")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], 
        y=df["avg_pollution"], 
        name="Avg Pollution",
        yaxis="y1",
        line=dict(color="#2196f3")
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], 
        y=df["high_risk_count"], 
        name="High Risk Count",
        yaxis="y2",
        line=dict(color="#f44336")
    ))
    fig.update_layout(
        xaxis_title="Date",
        yaxis=dict(title="Pollution (µg/m³)", side="left"),
        yaxis2=dict(title="High Risk Count", side="right", overlaying="y"),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Correlation analysis
    correlation = df["avg_pollution"].corr(df["high_risk_count"])
    st.metric("Pollution-Risk Correlation", f"{correlation:.3f}")

with tab4:
    st.header("Active Alerts & Recommendations")
    
    # Current alerts
    st.subheader("🚨 Current Alerts")
    
    if df.iloc[-1]["high_risk_count"] > 60:
        st.markdown(
            '<div class="alert-high"><strong>HIGH ALERT:</strong> High-risk cases above threshold. Immediate action recommended.</div>',
            unsafe_allow_html=True
        )
    
    if df.iloc[-1]["avg_pollution"] > 40:
        st.markdown(
            '<div class="alert-medium"><strong>MEDIUM ALERT:</strong> Elevated pollution levels detected. Monitor closely.</div>',
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # Recommendations
    st.subheader("📋 Recommended Actions")
    st.markdown("""
    1. **Increase monitoring** in high-risk regions
    2. **Issue public health advisory** for outdoor activities
    3. **Activate emergency response** protocols if needed
    4. **Coordinate with environmental agencies** on pollution control
    5. **Prepare healthcare facilities** for potential increase in cases
    """)
    
    # Export data
    st.markdown("---")
    st.subheader("📥 Export Data")
    if st.button("Generate Report"):
        st.success("Report generated! (Demo - implement actual report generation)")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Federated Health Risk Monitoring System v1.0 | Last updated: {}</div>".format(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ),
    unsafe_allow_html=True
)
