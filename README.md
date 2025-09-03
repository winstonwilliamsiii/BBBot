# Bentley Bot: Fiscal Budget Dashboard

This is a Streamlit-based web application that:

- Ingests 36 months of personal and small-business income/expense data from Google Sheets.
- Syncs bank and billing transactions via QuickBooks API.
- Stores and transforms data in MySQL using Airbyte.
- Orchestrates notifications sucha as upcoming-bill email alerts with Zapier.
- Presents an interactive dashboard with charts for Trend Analysis, Cash Flow Analysis and Spending categories.
- Embeds a chatbot for macro-economic forecasts, US demographic comparisons, and global scenario analysis.

<<<<<<< HEAD
## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation & Deployment

#### Option 1: Docker (Recommended)
```bash
# Clone the repository
git clone https://github.com/winstonwilliamsiii/BBBot.git
cd BBBot

# Start the application with MySQL database
docker-compose up --build -d

# Load GDP data into the database
docker-compose exec app python load_data_to_mysql.py

# Access the application
# Web UI: http://localhost:8501
# MySQL: localhost:3306
```

#### Option 2: WSL (Windows Subsystem for Linux)
For detailed WSL deployment instructions, see: **[WSL_DEPLOYMENT_GUIDE.md](WSL_DEPLOYMENT_GUIDE.md)**

## 🗄️ Database Setup

The application now includes a MySQL database with the following configuration:

### Connection Details
- **Database Name**: `Bentley_Budget`
- **Host**: `127.0.0.1` (localhost) or `mysql` (Docker)
- **Port**: `3306`
- **User**: `root`
- **Password**: `rootpassword`
- **MySQL Version**: `8.0.40`

### Database Schema
The database includes two main tables:
1. **`gdp_data`** - Raw GDP data with year columns (1960-2022)
2. **`gdp_yearly_data`** - Normalized table for efficient querying

### Data Loading
The application automatically loads GDP data from the CSV file during initialization. You can also manually load data:

```bash
# Manual data loading
docker-compose exec app python load_data_to_mysql.py
```

## 📊 Features

### Current Features
- ✅ **MySQL Database Integration** - Complete database setup with GDP data
- ✅ **Docker Containerization** - Easy deployment and management
- ✅ **Streamlit Web Interface** - Interactive dashboard
- ✅ **GDP Data Analysis** - 13,200+ data points across 262 countries/regions
- ✅ **Database Connection Module** - Robust database connectivity
- ✅ **WSL Support** - Comprehensive Windows Subsystem for Linux guide

### Planned Features
- 🔄 Google Sheets integration for personal finance data
- 🔄 QuickBooks API integration
- 🔄 AI chatbot for economic analysis
- 🔄 Advanced visualizations and charts
- 🔄 Email notifications and alerts

## 🛠️ Development

### Project Structure
```
BBBot/
├── data/                          # Data files
│   └── gdp_data.csv              # GDP dataset
├── mysql/                        # MySQL configuration
│   ├── init/                     # Database initialization
│   └── schema/                   # Database schema
├── .devcontainer/                # Development container config
├── docker-compose.yml           # Docker services
├── Dockerfile                   # Application container
├── database_connection.py       # Database connection module
├── load_data_to_mysql.py        # Data loading script
├── streamlit_app.py             # Main Streamlit application
├── requirements.txt             # Python dependencies
└── WSL_DEPLOYMENT_GUIDE.md      # WSL deployment guide
```

### Database Connection
The application uses a custom database connection module (`database_connection.py`) that provides:
- Automatic connection management
- Query methods for GDP data
- Error handling and retry logic
- Support for both Docker and local environments

### Environment Variables
```yaml
MYSQL_HOST: mysql
MYSQL_PORT: 3306
MYSQL_USER: root
MYSQL_PASSWORD: rootpassword
MYSQL_DATABASE: Bentley_Budget
```

## 🔧 Configuration

### Docker Services
- **app**: Streamlit application (port 8501)
- **mysql**: MySQL database (port 3306)

### Ports
- **8501**: Streamlit web application
- **3306**: MySQL database

## 📈 Data Sources

### GDP Data
- **Source**: World Bank GDP data
- **Coverage**: 1960-2022
- **Countries**: 262 countries and regions
- **Records**: 13,200+ data points

### Data Tables
1. **gdp_data**: Raw data with year columns
2. **gdp_yearly_data**: Normalized data for efficient querying

## 🚀 Deployment Options

### 1. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run streamlit_app.py
```

### 2. Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### 3. WSL Deployment
See **[WSL_DEPLOYMENT_GUIDE.md](WSL_DEPLOYMENT_GUIDE.md)** for detailed instructions.

### 4. Production Deployment
For production deployment, consider:
- Using environment variables for secrets
- Setting up SSL/TLS certificates
- Configuring proper firewall rules
- Implementing database backups
- Setting up monitoring and logging

## 🛠️ Troubleshooting

### Common Issues

#### Docker Issues
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs

# Restart services
docker-compose restart
```

#### Database Issues
```bash
# Check database connection
docker-compose exec mysql mysql -u root -prootpassword -e "SHOW DATABASES;"

# Reload data
docker-compose exec app python load_data_to_mysql.py
```

#### Port Conflicts
```bash
# Check port usage
sudo netstat -tulpn | grep :8501
sudo netstat -tulpn | grep :3306
```

For more detailed troubleshooting, see the **[WSL_DEPLOYMENT_GUIDE.md](WSL_DEPLOYMENT_GUIDE.md)**.

## 📞 Support

### Getting Help
1. Check the troubleshooting section above
2. Review the WSL deployment guide
3. Check GitHub issues for known problems
4. Verify all prerequisites are installed

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- World Bank for GDP data
- Streamlit for the web framework
- Docker for containerization
- MySQL for the database system

---

**Live Demo**: [bbbot305.streamlit.app](https://bbbot305.streamlit.app)

---

**Live Demo**: [bbbot305.streamlit.app](https://bbbot305.streamlit.app)

# Process Flow Image

https://app.diagrams.net/#G1puqYkLeP-SrmQ8khMA-ualIAiFyEnBJj#%7B%22pageId%22%3A%22V-6in7jooW1nca1V13b-%22%7D
<img width="460" height="373" alt="image" src="https://github.com/user-attachments/assets/433b4e08-945b-4ec0-b9f9-9a7b8085e602" />
