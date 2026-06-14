# Airbyte Cloud IP Whitelist Configuration

This directory contains configuration files to whitelist Airbyte Cloud IP addresses for MySQL database access.

## 📋 Whitelisted IP Addresses

### US Region
- `34.106.109.131`
- `34.106.196.165`
- `34.106.60.246`
- `34.106.229.69`
- `34.106.127.139`
- `34.106.218.58`
- `34.106.115.240`
- `34.106.225.141`

### EU Region
- `13.37.4.46`
- `13.37.142.60`
- `35.181.124.238`

### CIDR Range
- `34.33.7.0/29` (covers 34.33.7.0 - 34.33.7.7)

## 🚀 Quick Start

### Option 1: Automated Setup (Windows)

Run the PowerShell script as Administrator:

```powershell
# From project root
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_airbyte_firewall.ps1
```

This will:
- Create Windows Firewall rules for all Airbyte IPs
- Allow inbound connections on port 3307
- Display verification and next steps

### Option 2: Docker Compose (Recommended)

The MySQL configuration is already integrated into `docker-compose-airflow.yml`:

```bash
# Restart MySQL to apply new configuration
docker-compose -f docker-compose-airflow.yml restart mysql

# Verify MySQL is running with new config
docker exec bentley-mysql mysql -uroot -proot -e "SELECT User, Host FROM mysql.user WHERE User = 'airbyte';"
```

### Option 3: Manual MySQL Configuration

If you need to manually configure MySQL:

```bash
# Copy SQL script into running container
docker cp mysql_config/airbyte_ip_whitelist.sql bentley-mysql:/tmp/

# Execute the script
docker exec -it bentley-mysql mysql -uroot -proot mansa_bot < /tmp/airbyte_ip_whitelist.sql
```

## 📁 Files

### `my.cnf`
MySQL server configuration file that:
- Binds MySQL to `0.0.0.0` (all interfaces)
- Sets performance tuning parameters
- Configures character sets and logging

### `airbyte_ip_whitelist.sql`
SQL script that:
- Creates dedicated `airbyte` user
- Grants access from specific Airbyte Cloud IPs
- Configures database permissions for `mansa_bot`

### `ip_whitelist.conf`
Reference file containing:
- Complete list of Airbyte Cloud IPs
- Firewall rules for various platforms (UFW, iptables, Windows, AWS, Azure, GCP)
- Network security configuration examples

## 🔐 Security Considerations

### 1. Database Credentials

The default Airbyte user credentials are:
- **Username**: `airbyte`
- **Password**: `airbyte_secure_password_2025`

**⚠️ IMPORTANT**: Change this password before production use!

```sql
-- Change the Airbyte password
ALTER USER 'airbyte'@'%' IDENTIFIED BY 'your_strong_password_here';
FLUSH PRIVILEGES;
```

### 2. Network Security Layers

This configuration implements a **defense-in-depth** approach:

1. **Application Layer**: MySQL user permissions (least privilege)
2. **Network Layer**: Firewall rules (IP whitelisting)
3. **Transport Layer**: TLS/SSL encryption (optional, configure separately)

### 3. IP Address Updates

Airbyte Cloud may add or change IP addresses. Check the latest list at:
https://docs.airbyte.com/cloud/getting-started-with-airbyte-cloud

## 🔧 Troubleshooting

### Connection Refused

If Airbyte cannot connect:

1. **Verify MySQL is listening on public interface:**
   ```bash
   docker exec bentley-mysql netstat -tuln | grep 3306
   # Should show: 0.0.0.0:3306
   ```

2. **Check firewall rules (Windows):**
   ```powershell
   Get-NetFirewallRule | Where-Object { $_.DisplayName -like "Airbyte-MySQL-*" }
   ```

3. **Test from your machine:**
   ```bash
   mysql -h 127.0.0.1 -P 3307 -uairbyte -pairbyte_secure_password_2025 mansa_bot
   ```

### Access Denied

If you get "Access denied for user 'airbyte'@'<ip>'":

1. **Verify user exists:**
   ```sql
   SELECT User, Host FROM mysql.user WHERE User = 'airbyte';
   ```

2. **Check grants:**
   ```sql
   SHOW GRANTS FOR 'airbyte'@'%';
   ```

3. **Recreate user if needed:**
   ```sql
   DROP USER IF EXISTS 'airbyte'@'%';
   SOURCE /docker-entrypoint-initdb.d/02-airbyte-whitelist.sql;
   ```

### Public IP Address

To find your public IP address (needed for Airbyte Cloud connection):

```powershell
# Windows PowerShell
(Invoke-WebRequest -Uri "https://api.ipify.org").Content
```

Or visit: https://www.whatismyip.com/

## 🌐 Cloud Provider Setup

### AWS EC2

If running on AWS, update your Security Group:

```bash
# Get your security group ID
aws ec2 describe-instances --instance-ids i-xxxxx --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId'

# Add inbound rules for Airbyte IPs
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --ip-permissions \
    IpProtocol=tcp,FromPort=3307,ToPort=3307,IpRanges="[{CidrIp=34.106.109.131/32},{CidrIp=34.106.196.165/32}]"
```

### Azure VM

Update Network Security Group (NSG):

```bash
az network nsg rule create \
  --resource-group myResourceGroup \
  --nsg-name myNSG \
  --name AirbyteMySQLAccess \
  --priority 100 \
  --source-address-prefixes 34.106.109.131 34.106.196.165 \
  --destination-port-ranges 3307 \
  --protocol Tcp \
  --access Allow
```

### GCP Compute Engine

Create firewall rule:

```bash
gcloud compute firewall-rules create airbyte-mysql-access \
  --allow tcp:3307 \
  --source-ranges 34.106.109.131,34.106.196.165,34.106.60.246,34.106.229.69,34.106.127.139,34.106.218.58,34.106.115.240,34.106.225.141,13.37.4.46,13.37.142.60,35.181.124.238,34.33.7.0/29 \
  --description "Allow Airbyte Cloud to access MySQL"
```

## 📞 Airbyte Connection Settings

When configuring MySQL source in Airbyte Cloud, use:

| Setting | Value |
|---------|-------|
| Host | `<your-public-ip-or-domain>` |
| Port | `3307` |
| Database | `mansa_bot` |
| Username | `airbyte` |
| Password | `airbyte_secure_password_2025` |
| SSL Mode | `preferred` (or `required` if configured) |

## 🔄 Updating IP Whitelist

If Airbyte adds new IPs:

1. Update `airbyte_ip_whitelist.sql` with new IPs
2. Update `ip_whitelist.conf` reference file
3. Update `setup_airbyte_firewall.ps1` script
4. Restart MySQL container:
   ```bash
   docker-compose -f docker-compose-airflow.yml restart mysql
   ```
5. Re-run firewall script (if using Windows):
   ```powershell
   .\setup_airbyte_firewall.ps1
   ```

## 📚 Additional Resources

- [Airbyte Cloud Documentation](https://docs.airbyte.com/cloud/getting-started-with-airbyte-cloud)
- [MySQL User Account Management](https://dev.mysql.com/doc/refman/8.0/en/user-account-management.html)
- [Docker MySQL Configuration](https://hub.docker.com/_/mysql)
