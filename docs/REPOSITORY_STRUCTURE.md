# Bentley Budget Bot - Repository Structure

## 📁 Organized Directory Layout

This repository follows a clean, organized structure for better maintainability and collaboration.

```
BentleyBudgetBot/
├── docs/                          # 📚 All documentation
│   ├── guides/                    # Setup and configuration guides
│   │   ├── AIRBYTE_CLOUD_SETUP.md
│   │   ├── AIRBYTE_CONNECTION_GUIDE.md
│   │   ├── AIRBYTE_FIX_GUIDE.md
│   │   ├── AIRFLOW_CREDENTIALS_GUIDE.md
│   │   ├── AIRFLOW_CREDENTIALS_QUICKREF.md
│   │   ├── AIRFLOW_WINDOWS_FIX.md
│   │   ├── BENTLEY_DB_AIRFLOW_READY.md
│   │   ├── DEPLOYMENT.md
│   │   ├── DOCKER_SERVICES_GUIDE.md
│   │   ├── EXISTING_DATABASE_SETUP.md
│   │   ├── MYSQL_SETUP_GUIDE.md
│   │   ├── ORCHESTRATION_SUCCESS.md
│   │   ├── PLAID_SETUP_GUIDE.md
│   │   ├── SECURITY.md
│   │   └── SERVICE_STATUS.md
│   └── REPOSITORY_STRUCTURE.md  # This file
│
├── docker/                        # 🐳 Docker configuration
│   ├── docker-compose-airflow.yml      # Main orchestration stack
│   ├── docker-compose-airbyte.yml      # Airbyte configuration
│   ├── docker-compose-consolidated.yml # All services combined
│   ├── docker-compose-mlflow.yml       # MLflow configuration
│   ├── docker-compose-services.yml     # Individual services
│   ├── docker-compose.yml              # Streamlit app
│   ├── Dockerfile                      # Streamlit app image
│   ├── Dockerfile.airflow              # Airflow custom image
│   └── .dockerignore                   # Docker ignore patterns
│
├── airflow/                       # ✈️ Apache Airflow
│   ├── dags/                      # DAG definitions
│   │   ├── airbyte_sync_dag.py
│   │   ├── bentley_master_orchestration.py
│   │   ├── example_airbyte_trigger.py
│   │   ├── knime_cli_workflow.py
│   │   ├── mlflow_logging_dag.py
│   │   ├── plaid_financial_dag.py
│   │   └── stocktwits_sentiment_dag.py
│   ├── config/                    # Airflow configuration
│   │   ├── airflow.cfg
│   │   ├── webserver_config.py
│   │   └── logs/                  # Airflow logs
│   └── scripts/                   # Airflow helper scripts
│       ├── airflow.bat
│       ├── airflow_pendulum_fix.py
│       ├── airflow_windows.py
│       ├── init_airflow_simple.py
│       ├── start_airflow_docker.ps1
│       └── start_airflow_webserver.ps1
│
├── airbyte/                       # 🔄 Airbyte integration
│   ├── sources/                   # Custom Airbyte sources
│   │   └── stocktwits/            # Stocktwits sentiment connector
│   │       ├── source.py          # Airbyte source implementation
│   │       ├── spec.json          # Connector specification
│   │       ├── catalog.json       # Stream catalog
│   │       ├── config.json        # Default configuration
│   │       ├── Dockerfile         # Source image
│   │       ├── schema.sql         # MySQL table schema
│   │       └── SETUP_GUIDE.md     # Setup documentation
│   ├── config/                    # Airbyte configuration
│   │   ├── airbyte_config/
│   │   └── temporal-dynamicconfig/
│   └── scripts/                   # Airbyte helper scripts
│       ├── start_airbyte_docker.ps1
│       ├── setup_airbyte_firewall.ps1
│       └── setup_airbyte_fix.ps1
│
├── scripts/                       # 🔧 Utility scripts
│   ├── setup/                     # Setup and installation scripts
│   │   ├── setup_airflow_credentials.ps1
│   │   ├── setup_security.ps1
│   │   ├── setup_stocktwits_pipeline.ps1
│   │   ├── mysql_setup.py
│   │   ├── mysql_setup.sql
│   │   ├── mlflow_setup.py
│   │   └── update_mysql_password.py
│   └── management/                # Service management scripts
│       ├── manage_services.ps1
│       ├── activate_orchestration.ps1
│       ├── diagnose_services.py
│       ├── test_services.ps1
│       ├── validate_deployment.py
│       └── start_webserver.py
│
├── frontend/                      # 💻 Streamlit UI components
│   ├── styles/                    # UI styling
│   │   └── colors.py
│   └── utils/                     # Frontend utilities
│       ├── styling.py
│       └── yahoo.py
│
├── api/                           # 🌐 Vercel serverless API
│   ├── index.py                   # Main API handler
│   ├── budget.js
│   ├── transactions.js
│   └── zapierTriggers.js
│
├── data/                          # 📊 Data storage
│   └── mlflow/                    # MLflow artifacts
│
├── mysql_config/                  # 🗄️ MySQL configuration
│   ├── airbyte_ip_whitelist.sql
│   ├── my.cnf
│   └── plaid_transactions_schema.sql
│
├── .vscode/                       # VS Code workspace settings
│   └── plaid_client.py            # Plaid API client
│
├── .github/                       # GitHub workflows and actions
│
├── resources/                     # Static resources
│   └── templates/
│
├── lib/                           # External libraries
│   ├── apache_airflow_providers_docker-4.4.4/
│   └── documentation/
│
├── streamlit_app.py               # 🎯 Main Streamlit application
├── gsheetsconnection.py           # Google Sheets integration
├── config_env.py                  # Environment configuration
├── requirements.txt               # Python dependencies
├── vercel.json                    # Vercel deployment config
├── config/
│   └── env-templates/             # Environment templates (.env.example, etc.)
├── .gitignore                     # Git ignore patterns
├── LICENSE                        # Project license
└── README.md                      # Project overview
```

