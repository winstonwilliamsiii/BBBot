# Bentley Budget Bot - WSL Deployment Guide

This comprehensive guide will walk you through setting up and running the Bentley Budget Bot on Windows Subsystem for Linux (WSL).

## 📋 Prerequisites

### 1. WSL Installation
If you haven't installed WSL yet, follow these steps:

```powershell
# Open PowerShell as Administrator and run:
wsl --install
```

This will install WSL 2 with Ubuntu as the default distribution.

### 2. Update WSL
After installation, restart your computer and update WSL:

```bash
# Update package list
sudo apt update

# Upgrade packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git
```

### 3. Install Docker on WSL

#### Option A: Install Docker Desktop for Windows (Recommended)
1. Download Docker Desktop from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Install Docker Desktop
3. Enable WSL 2 integration in Docker Desktop settings
4. Restart Docker Desktop

#### Option B: Install Docker directly in WSL
```bash
# Remove any old versions
sudo apt remove docker docker-engine docker.io containerd runc

# Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add your user to docker group
sudo usermod -aG docker $USER

# Start Docker service
sudo service docker start

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 🚀 Deployment Steps

### 1. Clone the Repository
```bash
# Navigate to your desired directory
cd ~

# Clone the repository
git clone https://github.com/winstonwilliamsiii/BBBot.git

# Navigate to the project directory
cd BBBot
```

### 2. Verify Docker Installation
```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version

# Test Docker
docker run hello-world
```

### 3. Build and Run the Application
```bash
# Build and start the containers
docker-compose up --build -d

# Check container status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Load Data into MySQL
```bash
# Load the GDP data into the database
docker-compose exec app python load_data_to_mysql.py
```

### 5. Access the Application
- **Web Application**: http://localhost:8501
- **MySQL Database**: localhost:3306

## 🔧 Configuration

### Database Connection Details
- **Host**: localhost (or mysql from within containers)
- **Port**: 3306
- **Database**: Bentley_Budget
- **Username**: root
- **Password**: rootpassword

### Environment Variables
The application uses the following environment variables (configured in docker-compose.yml):
```yaml
MYSQL_HOST: mysql
MYSQL_PORT: 3306
MYSQL_USER: root
MYSQL_PASSWORD: rootpassword
MYSQL_DATABASE: Bentley_Budget
```

## 📊 Database Schema

The application creates two main tables:

### 1. gdp_data
Raw GDP data with year columns (1960-2022)

### 2. gdp_yearly_data
Normalized table for efficient querying with columns:
- country_code
- country_name
- year
- gdp_value

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. Docker Permission Denied
```bash
# If you get permission errors, add your user to docker group
sudo usermod -aG docker $USER

# Log out and log back in, or restart WSL
wsl --shutdown
# Then restart WSL
```

#### 2. Port Already in Use
```bash
# Check what's using the ports
sudo netstat -tulpn | grep :8501
sudo netstat -tulpn | grep :3306

# Stop conflicting services or change ports in docker-compose.yml
```

#### 3. MySQL Connection Issues
```bash
# Check if MySQL container is running
docker-compose ps

# Check MySQL logs
docker-compose logs mysql

# Restart MySQL container
docker-compose restart mysql
```

#### 4. Data Loading Issues
```bash
# Check if data file exists
ls -la data/gdp_data.csv

# Manually load data
docker-compose exec app python load_data_to_mysql.py

# Check database tables
docker-compose exec mysql mysql -u root -prootpassword -e "USE Bentley_Budget; SHOW TABLES;"
```

#### 5. WSL Memory Issues
If you encounter memory issues, create a `.wslconfig` file in your Windows user directory:

```ini
[wsl2]
memory=4GB
processors=2
swap=2GB
```

### Performance Optimization

#### 1. Increase Docker Resources
In Docker Desktop settings:
- Memory: 4GB or more
- CPUs: 2 or more
- Disk image size: 64GB or more

#### 2. WSL Performance
```bash
# Update WSL regularly
sudo apt update && sudo apt upgrade -y

# Clean up Docker
docker system prune -a

# Monitor resource usage
htop
```

## 🔄 Maintenance

### Regular Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose down
docker-compose up --build -d

# Update data
docker-compose exec app python load_data_to_mysql.py
```

### Backup Database
```bash
# Create backup
docker-compose exec mysql mysqldump -u root -prootpassword Bentley_Budget > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose exec -T mysql mysql -u root -prootpassword Bentley_Budget < backup_file.sql
```

### Clean Up
```bash
# Stop containers
docker-compose down

# Remove volumes (WARNING: This will delete all data)
docker-compose down -v

# Clean up Docker images
docker system prune -a
```

## 📱 Accessing the Application

### Local Access
- **Streamlit App**: http://localhost:8501
- **MySQL Workbench**: Connect to localhost:3306

### Remote Access (Optional)
To access from other devices on your network:

1. Find your WSL IP address:
```bash
ip addr show eth0
```

2. Update docker-compose.yml to bind to all interfaces:
```yaml
ports:
  - "0.0.0.0:8501:8501"
  - "0.0.0.0:3306:3306"
```

3. Access via your computer's IP address:
- http://YOUR_COMPUTER_IP:8501

## 🔒 Security Considerations

### Production Deployment
For production use, consider:

1. **Change default passwords**
2. **Use environment variables for secrets**
3. **Enable SSL/TLS**
4. **Set up proper firewall rules**
5. **Regular security updates**

### Development Security
```bash
# Use strong passwords
# Limit network access
# Regular backups
# Monitor logs
```

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Docker and WSL logs
3. Verify all prerequisites are installed
4. Check GitHub issues for known problems

## 🎯 Quick Start Commands

```bash
# Complete setup in one go
cd ~
git clone https://github.com/winstonwilliamsiii/BBBot.git
cd BBBot
docker-compose up --build -d
docker-compose exec app python load_data_to_mysql.py

# Access the application
# Open browser: http://localhost:8501
```

---

**Note**: This guide assumes you're using WSL 2 with Ubuntu. If you're using a different distribution, some commands may vary slightly. 