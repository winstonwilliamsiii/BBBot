#Dockerfile_Indicators

# Dockerfile.indicators

FROM python:3.10-slim

# Install dependencies
RUN pip install pandas

# Copy your indicator logic
WORKDIR /app
COPY indicators.py .  # This should contain calculate_rsi and calculate_macd
COPY compute_indicators.py .  # This will be the entrypoint script

# Entrypoint
CMD ["python", "compute_indicators.py"]