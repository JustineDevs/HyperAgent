# Supabase Connection Fix - IPv6/IPv4 Compatibility

## Problem

If you're getting this error:
```
could not translate host name "db.xxx.supabase.co" to address: No such host is known
```

This is because **Supabase databases use IPv6 by default**, and your network may not support IPv6.

## Solution: Use Supavisor Connection Pooler

Supavisor is Supabase's connection pooler that supports **both IPv4 and IPv6**, making it compatible with all networks.

### Step 1: Get Supavisor Connection String

1. Go to https://app.supabase.com
2. Select your project
3. Navigate to **Settings** → **Database**
4. Scroll down to **Connection Pooling** section
5. You'll see two connection strings:
   - **Session mode** (port `5432`) - Use this for migrations
   - **Transaction mode** (port `6543`) - Use this for application connections

### Step 2: Update Your .env File

Replace your `DATABASE_URL` with the Supavisor connection string:

**For Migrations (Session mode - port 5432):**
```bash
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
```

**For Application (Transaction mode - port 6543):**
```bash
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

**Example:**
```bash
# Before (direct connection - IPv6 only)
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres

# After (Supavisor - IPv4 compatible)
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Step 3: Test Connection

```bash
# Test config loads
.\venv\Scripts\python.exe -c "from hyperagent.core.config import settings; print('Config OK')"

# Run migrations
.\venv\Scripts\alembic.exe upgrade head
```

## Alternative: Enable IPv4 Add-on

If you prefer direct connections:

1. Go to Supabase Dashboard
2. Navigate to **Add-ons** section
3. Enable **IPv4 add-on** for your project
4. This assigns an IPv4 address to your database
5. Use the new IPv4 connection string

**Note:** IPv4 add-on may have additional costs.

## Connection String Format

Supavisor connection strings follow this pattern:

```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:[PORT]/postgres
```

Where:
- `[PROJECT-REF]`: Your project reference (found in project settings)
- `[PASSWORD]`: Your database password
- `[REGION]`: AWS region (e.g., `us-east-1`, `eu-west-1`)
- `[PORT]`: `5432` for session mode, `6543` for transaction mode

## Benefits of Supavisor

1. **IPv4 Compatibility**: Works on networks without IPv6
2. **Connection Pooling**: Better performance and connection management
3. **No Code Changes**: Just update the connection string
4. **Free**: Included with all Supabase plans

## Troubleshooting

### Still Can't Connect?

1. **Check Project Status**: Ensure your Supabase project is active (not paused)
2. **Verify Password**: Double-check your database password
3. **Check Network Bans**: Go to Database → Settings → Network Bans and unban your IP if needed
4. **Test DNS**: Try `nslookup aws-0-[REGION].pooler.supabase.com` to verify DNS resolution
5. **Firewall**: Ensure your firewall allows outbound connections on ports 5432/6543

### Test Connection with Python

Create `test_connection.py`:

```python
import psycopg2
from hyperagent.core.config import settings

try:
    conn = psycopg2.connect(settings.database_url)
    print("[+] Connection successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    print(f"[*] PostgreSQL version: {cursor.fetchone()[0]}")
    conn.close()
except Exception as e:
    print(f"[-] Connection failed: {e}")
```

Run:
```bash
.\venv\Scripts\python.exe test_connection.py
```

## Next Steps

Once connected:
1. Run database migrations: `alembic upgrade head`
2. Verify schema: Check that all tables are created
3. Test pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector;`
4. Continue with HyperAgent setup

