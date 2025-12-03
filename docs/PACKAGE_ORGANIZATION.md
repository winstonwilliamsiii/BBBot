# Package Organization Guide

## 📦 Package Structure

This project has been organized into component-specific requirement files:

### 1. **Streamlit Application** (`requirements-streamlit.txt`)
For running the main web dashboard locally.

```bash
pip install -r requirements-streamlit.txt
```

**Includes:**
- Streamlit web framework
- Data visualization (Plotly)
- Database connectivity (SQLAlchemy, PyMySQL)
- Financial data APIs (yfinance)
- MLFlow integration
- Machine learning libraries

### 2. **BBBot1 Pipeline & MLFlow** (`bbbot1_pipeline/requirements.txt`)
For data pipeline operations and MLFlow experiment tracking.

```bash
pip install -r bbbot1_pipeline/requirements.txt
```

**Includes:**
- MLFlow tracking and logging
- Database connectivity
- Data processing (Pandas, NumPy)
- Machine learning (scikit-learn)
- API clients (yfinance, requests)
- Airflow orchestration

### 3. **Vercel API** (`api/requirements.txt`)
Minimal dependencies for serverless functions on Vercel.

```bash
pip install -r api/requirements.txt
```

**Includes:**
- Flask (lightweight web framework)
- Pandas (data handling)
- Requests (HTTP client)
- Python-dotenv (environment variables)

### 4. **Master Requirements** (`requirements.txt`)
Comprehensive requirements for full local development. This is the main file for complete installation.

```bash
pip install -r requirements.txt
```

---

## 🚀 Quick Start

### For Full Development Environment:
```bash
# Install everything
pip install -r requirements.txt
```

### For Streamlit Dashboard Only:
```bash
# Install Streamlit app dependencies
pip install -r requirements-streamlit.txt

# Run the dashboard
streamlit run streamlit_app.py
```

### For MLFlow Pipeline Development:
```bash
# Install pipeline dependencies
pip install -r bbbot1_pipeline/requirements.txt

# Test MLFlow connection
python -c "from bbbot1_pipeline.mlflow_config import validate_connection; validate_connection()"
```

### For Vercel Deployment:
The `api/requirements.txt` is automatically used by Vercel for serverless functions.

---

## 📂 File Locations

| Component | Requirements File | Purpose |
|-----------|------------------|---------|
| **Streamlit App** | `requirements-streamlit.txt` | Web dashboard |
| **MLFlow Pipeline** | `bbbot1_pipeline/requirements.txt` | Data pipeline & ML tracking |
| **Vercel API** | `api/requirements.txt` | Serverless functions |
| **Complete Install** | `requirements.txt` | Full development environment |

---

## 🔧 Configuration Files

### MLFlow Configuration
- **File**: `bbbot1_pipeline/mlflow_config.py`
- **Database**: MySQL on port 3307
- **Connection**: `mysql+pymysql://root:root@127.0.0.1:3307/mlflow_db`

### Ticker Configuration
- **File**: `bbbot1_pipeline/tickers_config.yaml`
- **Tickers**: IONQ, QBTS, SOUN, RGTI, AMZN, MSFT, GOOGL

---

## 🐳 Docker Setup

MySQL container must be running for MLFlow:
```bash
docker ps --filter "name=bentley-mysql"
```

Expected output:
```
NAMES           STATUS        PORTS
bentley-mysql   Up X hours    0.0.0.0:3307->3306/tcp
```

---

## ✅ Verification

### Test MLFlow Connection:
```bash
python -c "from bbbot1_pipeline.mlflow_config import validate_connection; validate_connection()"
```

### Test Streamlit App:
```bash
streamlit run streamlit_app.py
```

### Check Python Environment:
```bash
pip list | grep -E "mlflow|streamlit|pandas|sqlalchemy"
```

---

## 📝 Notes

- **Vercel Deployment**: Only `api/` folder is deployed to Vercel
- **MLFlow Storage**: Artifacts stored in `data/mlflow_artifacts/`
- **Database**: MySQL container must be running on port 3307
- **Python Version**: Requires Python 3.8+

---

## 🔄 Updating Dependencies

To update all packages:
```bash
pip install -r requirements.txt --upgrade
```

To update specific component:
```bash
pip install -r requirements-streamlit.txt --upgrade
pip install -r bbbot1_pipeline/requirements.txt --upgrade
pip install -r api/requirements.txt --upgrade
```
