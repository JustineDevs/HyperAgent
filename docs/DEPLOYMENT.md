# Production Deployment Guide

**Document Type**: How-To Guide (Goal-Oriented)  
**Category**: Deployment  
**Audience**: DevOps, System Administrators  
**Location**: `docs/DEPLOYMENT.md`

This guide covers deploying HyperAgent to production environments.

## Deployment Options

### 1. Docker Compose (Recommended for Small-Medium Scale)

Best for: Single server deployments, development-to-production pipelines

#### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Minimum 4GB RAM, 2 CPU cores

#### Steps

1. **Prepare Environment**

```bash
# Clone repository
git clone https://github.com/JustineDevs/HyperAgent.git
cd HyperAgent

# Create production environment file
cp env.example .env.production

# Edit .env.production with production values
# - Strong database passwords
# - Secure Redis password
# - Production API keys
# - JWT_SECRET_KEY (generate strong random key)
```

2. **Configure Production Settings**

```env
# .env.production
NODE_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=<generate-strong-random-key>
ENABLE_AUTHENTICATION=true
ENABLE_RATE_LIMITING=true

# Database (use strong passwords)
DATABASE_URL=postgresql://user:strong_password@postgres:5432/hyperagent_db

# Redis (use password)
REDIS_URL=redis://:strong_password@redis:6379/0
REDIS_PASSWORD=strong_password

# API Configuration
API_WORKERS=4
CORS_ORIGINS=https://yourdomain.com
```

3. **Deploy**

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

4. **Initialize Database**

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec hyperagent alembic upgrade head
```

5. **Verify Deployment**

```bash
# Health check
curl http://localhost:8000/api/v1/health/detailed

# Expected: All services healthy
```

### 2. Kubernetes Deployment

Best for: Large-scale deployments, high availability

#### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Helm 3.0+ (optional)

#### Deployment Steps

1. **Create ConfigMap**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hyperagent-config
data:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/db"
  REDIS_URL: "redis://redis:6379/0"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
```

2. **Create Secret**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: hyperagent-secrets
type: Opaque
stringData:
  GEMINI_API_KEY: "your-api-key"
  JWT_SECRET_KEY: "your-jwt-secret"
  DATABASE_PASSWORD: "your-db-password"
  REDIS_PASSWORD: "your-redis-password"
```

3. **Deploy Application**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hyperagent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hyperagent
  template:
    metadata:
      labels:
        app: hyperagent
    spec:
      containers:
      - name: hyperagent
        image: hyperagent:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: hyperagent-config
        - secretRef:
            name: hyperagent-secrets
        livenessProbe:
          httpGet:
            path: /api/v1/health/liveness
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/health/readiness
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
```

### 3. Cloud Platform Deployment

#### AWS (ECS/EKS)

- Use ECS with Fargate for serverless containers
- Use EKS for Kubernetes orchestration
- Use RDS for PostgreSQL (with pgvector extension)
- Use ElastiCache for Redis

#### Google Cloud Platform

- Use Cloud Run for serverless containers
- Use GKE for Kubernetes
- Use Cloud SQL for PostgreSQL
- Use Memorystore for Redis

#### Azure

- Use Container Instances or AKS
- Use Azure Database for PostgreSQL
- Use Azure Cache for Redis

## Database Setup

### PostgreSQL with pgvector

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE hyperagent_db;

-- Connect to database
\c hyperagent_db

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### Using Supabase (Cloud Alternative)

1. Create project at [supabase.com](https://supabase.com)
2. Enable pgvector extension in database settings
3. Get connection string from project settings
4. Update `DATABASE_URL` in `.env`

## Redis Setup

### Local Redis

```bash
# Install Redis
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

### Redis Cloud

1. Create account at [redis.com](https://redis.com)
2. Create database
3. Get connection URL
4. Update `REDIS_URL` in `.env`

## Security Best Practices

### 1. Environment Variables

- Never commit `.env` files
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Rotate API keys regularly
- Use strong passwords for database and Redis

### 2. Network Security

- Use HTTPS in production (reverse proxy with nginx/traefik)
- Restrict CORS origins to your domain
- Enable rate limiting
- Use firewall rules to restrict access

### 3. Authentication

```env
# Enable authentication
ENABLE_AUTHENTICATION=true
JWT_SECRET_KEY=<strong-random-key>
JWT_EXPIRE_MINUTES=1440
```

### 4. API Keys

- Store API keys securely
- Use environment variables or secrets management
- Rotate keys periodically
- Monitor API usage

## Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost:8000/api/v1/health/

# Detailed health (includes service checks)
curl http://localhost:8000/api/v1/health/detailed

# Kubernetes probes
curl http://localhost:8000/api/v1/health/liveness
curl http://localhost:8000/api/v1/health/readiness
```

### Metrics

If metrics are enabled:

```bash
# Prometheus metrics
curl http://localhost:9090/metrics
```

### Logging

- Logs are written to `logs/hyperagent.log`
- Use log aggregation (ELK, Loki, CloudWatch)
- Set `LOG_FORMAT=json` for structured logging

## Scaling

### Horizontal Scaling

- Run multiple API instances behind load balancer
- Use shared database and Redis
- Configure session affinity if needed

### Vertical Scaling

- Increase `API_WORKERS` for more concurrent requests
- Allocate more CPU/memory to containers
- Optimize database connection pooling

## Backup and Recovery

### Database Backups

```bash
# Backup PostgreSQL
pg_dump -U user hyperagent_db > backup.sql

# Restore
psql -U user hyperagent_db < backup.sql
```

### Automated Backups

- Schedule regular database backups
- Store backups in secure location
- Test restore procedures

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check database is running
   - Verify connection string
   - Check firewall rules

2. **Redis Connection Failed**
   - Check Redis is running
   - Verify connection URL
   - Check authentication

3. **High Memory Usage**
   - Reduce `API_WORKERS`
   - Optimize database queries
   - Check for memory leaks

For more troubleshooting, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## Additional Resources

- [Configuration Guide](./CONFIGURATION.md) - All configuration options
- [API Reference](./API_REFERENCE.md) - API documentation
- [Networks Guide](./NETWORKS.md) - Network configuration

---

**Need help?** Open an issue on [GitHub](https://github.com/JustineDevs/HyperAgent/issues)

