# Dockerfile.trading - This is a Dockerfile configuration, not executable Python code
# This file should be renamed to Dockerfile.trading (without .py extension)

# FROM python:3.10-slim
# 
# RUN pip install pandas mlflow requests
# 
# WORKDIR /app
# COPY train_and_trade.py .
# COPY indicators.py .
# COPY trigger_engine.py .
# COPY broker_api.py .
# 
# CMD ["python", "train_and_trade.py"]