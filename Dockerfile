FROM python:3.11

WORKDIR /workspace

# Install system dependencies including MySQL client
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install additional MySQL-related packages
RUN pip install mysql-connector-python pymysql

COPY . . 