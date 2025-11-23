FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    streamlit==1.39.0 \
    pandas==2.2.0 \
    plotly==5.24.0 \
    requests==2.32.0

# Copy dashboard code
COPY dashboards/authority_app/app.py .

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
