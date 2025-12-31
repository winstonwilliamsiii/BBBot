# 🚀 BENTLEY BUDGET BOT - ENGINE STARTUP GUIDE

## Quick Start

### One-Command Startup (Recommended)
```powershell
.\START_ALL_ENGINES.ps1
```

This master script starts ALL services in the correct order:
1. **MySQL Database** - Data storage (ports 3306, 3307)
2. **Apache Airflow** - Workflow orchestration (port 8080)
3. **Airbyte** - Data integration (port 8000)
4. **MLflow** - ML experiment tracking (port 5000)
5. **Streamlit** - Trading dashboard (port 8501)

---

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow UI | http://localhost:8080 | admin / admin |
| Airbyte UI | http://localhost:8000 | Set on first login |
| MLflow Tracking | http://localhost:5000 | None |
| Streamlit Dashboard | http://localhost:8501 | None |
| MySQL Database | localhost:3306, 3307 | root / root |

---

## Individual Service Startup

If you need to start services individually:

### MySQL
```powershell
docker start mysql
```

### Airflow
```powershell
.\airflow\scripts\start_airflow_docker.ps1
```

### Airbyte
```powershell
.\airbyte\scripts\start_airbyte_docker.ps1
```

### MLflow
```powershell
python -m mlflow server --host 0.0.0.0 --port 5000
```

### Streamlit
```powershell
.\RESTART_STREAMLIT.ps1
```

---

## Discord Alerts Setup

### Get Your Discord Webhook URL:

1. Open Discord → Go to your server
2. Server Settings → Integrations → Webhooks
3. Click **"New Webhook"**
4. Name it: "Trading Alerts"
5. Choose channel (e.g., #trading-alerts)
6. **Copy Webhook URL** (looks like: `https://discord.com/api/webhooks/1234567890/abcdefg...`)

### Configure the Bot:

1. Open `.env` file in the project root
2. Find line: `DISCORD_WEBHOOK=https://discord.com/api/webhooks/your_webhook_id`
3. **Replace** `your_webhook_id` with your actual webhook URL
4. Save the file

Example:
```env
DISCORD_WEBHOOK=https://discord.com/api/webhooks/1234567890123456789/aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890abcdefghijklmnop
```

### Test Discord Alerts:

```powershell
cd mvp2-alerts
node index.js
```

This sends a test alert to your Discord channel with:
- Top 5 market gainers
- Top 5 market losers  
- Your portfolio moves ≥5%

---

## Troubleshooting

### Docker Issues
```powershell
# Check if Docker is running
docker info

# Restart Docker Desktop if needed
# Then run: .\START_ALL_ENGINES.ps1
```

### Port Conflicts
If ports are already in use:
```powershell
# Find process using port 8080 (example)
netstat -ano | findstr :8080

# Kill process by PID
taskkill /PID <PID> /F
```

### Service Not Starting
```powershell
# Check logs for specific service
docker-compose logs -f airflow-webserver
docker-compose logs -f airbyte-webapp
```

### Stop All Services
```powershell
# Stop all Docker containers
docker-compose down

# Or kill individual processes
taskkill /F /IM python.exe /T
```

---

## Daily Workflow

### Morning Routine:
1. Start Docker Desktop
2. Run: `.\START_ALL_ENGINES.ps1`
3. Wait 2-3 minutes for all services to initialize
4. Check dashboard: http://localhost:8501
5. Verify Airflow DAGs: http://localhost:8080

### During Trading Hours:
- Monitor Discord for alerts (auto-sent at 9:30 AM, 12:00 PM, 3:30 PM ET)
- Check MLflow experiments: http://localhost:5000
- Review Streamlit portfolio: http://localhost:8501

### End of Day:
- Let services run overnight (they're lightweight)
- Or stop with: `docker-compose down`

---

## Service Dependencies

```
MySQL (Foundation)
  ↓
Airflow (Orchestration) + Airbyte (Data Ingestion)
  ↓
MLflow (ML Tracking)
  ↓
Streamlit (Dashboard)
```

**Note:** Start in this order for proper initialization. The master script (`START_ALL_ENGINES.ps1`) handles this automatically.

---

## Need Help?

- **Logs Location**: `./logs/` (for Airflow DAGs)
- **MLflow Data**: `./data/mlflow/`
- **Docker Logs**: `docker-compose logs [service-name]`
- **Streamlit Logs**: Check terminal where Streamlit is running

---

## Quick Reference

| Command | Action |
|---------|--------|
| `.\START_ALL_ENGINES.ps1` | Start everything |
| `docker ps` | Check running containers |
| `docker-compose down` | Stop all services |
| `.\RESTART_STREAMLIT.ps1` | Restart Streamlit only |
| `node mvp2-alerts/index.js` | Test Discord alerts |

---

**Last Updated:** December 30, 2025  
**Platform:** Windows 11 + Docker Desktop
