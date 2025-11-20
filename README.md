# Bentley Bot: Fiscal Budget Dashboard

This is a Streamlit-based web application that:

- Ingests 36 months of personal and small-business income/expense data from Google Sheets.
- Syncs bank and billing transactions via QuickBooks API (or alternative financial aggregators).
- Stores and transforms data in MySQL (self-hosted or Appwrite BaaS) using Airbyte.
- Orchestrates notifications with Zapier and AI workflows with n8n.
- Presents an interactive dashboard with charts for spending categories (Shopping, Bank Fees, Miscellaneous, etc.) and upcoming-bill email alerts.
- Embeds a chatbot for macro-economic forecasts, US demographic comparisons, and global scenario analysis.

## 🚀 Quick Start

### Can't Access Airflow/Airbyte/MLflow in Browser?

See [SERVICES_QUICK_START.md](SERVICES_QUICK_START.md) for a complete troubleshooting guide!

### Start All Services

```powershell
.\manage_services.ps1 -Service all -Action start
```

**Access Points:**
- **Streamlit App**: http://localhost:8501
- **Airflow UI**: http://localhost:8080 (admin/admin)
- **Airbyte UI**: http://localhost:8000
- **MLflow UI**: http://localhost:5000

## 📚 Documentation

- **[SERVICES_QUICK_START.md](SERVICES_QUICK_START.md)** - Fix localhost access issues
- **[MLFLOW_INTEGRATION.md](MLFLOW_INTEGRATION.md)** - MLflow + Airflow integration guide
- **[DOCKER_SERVICES_GUIDE.md](DOCKER_SERVICES_GUIDE.md)** - Architecture and Docker setup
- **[AIRFLOW_WINDOWS_FIX.md](AIRFLOW_WINDOWS_FIX.md)** - Windows-specific fixes

## 🔧 Troubleshooting

```powershell
# Diagnose service issues
.\troubleshoot_services.ps1

# View service status
.\manage_services.ps1 -Action status

# View logs
.\manage_services.ps1 -Service airflow -Action logs
```

# Process Flow Image

https://app.diagrams.net/#G1puqYkLeP-SrmQ8khMA-ualIAiFyEnBJj#%7B%22pageId%22%3A%22V-6in7jooW1nca1V13b-%22%7D
<img width="460" height="373" alt="image" src="https://github.com/user-attachments/assets/433b4e08-945b-4ec0-b9f9-9a7b8085e602" />
