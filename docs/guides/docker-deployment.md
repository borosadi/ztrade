# Docker Deployment Guide

Complete guide to deploying Ztrade using Docker and Docker Compose.

---

## Overview

Ztrade uses a multi-container architecture with separate services for trading, data collection, monitoring, and storage. This guide covers local development and production deployment using Docker.

---

## Prerequisites

### Required Software

```bash
# Docker (20.10+)
docker --version

# Docker Compose (2.0+)
docker-compose --version

# Git
git --version
```

### Installation

**macOS:**
```bash
# Install Docker Desktop
brew install --cask docker
```

**Linux:**
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

## Quick Start (Development)

###1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/your-org/ztrade.git
cd ztrade

# Copy environment file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Build and Start

```bash
# Build images
./docker-control.sh dev build

# Start all services
./docker-control.sh dev up

# View logs
./docker-control.sh dev logs
```

### 3. Access Services

- **Dashboard**: http://localhost:8501
- **Flower**: http://localhost:5555
- **PostgreSQL**: localhost:5432

### 4. Stop Services

```bash
# Stop all services
./docker-control.sh dev down
```

---

## Service Architecture

```
┌─────────────────────────────────────────────────┐
│              Ztrade Docker Services              │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Trading  │  │Dashboard │  │  Flower  │     │
│  │  :---    │  │  :8501   │  │  :5555   │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │             │              │            │
│  ┌────▼─────┐  ┌───▼──────┐  ┌───▼──────┐    │
│  │  Worker  │  │  Beat    │  │  Redis   │    │
│  │  (x4)    │  │  (x1)    │  │  :6379   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │              │            │
│       └─────────────▼──────────────┘            │
│                     │                           │
│              ┌──────▼──────┐                   │
│              │ PostgreSQL  │                   │
│              │   :5432     │                   │
│              └─────────────┘                   │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Service Details

| Service | Container | Purpose | Ports |
|---------|-----------|---------|-------|
| **trading** | ztrade-trading | CLI operations, manual trading | - |
| **worker** | ztrade-worker | Celery workers for autonomous trading | - |
| **beat** | ztrade-beat | Celery scheduler for periodic tasks | - |
| **dashboard** | ztrade-dashboard | Streamlit web UI | 8501 |
| **flower** | ztrade-flower | Celery monitoring UI | 5555 |
| **postgres** | ztrade-postgres | Primary database | 5432 |
| **redis** | ztrade-redis | Message broker & cache | 6379 |

---

## Environment Configuration

### Required Variables (.env)

```bash
# Alpaca API (Required)
ALPACA_API_KEY=pk_xxx
ALPACA_SECRET_KEY=sk_xxx
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Database (Auto-configured in Docker)
POSTGRES_DB=ztrade
POSTGRES_USER=ztrade
POSTGRES_PASSWORD=change_this_password

# Redis (Auto-configured in Docker)
REDIS_URL=redis://redis:6379/0

# Optional APIs
ANTHROPIC_API_KEY=sk-xxx  # For automated trading
REDDIT_CLIENT_ID=xxx      # For Reddit sentiment
REDDIT_CLIENT_SECRET=xxx
REDDIT_USER_AGENT="Ztrade:v1.0"
```

### Development vs Production

**Development (.env.dev):**
- Hot-reload enabled (volume mounts)
- Debug logging
- Exposed database ports
- No resource limits

**Production (.env.prod):**
- Optimized images (no volume mounts)
- Info-level logging
- No exposed database ports
- Resource limits enforced
- Authentication required

---

## Common Operations

### View Logs

```bash
# All services
./docker-control.sh dev logs

# Specific service
./docker-control.sh dev logs worker

# Follow logs
docker-compose -f docker-compose.dev.yml logs -f worker

# Last 100 lines
docker-compose -f docker-compose.dev.yml logs --tail=100 trading
```

### Execute Commands

```bash
# Open shell in trading container
./docker-control.sh dev shell

# Run specific command
docker-compose -f docker-compose.dev.yml exec trading uv run ztrade agent list

# Run as one-off
docker-compose -f docker-compose.dev.yml run --rm trading uv run ztrade agent status agent_spy
```

### Database Operations

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.dev.yml exec postgres psql -U ztrade -d ztrade

# Backup database
docker-compose -f docker-compose.dev.yml exec postgres pg_dump -U ztrade ztrade > backup.sql

# Restore database
cat backup.sql | docker-compose -f docker-compose.dev.yml exec -T postgres psql -U ztrade -d ztrade

# View tables
docker-compose -f docker-compose.dev.yml exec postgres psql -U ztrade -d ztrade -c "\dt"
```

### Restart Services

```bash
# Restart all
./docker-control.sh dev restart

# Restart specific service
docker-compose -f docker-compose.dev.yml restart worker

# Rebuild and restart
docker-compose -f docker-compose.dev.yml up -d --build worker
```

---

## Production Deployment

### 1. Prepare Environment

```bash
# Copy production env file
cp .env.example .env.prod

# Edit with production values
nano .env.prod

# IMPORTANT: Change all passwords!
# - POSTGRES_PASSWORD
# - FLOWER_PASSWORD
```

### 2. Build Production Images

```bash
# Build optimized images
./docker-control.sh prod build

# Or use Docker directly
docker build --target production -t ztrade:latest .
```

### 3. Deploy

```bash
# Start production services
./docker-control.sh prod up

# Check status
./docker-control.sh prod ps

# View logs
./docker-control.sh prod logs
```

