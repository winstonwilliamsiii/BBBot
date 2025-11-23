# 🎯 Airbyte Cloud MySQL Connection - Quick Reference

## ✅ Configuration Complete!

All Airbyte Cloud IP addresses have been whitelisted for MySQL access.

---

## 📋 MySQL Connection Details for Airbyte Cloud

| Setting | Value |
|---------|-------|
| **Host** | `186.112.188.47` (your public IP) |
| **Port** | `3307` |
| **Database** | `mansa_bot` |
| **Username** | `airbyte` |
| **Password** | `airbyte_secure_password_2025` |
| **SSL Mode** | `preferred` (or `disabled` for testing) |

---

## ✅ Verified Configuration

### 1. MySQL Users Created (20 total)
- ✅ `airbyte@%` (wildcard - backup)
- ✅ 8 US Region IPs (34.106.x.x)
- ✅ 3 EU Region IPs (13.37.x.x, 35.181.x.x)
- ✅ 8 CIDR Range IPs (34.33.7.0-7)

### 2. MySQL Network Settings
- ✅ Bind Address: `*` (all interfaces)
- ✅ Port: `3307` exposed on host
- ✅ Authentication: `mysql_native_password`

### 3. Database Permissions
- ✅ SELECT, INSERT, UPDATE, DELETE
- ✅ CREATE, DROP, ALTER, INDEX
- ✅ CREATE TEMPORARY TABLES, LOCK TABLES

---

## 🔥 Windows Firewall Setup

To allow Airbyte IPs through Windows Firewall, run as Administrator:

```powershell
cd C:\Users\winst\BentleyBudgetBot
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_airbyte_firewall.ps1
```

This will create 12 firewall rules allowing inbound connections from all Airbyte Cloud IPs.

---

## 🧪 Test Connection

### From Local Machine
```bash
mysql -h 127.0.0.1 -P 3307 -uairbyte -pairbyte_secure_password_2025 mansa_bot
```

### From Docker Container
```bash
docker exec -it bentley-mysql mysql -uairbyte -pairbyte_secure_password_2025 mansa_bot
```

### Test Query
```sql
SHOW TABLES;
SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'mansa_bot';
```

---

## 📊 Whitelisted IP Addresses

### US Region (8 IPs)
- 34.106.109.131
- 34.106.196.165
- 34.106.60.246
- 34.106.229.69
- 34.106.127.139
- 34.106.218.58
- 34.106.115.240
- 34.106.225.141

### EU Region (3 IPs)
- 13.37.4.46
- 13.37.142.60
- 35.181.124.238

### CIDR Range (8 IPs)
- 34.33.7.0/29 (34.33.7.0 - 34.33.7.7)

---

## 🚀 Next Steps

### 1. Configure Airbyte Cloud
1. Go to https://cloud.airbyte.com
2. Navigate to **Sources** → **New Source**
3. Select **MySQL** as the source type
4. Enter the connection details above
5. Test the connection
6. Configure sync schedule and destinations

### 2. Verify Firewall (if on Windows)
Run the firewall script to allow Airbyte IPs:
```powershell
.\setup_airbyte_firewall.ps1
```

### 3. Router/Modem Port Forwarding (if needed)
If you're behind a router, forward port **3307** to your machine's local IP.

### 4. Cloud Deployment (recommended)
For production, consider:
- Deploy MySQL to cloud (AWS RDS, Azure Database, GCP Cloud SQL)
- Use security groups instead of IP whitelisting
- Enable SSL/TLS encryption

---

## 🔐 Security Notes

### Change Default Password
```sql
ALTER USER 'airbyte'@'%' IDENTIFIED BY 'your_strong_password_here';
FLUSH PRIVILEGES;
```

Update `.env` file with new password:
```env
AIRBYTE_MYSQL_PASSWORD=your_strong_password_here
```

### Enable SSL (Optional)
Generate SSL certificates and configure in `my.cnf`:
```ini
[mysqld]
require_secure_transport=ON
ssl-ca=/etc/mysql/ssl/ca.pem
ssl-cert=/etc/mysql/ssl/server-cert.pem
ssl-key=/etc/mysql/ssl/server-key.pem
```

---

## 🛠 Troubleshooting

### Connection Timeout
- Check Windows Firewall: `Get-NetFirewallRule | Where-Object { $_.DisplayName -like "Airbyte-MySQL-*" }`
- Verify MySQL is running: `docker ps | grep bentley-mysql`
- Test port accessibility: `Test-NetConnection -ComputerName 186.112.188.47 -Port 3307`

### Access Denied
- Verify user exists: `docker exec bentley-mysql mysql -uroot -proot -e "SELECT User, Host FROM mysql.user WHERE User = 'airbyte';"`
- Check grants: `SHOW GRANTS FOR 'airbyte'@'%';`

### Can't Connect from Airbyte Cloud
1. Ensure port 3307 is open in router/firewall
2. Verify public IP hasn't changed: `(Invoke-WebRequest -Uri "https://api.ipify.org").Content`
3. Check MySQL is bound to all interfaces: `docker exec bentley-mysql mysql -uroot -proot -e "SHOW VARIABLES LIKE 'bind_address';"`

---

## 📞 Support Resources

- [Airbyte MySQL Connector Docs](https://docs.airbyte.com/integrations/sources/mysql)
- [Airbyte Cloud IP Addresses](https://docs.airbyte.com/cloud/getting-started-with-airbyte-cloud)
- [MySQL User Management](https://dev.mysql.com/doc/refman/8.0/en/user-account-management.html)

---

**Last Updated**: November 22, 2025  
**Your Public IP**: 186.112.188.47  
**MySQL Port**: 3307  
**Status**: ✅ Ready for Airbyte Cloud Connection
