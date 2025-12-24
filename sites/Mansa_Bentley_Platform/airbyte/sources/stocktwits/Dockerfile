FROM python:3.11-slim

# Set working directory
WORKDIR /airbyte/integration_code

# Install dependencies
RUN pip install --no-cache-dir \
    requests==2.31.0 \
    beautifulsoup4==4.12.2 \
    lxml==4.9.3

# Copy source code
COPY source.py /airbyte/integration_code/source.py
COPY spec.json /airbyte/integration_code/spec.json
COPY catalog.json /airbyte/integration_code/catalog.json

# Make source.py executable
RUN chmod +x /airbyte/integration_code/source.py

# Set entrypoint
ENTRYPOINT ["python", "/airbyte/integration_code/source.py"]
