# Bentley Bot: Financial Portfolio Dashboard

A comprehensive financial data platform with real-time portfolio tracking, automated data pipelines, and ML-powered insights.

## 🌐 Live Demo

**Streamlit Cloud**: https://bbbot305.streamlit.app/

## 🎯 Features

- **Portfolio Dashboard**: Real-time tracking of stocks, ETFs, and financial holdings via Yahoo Finance
- **Live Crypto Dashboard**: Real-time cryptocurrency prices and charts
- **Multi-Broker Trading**: Automated trading across Webull, IBKR, and Binance (local only)
- **Data Pipeline**: Automated ETL using Apache Airflow + Airbyte + dbt + MLflow
- **Sentiment Analysis**: Stocktwits social sentiment tracking for market insights
- **Financial Integration**: Plaid API for bank/billing transaction sync
- **ML Tracking**: MLflow experiment tracking and model management
- **Interactive Charts**: Spending categories, portfolio performance, and trend analysis
- **Secure**: Airflow Variables/Connections for encrypted credential management

## 🏗️ Architecture

### Tech Stack
- **Frontend**: Streamlit (Python)
- **Orchestration**: Apache Airflow (CeleryExecutor)
- **Data Integration**: Airbyte (Cloud + Custom Sources)
- **ML Platform**: MLflow
- **Database**: MySQL 8.0
- **Cache**: Redis 7
- **Deployment**: Docker Compose + Vercel Serverless

### Data Flow
```
Financial APIs (Plaid, Yahoo Finance, Stocktwits)
    ↓
Airbyte (ETL & Custom Sources)
    ↓
MySQL Database
    ↓
Apache Airflow (Orchestration)
    ↓
MLflow (Experiment Tracking)
    ↓
Streamlit Dashboard
```

## 📁 Repository Structure

See [docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md) for detailed organization.

```
BentleyBudgetBot/
├── docs/                    # 📚 Documentation & guides
├── docker/                  # 🐳 Docker compose files
├── airflow/                 # ✈️ Airflow DAGs & config
├── airbyte/                 # 🔄 Custom Airbyte sources
├── scripts/                 # 🔧 Setup & management scripts
├── frontend/                # 💻 Streamlit UI components
├── api/                     # 🌐 Vercel serverless API
└── streamlit_app.py         # 🎯 Main application
```

## 🚀 Quick Start

### Option 1: Cloud Demo (Read-Only)
Visit https://bbbot305.streamlit.app/ for a live demo with portfolio tracking and crypto dashboard.

### Option 2: Local Development (Full Features)

#### Prerequisites
- Docker Desktop
- PowerShell (Windows) or Bash
- Python 3.11+

#### 1. Clone & Setup
```bash
git clone https://github.com/winstonwilliamsiii/BBBot.git
cd BentleyBudgetBot

# Install dependencies
pip install -r requirements-local.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

#### 2. Start Services
```powershell
cd docker
docker-compose -f docker-compose-airflow.yml up -d
```

#### 3. Launch Streamlit
```bash
streamlit run streamlit_app.py
```

#### 4. Access Applications
- **Streamlit Dashboard**: http://localhost:8501
- **Airflow UI**: http://localhost:8080 (admin/admin)
- **MLflow**: http://localhost:5000

### Cloud vs Local Features

| Feature | Cloud (bbbot305.streamlit.app) | Local Development |
|---------|-------------------------------|-------------------|
| Portfolio Dashboard | ✅ | ✅ |
| Live Crypto Dashboard | ✅ | ✅ |
| Yahoo Finance Integration | ✅ | ✅ |
| Broker Trading | ❌ | ✅ |
| Airflow Orchestration | ❌ | ✅ |
| MLFlow Tracking | ❌ | ✅ |
| dbt Transformations | ❌ | ✅ |
| MySQL/Snowflake | ❌ | ✅ |

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [Airflow Credentials](docs/guides/AIRFLOW_CREDENTIALS_GUIDE.md) | Secure credential management |
| [Stocktwits Setup](airbyte/sources/stocktwits/SETUP_GUIDE.md) | Sentiment data pipeline |
| [Plaid Setup](docs/guides/PLAID_SETUP_GUIDE.md) | Bank transaction integration |
| [Docker Services](docs/guides/DOCKER_SERVICES_GUIDE.md) | Service management |
| [Deployment](docs/guides/DEPLOYMENT.md) | Production deployment guide |
| [Security](docs/guides/SECURITY.md) | Security best practices |

## 🔧 Common Tasks

### Setup Airflow Credentials
```powershell
.\scripts\setup\setup_airflow_credentials.ps1
```

### Setup Stocktwits Pipeline
```powershell
.\scripts\setup\setup_stocktwits_pipeline.ps1
```

### Manage Services
```powershell
.\scripts\management\manage_services.ps1 -Action start
.\scripts\management\manage_services.ps1 -Action stop
.\scripts\management\manage_services.ps1 -Action restart
```

### View Logs
```powershell
docker logs bentley-airflow-webserver
docker logs bentley-mysql
docker logs bentley-mlflow
```

## 🧪 Development

### Local Streamlit Development
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Run Tests
```powershell
.\scripts\management\test_services.ps1
```

## 📊 Data Sources

- **Yahoo Finance**: Stock/ETF price data & portfolio scraping
- **Plaid API**: Bank transactions & account balances
- **Stocktwits**: Social sentiment analysis
- **CSV Uploads**: Manual portfolio data import

## 🔐 Security

- Airflow Fernet encryption for sensitive variables
- Environment-based credential management
- API key rotation support
- MySQL IP whitelisting for Airbyte Cloud

See [docs/guides/SECURITY.md](docs/guides/SECURITY.md) for details.

## 🌐 Deployment

### Vercel (Serverless)
```bash
vercel deploy
```

### Docker (Self-hosted)
```bash
cd docker
docker-compose -f docker-compose-airflow.yml up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 📞 Support

- **Issues**: GitHub Issues
- **Diagnostics**: `.\scripts\management\diagnose_services.py`
- **Logs**: `docker logs <container-name>`

---

# Process Flow Diagram

https://app.diagrams.net/#G1puqYkLeP-SrmQ8khMA-ualIAiFyEnBJj#%7B%22pageId%22%3A%22V-6in7jooW1nca1V13b-%22%7D
<img width="460" height="373" alt="image" src="https://github.com/user-attachments/assets/433b4e08-945b-4ec0-b9f9-9a7b8085e602" />

**Built with ❤️ using Python, Streamlit, Airflow, and Docker**
