# Quick Start Guide: Google Cloud SQL Configuration

## For New Deployments (Cloud SQL)

### 1. Set Environment Variables

Set the following environment variables in your deployment environment (Cloud Run, Kubernetes, etc.):

```bash
DB_HOST=34.40.117.250
DB_PORT=5432
DB_NAME=nexus_warehouse
DB_USER=your_cloud_sql_user
DB_PASSWORD=your_secure_password
DB_SSL_MODE=require
```

### 2. Validate Configuration (Optional)

Before deploying, validate your configuration locally:

```bash
# Set the environment variables
export DB_HOST=34.40.117.250
export DB_PORT=5432
export DB_NAME=nexus_warehouse
export DB_USER=test_user
export DB_PASSWORD=test_pass
export DB_SSL_MODE=require

# Run validation
python validate_db_config.py
```

### 3. Deploy Application

Deploy the application using your preferred method. The application will automatically use the DB_ environment variables.

### 4. Verify Health

Once deployed, check the health endpoint:

```bash
curl https://your-app-url/health
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "database": "connected",
    "api": "responsive",
    "routing": "active"
  }
}
```

## For Existing Deployments (Migration)

### Option 1: Add DB_ Variables (Recommended)

Add DB_ variables alongside existing QW_ variables:

```bash
# New Cloud SQL variables (take precedence)
DB_HOST=34.40.117.250
DB_PORT=5432
DB_NAME=nexus_warehouse
DB_USER=cloud_user
DB_PASSWORD=cloud_password
DB_SSL_MODE=require

# Existing QW_ variables (kept as fallback)
QW_PSQL_NODE_HOSTNAME=localhost
QW_PSQL_NODE_TCP_PORT=5432
# ... other QW_ variables
```

Benefits:
- Zero-downtime migration
- Easy rollback (just remove DB_ variables)
- DB_ variables take precedence when present

### Option 2: Keep Existing QW_ Variables

No changes needed! The application continues to work with QW_ variables.

## Testing the Connection

### Method 1: Using the Validation Script

```bash
python validate_db_config.py
```

Select 'y' when prompted to test the database connection.

### Method 2: Using Python

```python
from warehouse_nexus.cerebrum.psql_conductor import psql_conductor

# Test connection
with psql_conductor.connect() as conn:
    result = conn.execute("SELECT version();")
    print(result.fetchone()[0])
```

### Method 3: Using the Health Endpoint

```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Issue: "Connection refused"

**Possible causes:**
- Database server is not running
- Incorrect host/port configuration
- Firewall blocking the connection

**Solution:**
1. Verify DB_HOST is correct (34.40.117.250 for Cloud SQL)
2. Check port is 5432
3. Verify firewall allows connections from your IP
4. In Cloud SQL console, add your IP to authorized networks

### Issue: "Authentication failed"

**Possible causes:**
- Incorrect username or password
- User doesn't have access to the database

**Solution:**
1. Verify DB_USER and DB_PASSWORD are correct
2. Check user has been created in Cloud SQL
3. Verify user has privileges on the database:
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE nexus_warehouse TO your_user;
   ```

### Issue: "SSL connection required"

**Possible causes:**
- Cloud SQL requires SSL but DB_SSL_MODE is not set

**Solution:**
Set `DB_SSL_MODE=require` in your environment variables.

### Issue: "Database does not exist"

**Solution:**
Create the database in Cloud SQL:
```sql
CREATE DATABASE nexus_warehouse;
```

Then run migrations:
```bash
alembic upgrade head
```

## Running Migrations

After connecting to Cloud SQL, run database migrations:

```bash
# Check current version
alembic current

# Upgrade to latest version
alembic upgrade head

# Verify tables were created
# Connect to database and check:
\dt  # in psql
```

## Security Best Practices

1. **Use SSL**: Always set `DB_SSL_MODE=require` for Cloud SQL connections
2. **Strong Passwords**: Use strong, randomly generated passwords
3. **Secret Management**: Store credentials in a secret manager (Google Secret Manager, AWS Secrets Manager, etc.)
4. **IP Allowlisting**: Restrict database access to known IP addresses
5. **Least Privilege**: Grant only necessary database privileges to application user
6. **Regular Rotation**: Rotate database passwords regularly

## Cloud SQL Instance Details

Based on the issue, your Cloud SQL instance has:
- **Connection Name**: `cogent-quarter-486519:13:europe-west3:lms-backend-db`
- **Public IP**: `34.40.117.250`
- **Port**: `5432`
- **Region**: `europe-west3`

## Next Steps

1. ✅ Set DB_ environment variables
2. ✅ Validate configuration with `validate_db_config.py`
3. ✅ Deploy application
4. ✅ Run migrations: `alembic upgrade head`
5. ✅ Verify health endpoint
6. ✅ Test API endpoints

## Support

For issues or questions:
1. Check CLOUD_SQL_IMPLEMENTATION.md for detailed documentation
2. Run `python validate_db_config.py` to diagnose configuration issues
3. Review application logs for connection errors
4. Check Google Cloud SQL logs in Cloud Console

## Example: Complete Setup Script

```bash
#!/bin/bash
# setup_cloud_sql.sh

# Set environment variables
export DB_HOST=34.40.117.250
export DB_PORT=5432
export DB_NAME=nexus_warehouse
export DB_USER=nexus_admin
export DB_PASSWORD=your_secure_password_here
export DB_SSL_MODE=require

# Validate configuration
echo "Validating configuration..."
python validate_db_config.py

# Run migrations
echo "Running migrations..."
alembic upgrade head

# Start application
echo "Starting application..."
python launch_nexus.py
```

Make the script executable:
```bash
chmod +x setup_cloud_sql.sh
./setup_cloud_sql.sh
```