### 4. Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Check health
docker-compose -f docker-compose.prod.yml exec trading python -c "import sys; sys.exit(0)"

# Test database connection
docker-compose -f docker-compose.prod.yml exec trading uv run python -c "from cli.utils.broker import get_broker; print(get_broker().get_account_info())"
```

---

## Monitoring

### Health Checks

```bash
# Check container health
docker ps --filter "name=ztrade" --format "table {{.Names}}\t{{.Status}}"

# Inspect health check
docker inspect --format='{{json .State.Health}}' ztrade-worker | jq
```

### Resource Usage

```bash
# Container stats
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Specific container
docker stats ztrade-worker --no-stream
```

### Logs

```bash
# Export logs
docker-compose -f docker-compose.prod.yml logs --since 24h > logs-$(date +%Y%m%d).txt

# Watch specific service
docker-compose -f docker-compose.prod.yml logs -f --tail=50 worker
```

---

## Troubleshooting

### Container Won't Start

```bash
# View container logs
docker logs ztrade-worker

# Check events
docker events --filter 'container=ztrade-worker'

# Inspect container
docker inspect ztrade-worker

# Common issues:
# - Missing environment variables
# - Database not ready (check depends_on)
# - Volume mount issues
# - Port conflicts
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs ztrade-postgres

# Test connection
docker-compose -f docker-compose.dev.yml exec trading \
  psql postgresql://ztrade:password@postgres:5432/ztrade

# Reset database
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d postgres
```

### Worker Not Processing Tasks

```bash
# Check Redis
docker logs ztrade-redis
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping

# Check Celery worker
docker logs ztrade-worker

# Check queue
docker-compose -f docker-compose.dev.yml exec worker uv run celery -A celery_app inspect active

# Restart worker
docker-compose -f docker-compose.dev.yml restart worker
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Increase worker concurrency
# Edit docker-compose.prod.yml:
# environment:
#   CELERY_WORKER_CONCURRENCY: 8

# Add more worker replicas
docker-compose -f docker-compose.prod.yml up -d --scale worker=3
```

---

## Data Management

### Volumes

```bash
# List volumes
docker volume ls | grep ztrade

# Inspect volume
docker volume inspect ztrade-postgres-data

# Backup volume
docker run --rm -v ztrade-postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz /data

# Restore volume
docker run --rm -v ztrade-postgres-data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres-backup.tar.gz -C /
```

### Backups

```bash
# Automated backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U ztrade ztrade | gzip > backup_${DATE}.sql.gz
echo "Backup created: backup_${DATE}.sql.gz"
EOF
chmod +x backup.sh

# Schedule daily backups (cron)
0 2 * * * /path/to/ztrade/backup.sh
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=5

# Check scaled containers
docker ps | grep worker
```

### Resource Limits

Edit `docker-compose.prod.yml`:

```yaml
services:
  worker:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '2.0'
          memory: 2G
```

---

## Security

### Best Practices

1. **Never commit .env files**
   - Add to .gitignore
   - Use secrets management (Vault, AWS Secrets Manager)

2. **Use strong passwords**
   ```bash
   # Generate secure password
   openssl rand -base64 32
   ```

3. **Run as non-root**
   - Already configured in Dockerfile
   - Verify: `docker-compose exec trading whoami`

4. **Network isolation**
   - Services communicate via internal network
   - Only dashboard and flower exposed

5. **Regular updates**
   ```bash
   # Update base images
   docker-compose pull
   docker-compose up -d
   ```

---

## Cleanup

### Remove Containers

```bash
# Stop and remove containers
./docker-control.sh dev down

# Remove volumes (WARNING: deletes data)
./docker-control.sh dev clean
```

### Remove Images

```bash
# Remove Ztrade images
docker rmi $(docker images -q ztrade)

# Remove unused images
docker image prune -a
```

### Full Cleanup

```bash
# Remove everything (containers, volumes, networks)
docker-compose -f docker-compose.dev.yml down -v --rmi all

# System-wide cleanup
docker system prune -a --volumes
```

---

## Migration from Local

### Export Current State

```bash
# Backup agent states
cp -r agents/ agents_backup/

# Backup configurations
cp -r config/ config_backup/

# Export environment
cp .env .env.local_backup
```

### Import to Docker

```bash
# Start Docker environment
./docker-control.sh dev up

# Import data (if needed)
docker-compose -f docker-compose.dev.yml cp agents_backup/ trading:/app/agents/
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t ztrade:${{ github.sha }} .

      - name: Push to registry
        run: |
          docker tag ztrade:${{ github.sha }} registry/ztrade:latest
          docker push registry/ztrade:latest

      - name: Deploy
        run: |
          # Deploy to production
          ssh user@server "cd /app && docker-compose pull && docker-compose up -d"
```

---

## Next Steps

1. **Test Development Environment**
   - Run `./docker-control.sh dev up`
   - Access dashboard at http://localhost:8501
   - Verify all services are healthy

2. **Configure Production**
   - Create `.env.prod` with production credentials
   - Test production build locally
   - Deploy to production server

3. **Set Up Monitoring**
   - Configure log aggregation
   - Set up health check alerts
   - Monitor resource usage

4. **Kubernetes (Optional)**
   - See [k8s/README.md](../../k8s/README.md) for Kubernetes deployment

---

## Support

For issues or questions:
1. Check logs: `./docker-control.sh dev logs`
2. Review troubleshooting section above
3. File issue at: https://github.com/your-org/ztrade/issues

---

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [ADR-006: Containerization Strategy](../adr/ADR-006-containerization-strategy.md)
