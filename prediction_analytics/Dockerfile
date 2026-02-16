FROM python:3.11-slim

WORKDIR /app
COPY prediction_analytics/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY prediction_analytics ./prediction_analytics
ENV PYTHONPATH="/app"
CMD ["python", "prediction_analytics/main.py"]
