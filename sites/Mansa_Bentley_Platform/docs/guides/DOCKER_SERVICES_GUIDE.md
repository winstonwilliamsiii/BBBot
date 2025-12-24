# Bentley Budget Bot - Docker Services Guide

This guide explains how to run Bentley Budget Bot with **separate Docker Compose configurations** for different services.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────┐
│              Bentley Budget Bot             │
├─────────────────┬───────────────┬───────────┤
│   Streamlit     │    Airflow    │  Airbyte  │
│   (Port 8501)   │ (Port 8080)   │(Port 8000)│
│                 │               │           │
│ • Main App      │ • Orchestration│• Data ETL │
│ • Yahoo Finance │ • DAG Mgmt    │• API Sync │
│ • Portfolio UI  │ • Scheduling  │• Transform│
└─────────────────┴───────────────┴───────────┘
            │             │             │
            └─────────────┼─────────────┘
                          │
                    MySQL Database
                    (Port 3306)
```

## 📁 Docker Compose Files

### 1. **`docker-compose-airflow.yml`** - Airflow + Streamlit + MySQL
- **Airflow Webserver** (8080) - UI and API
- **Airflow Scheduler** - DAG execution
- **Airflow Worker** - Task execution  
- **Streamlit App** (8501) - Main application
- **MySQL Database** (3306) - Shared storage
- **Redis** (6379) - Airflow message broker

### 2. **`docker-compose-airbyte.yml`** - Airbyte Platform
- **Airbyte Web UI** (8000) - Configuration interface
- **Airbyte API** (8001) - REST API for integrations
- **Airbyte Worker** - Data sync execution
- **Airbyte Scheduler** - Job scheduling
- **PostgreSQL** - Airbyte metadata storage

### 3. **`docker-compose.yml`** - Original Streamlit Only
- **Streamlit App** (8501) - Standalone mode

## 🚀 Quick Start Commands

### Start Everything
```powershell
# Start all services (recommended)
.\manage_services.ps1 -Service all -Action start

# Or start individual services
.\start_airflow_docker.ps1    # Airflow + Streamlit + MySQL
.\start_airbyte_docker.ps1    # Airbyte platform
```

### Access Applications
- **Streamlit App**: http://localhost:8501
- **Airflow UI**: http://localhost:8080 (admin/admin)
- **Airbyte UI**: http://localhost:8000

### Manage Services
```powershell
# Check status
.\manage_services.ps1 -Action status

# View logs
.\manage_services.ps1 -Service airflow -Action logs
.\manage_services.ps1 -Service airbyte -Action logs

# Stop services
.\manage_services.ps1 -Service all -Action stop
```

## 🔧 Why Separate Docker Compose Files?

### ✅ **Benefits of Separation:**

1. **Independent Scaling** - Scale Airflow workers without affecting Airbyte
2. **Resource Isolation** - Airbyte can be resource-intensive
3. **Different Lifecycles** - Update/restart services independently  
4. **Network Separation** - Different networks for security
5. **Port Management** - Avoid conflicts between services
6. **Easier Debugging** - Isolate issues to specific services

### 🔄 **Integration Points:**

- **Airflow → Airbyte**: Via HTTP API (localhost:8001)
- **Airflow → MySQL**: Direct database connection
- **Streamlit → MySQL**: Shared database access
- **All Services**: Can communicate through host networking

## 📋 Configuration Files

### Airflow Integration (`Airbyt_sync_DAG.py`)
```python
# Configured for Docker Airbyte
AIRBYTE_API = "http://localhost:8001"
CONNECTION_ID = "your-connection-id"  # Set in Airbyte UI
```

### Environment Variables
```bash
# Airflow
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=mysql+pymysql://airflow:airflow@mysql:3306/mansa_bot

# Streamlit  
DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=mansa_bot
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's using ports
   netstat -ano | findstr :8080
   netstat -ano | findstr :8000
   ```

2. **Database Connection Issues**
   ```bash
   # Check MySQL container
   docker exec -it bentley-mysql mysql -u root -p
   ```

3. **Airbyte Not Starting**
   ```powershell
   # Check logs
   docker-compose -f docker-compose-airbyte.yml logs airbyte-server
   ```

### Service Dependencies

**Start Order (if manual):**
1. MySQL Database (in airflow compose)
2. Redis (in airflow compose) 
3. Airflow Services
4. Airbyte Services (independent)

## 📊 Resource Requirements

### **Minimum System Requirements:**
- **RAM**: 8GB (16GB recommended)
- **CPU**: 4 cores
- **Disk**: 10GB free space
- **Docker**: Desktop 4.0+

### **Service Resource Usage:**
- **Airbyte**: ~2-4GB RAM (heaviest)
- **Airflow**: ~1-2GB RAM  
- **MySQL**: ~500MB RAM
- **Streamlit**: ~200MB RAM

## 🔗 Integration Workflow

```mermaid
graph LR
    A[Airbyte] -->|ETL Data| B[MySQL]
    B -->|Store Data| C[Airflow]
    C -->|Orchestrate| A
    C -->|Schedule Tasks| D[Streamlit]
    D -->|Display Data| B
```

1. **Airbyte** extracts data from external sources
2. **MySQL** stores the transformed data
3. **Airflow** orchestrates and schedules the pipeline
4. **Streamlit** provides the user interface

## 📝 Next Steps

1. **Configure Airbyte Sources** - Set up data connections in UI
2. **Update Connection IDs** - Get actual IDs from Airbyte for your DAG
3. **Test Integration** - Run the Airbyte sync DAG in Airflow
4. **Monitor Performance** - Use Docker stats and service logs
5. **Set Up Monitoring** - Consider adding Prometheus/Grafana

---

**Need Help?** Check the individual startup scripts or run:
```powershell
.\manage_services.ps1  # Shows usage examples
```