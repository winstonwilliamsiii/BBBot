FROM python:3.11-slim

WORKDIR /app
COPY source.py /app/source.py
COPY spec.json /app/spec.json
COPY catalog.json /app/catalog.json

RUN pip install --no-cache-dir requests beautifulsoup4

ENTRYPOINT ["python", "/app/source.py"]