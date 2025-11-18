# Docker & Containerization Guide

## Overview

HyperAgent is fully containerized using Docker and Docker Compose for consistent deployments across development, staging, and production environments.

## Quick Start

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f hyperagent

# Stop services
docker-compose down
```

### Production

```bash
# Build image
docker build -t hyperagent:latest .

# Start with production compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Dockerfile

### Multi-Stage Build

The Dockerfile uses a multi-stage build to minimize image size:

1. **Builder Stage**: Installs build dependencies and Python packages
2. **Runtime Stage**: Creates minimal runtime image with only necessary files

### Security Features

- **Non-root user**: Application runs as `hyperagent` user (not root)
- **Minimal base image**: Uses `python:3.10-slim` for smaller footprint
- **Health checks**: Built-in health monitoring
- **Read-only mounts**: Source code mounted read-only in development

### Image Optimization

- Layer caching for faster rebuilds
- `--no-install-recommends` to reduce package size
- Removed build dependencies in runtime stage
- `.dockerignore` to exclude unnecessary files

## Docker Compose

### Development Stack (`docker-compose.yml`)

**Services:**
- `hyperagent`: Main application
- `postgres`: PostgreSQL database with pgvector
- `redis`: Redis cache and event bus

**Features:**
- Hot reload with volume mounts
- Environment variable management
- Health checks for all services
- Automatic service dependencies

### Production Stack (`docker-compose.prod.yml`)

**Features:**
- Resource limits and reservations
- No source code mounts (uses image)
- Production environment variables
- Enhanced security settings

## Environment Variables

### Required Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# LLM
GEMINI_API_KEY=your_key_here

# Redis
REDIS_URL=redis://host:6379/0
```

### Optional Variables

See `.env.example` for complete list of configurable variables.

## Building Images

### Standard Build

```bash
docker build -t hyperagent:latest .
```

### Using Build Script

```bash
chmod +x scripts/docker_build.sh
./scripts/docker_build.sh
```

### Build Arguments

```bash
docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t hyperagent:latest .
```

## Running Containers

### Development

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d hyperagent

# View logs
docker-compose logs -f hyperagent

# Execute commands
docker-compose exec hyperagent alembic upgrade head
```

### Production

```bash
# Run container
docker run -d \
  --name hyperagent \
  --env-file .env.production \
  -p 8000:8000 \
  hyperagent:latest
```

## Health Checks

### Application Health

```bash
# Check health endpoint
curl http://localhost:8000/api/v1/health/basic

# Check detailed health
curl http://localhost:8000/api/v1/health/detailed
```

### Container Health

```bash
# View container status
docker-compose ps

# Check health status
docker inspect hyperagent_app | grep Health -A 10
```

## Database Migrations

### Run Migrations

```bash
# Using Docker Compose
docker-compose exec hyperagent alembic upgrade head

# Using Makefile
make migrate
```

### Create Migration

```bash
docker-compose exec hyperagent alembic revision --autogenerate -m "description"
```

## Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f hyperagent

# Last 100 lines
docker-compose logs --tail=100 hyperagent
```

### Log Locations

- Container: `/app/logs/`
- Host: `./logs/` (mounted volume)

## Volumes

### Development Volumes

- `./hyperagent:/app/hyperagent:ro` - Source code (read-only)
- `./logs:/app/logs` - Application logs
- `./alembic:/app/alembic:ro` - Migration files

### Data Volumes

- `postgres_data` - PostgreSQL data persistence
- `redis_data` - Redis data persistence

## Networking

### Default Network

All services are connected to `hyperagent_network` bridge network.

### Service Discovery

Services can communicate using service names:
- `postgres:5432` - Database
- `redis:6379` - Redis cache

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs hyperagent

# Check health
docker-compose ps

# Restart services
docker-compose restart
```

### Database Connection Issues

```bash
# Verify database is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U hyperagent_user -d hyperagent_db
```

### Redis Connection Issues

```bash
# Verify Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
```

### Permission Issues

```bash
# Fix log directory permissions
sudo chown -R $USER:$USER logs/
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Update `.env.production` with production values
- [ ] Set strong passwords for database and Redis
- [ ] Configure JWT secret key
- [ ] Set up SSL/TLS certificates
- [ ] Configure resource limits
- [ ] Set up monitoring and logging

### Deployment Steps

1. **Build production image:**
   ```bash
   docker build -t hyperagent:latest .
   ```

2. **Tag for registry:**
   ```bash
   docker tag hyperagent:latest registry.example.com/hyperagent:latest
   ```

3. **Push to registry:**
   ```bash
   docker push registry.example.com/hyperagent:latest
   ```

4. **Deploy with compose:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### Resource Limits

Production compose file includes resource limits:
- **HyperAgent**: 2 CPU, 2GB RAM
- **PostgreSQL**: 1 CPU, 1GB RAM
- **Redis**: 0.5 CPU, 512MB RAM

## Makefile Commands

```bash
make build      # Build Docker image
make up         # Start development stack
make up-prod    # Start production stack
make down       # Stop all services
make logs       # View logs
make restart    # Restart services
make clean      # Remove containers and volumes
make test       # Run tests in container
make shell      # Open shell in container
make migrate    # Run database migrations
make health     # Check service health
```

## Best Practices

1. **Use .env files**: Never commit secrets to version control
2. **Health checks**: Always configure health checks for services
3. **Resource limits**: Set appropriate limits in production
4. **Log rotation**: Configure log rotation to prevent disk fill
5. **Backup volumes**: Regularly backup data volumes
6. **Update images**: Keep base images updated for security
7. **Non-root user**: Always run containers as non-root user
8. **Read-only mounts**: Use read-only mounts where possible

## CI/CD Integration

Docker images are automatically built and pushed in CI/CD pipeline:

- **Build**: On every commit to main/develop
- **Tag**: With branch name, commit SHA, and `latest` (main only)
- **Push**: To GitHub Container Registry (ghcr.io)
- **Test**: Docker Compose integration tests run automatically

## Image Size Optimization

Current optimizations:
- Multi-stage build reduces final image size
- Minimal base image (python:3.10-slim)
- Removed build dependencies in runtime
- `.dockerignore` excludes unnecessary files

**Target**: < 500MB final image size

