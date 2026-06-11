# 🎯 Quick Start Guide

## Automatic MySQL Docker Startup - ENABLED! ✨

Your workspace is now configured to **automatically start MySQL Docker containers** when you open VS Code!

### What Happens Automatically

When you open this workspace:
1. ✅ Docker Desktop starts (if not running)
2. ✅ MySQL containers launch
3. ✅ Connection is verified
4. ✅ You get a status report in the terminal

### First Time Setup

**You'll see this prompt once:**
```
This workspace has tasks that run automatically when you open it.
Do you allow automatic tasks in this workspace?
```

👉 **Click "Allow"** to enable auto-start forever!

---

## 📋 Available Commands

Press `Ctrl+Shift+P` and type "Run Task" to access:

### 🚀 Start MySQL Docker Environment
Start everything manually (or re-run if needed)

### 🛑 Stop MySQL Docker Containers  
Stop containers when you're done working

### 🔄 Restart MySQL Docker Containers
Restart if containers become unresponsive

### 📊 View MySQL Container Logs
See real-time MySQL logs for debugging

### 🔌 Test MySQL Connection
Quick health check

---

## 💾 MySQL Connection Settings

**For MySQL Workbench or any SQL client:**

```
Host:     127.0.0.1
Port:     3307
Username: root
Password: root
Database: mansa_bot
```

---

## 🔧 Manual Control

### Run the script manually:
```powershell
.\start_mysql_docker.ps1
```

### Disable auto-start:
1. Open `.vscode/settings.json`
2. Change: `"task.allowAutomaticTasks": "off"`

---

## 🐛 Troubleshooting

**Auto-start not working?**
- Make sure you clicked "Allow" when prompted
- Check: `Ctrl+Shift+P` → "Tasks: Manage Automatic Tasks in Folder"

**Docker errors?**
- Ensure Docker Desktop is installed
- Try running the task manually to see detailed errors

**Connection refused?**
- Containers might still be starting, wait 10-20 seconds
- Run: `docker ps` to verify containers are running

---

## 📚 Learn More

See [.vscode/README.md](.vscode/README.md) for detailed documentation.

---

**You're all set! Just open VS Code and MySQL will be ready. 🎉**