## 🎯 Quick Navigation

### Documentation
- **Setup Guides**: `docs/guides/` - All setup and configuration documentation
- **Security**: `docs/guides/SECURITY.md` - Security best practices
- **Deployment**: `docs/guides/DEPLOYMENT.md` - Deployment instructions

### Docker & Infrastructure
- **Main Stack**: `docker/docker-compose-airflow.yml` - Run all services
- **Individual Services**: `docker/docker-compose-*.yml` - Service-specific configs
- **Images**: `docker/Dockerfile*` - Container definitions

### Data Pipeline
- **Airflow DAGs**: `airflow/dags/` - Orchestration workflows
- **Airbyte Sources**: `airbyte/sources/` - Custom data connectors
- **Scripts**: `scripts/` - Setup and management utilities

### Application Code
- **Main App**: `streamlit_app.py` - Streamlit dashboard
- **Frontend**: `frontend/` - Reusable UI components
- **API**: `api/` - Serverless endpoints

## 🚀 Quick Start Commands

### Run Docker Services
```powershell
# From project root
cd docker
docker-compose -f docker-compose-airflow.yml up -d
```

### Setup Scripts
```powershell
# Configure Airflow credentials
.\scripts\setup\setup_airflow_credentials.ps1

# Setup Stocktwits pipeline
.\scripts\setup\setup_stocktwits_pipeline.ps1
```

### Management Scripts
```powershell
# Manage all services
.\scripts\management\manage_services.ps1 -Action start

# Test service connectivity
.\scripts\management\test_services.ps1
```

## 📋 File Organization Principles

1. **Documentation** (`docs/`) - All markdown guides and documentation
2. **Infrastructure** (`docker/`) - All Docker and containerization files
3. **Data Pipeline** (`airflow/`, `airbyte/`) - ETL and orchestration components
4. **Scripts** (`scripts/`) - Utility scripts organized by purpose
5. **Application** (root) - Core application files (Streamlit, API, frontend)
6. **Configuration** (root/folders) - Service-specific config folders

## 🔗 Key Integration Points

### Airflow → Airbyte
- DAGs in `airflow/dags/` trigger Airbyte connections
- Custom sources in `airbyte/sources/` mounted to Airflow containers

### Airflow → MLflow
- MLflow tracking URI: `http://mlflow:5000`
- Artifacts stored in `data/mlflow/`

### MySQL → All Services
- Shared database container
- Schemas in `mysql_config/`
- Port: 3307 (mapped to avoid conflicts)

### Streamlit → MySQL + MLflow
- Main app queries MySQL for financial data
- MLflow integration for model tracking

## 📦 Important Notes

- **All docker-compose commands must be run from the `docker/` directory**
- **Volume mounts use relative paths from `docker/` directory**
- **DAGs automatically sync to Airflow containers**
- **Airbyte sources mounted at `/opt/airflow/airbyte-source-stocktwits`**

## 🔄 Migration Guide

If you have existing scripts or references to old paths:

| Old Path | New Path |
|----------|----------|
| `./AIRFLOW_CREDENTIALS_GUIDE.md` | `docs/guides/AIRFLOW_CREDENTIALS_GUIDE.md` |
| `./docker-compose-airflow.yml` | `docker/docker-compose-airflow.yml` |
| `./dags/` | `airflow/dags/` |
| `./airbyte-source-stocktwits/` | `airbyte/sources/stocktwits/` |
| `./setup_airflow_credentials.ps1` | `scripts/setup/setup_airflow_credentials.ps1` |
| `./manage_services.ps1` | `scripts/management/manage_services.ps1` |

## 📞 Support

For issues or questions:
1. Check relevant guide in `docs/guides/`
2. Review service logs: `docker logs <container-name>`
3. Run diagnostics: `.\scripts\management\diagnose_services.py`

---
**Last Updated**: November 23, 2025
