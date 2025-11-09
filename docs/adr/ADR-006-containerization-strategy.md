# ADR-006: Containerization Strategy with Docker and Kubernetes

**Status:** Accepted
**Date:** 2025-11-09
**Deciders:** Development Team
**Context:** Need portable, scalable deployment supporting modular architecture

---

## Context and Problem Statement

The Ztrade trading system needs to:
1. Be portable across development, staging, and production environments
2. Support independent service scaling (trading, data collection, backtesting)
3. Enable easy deployment and rollback
4. Prepare for potential Kubernetes orchestration
5. Isolate dependencies and configurations
6. Support hot-reload during development

Traditional local deployment has limitations:
- Environment-specific configurations
- Dependency conflicts
- Difficult to scale individual services
- Complex setup for new developers
- No infrastructure-as-code approach

---

## Decision Drivers

* **Portability:** Run anywhere (local, cloud, different OS)
* **Modularity:** Independent services with clear boundaries
* **Scalability:** Ability to scale services independently
* **Developer Experience:** Easy setup, hot-reload support
* **Production Readiness:** Path to Kubernetes deployment
* **Resource Efficiency:** Optimize for cost in production

---

## Considered Options

### Option 1: Single Monolithic Container
**Pros:**
- Simplest to build and deploy
- All components in one place
- Lower orchestration overhead

**Cons:**
- Can't scale services independently
- Restart entire system for any change
- Large image size
- Poor resource utilization
- Not Kubernetes-friendly

### Option 2: Multi-Container with Docker Compose
**Pros:**
- Service isolation and independence
- Individual service scaling
- Better resource utilization
- Easy local development
- Natural path to Kubernetes

**Cons:**
- More complex orchestration
- More configuration files
- Network management needed

### Option 3: Kubernetes-First Approach
**Pros:**
- Production-grade from start
- Built-in scaling and resilience
- Service mesh capabilities

**Cons:**
- Overkill for local development
- Steep learning curve
- Complex for solo developer
- Higher resource requirements

---

## Decision Outcome

**Chosen Option: Multi-Container with Docker Compose + Kubernetes Manifests**

We will implement a multi-container architecture using Docker Compose for local/development and provide Kubernetes manifests for future production deployment.

### Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Ztrade System                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Trading    │  │  Dashboard   │  │   Worker     │     │
│  │  Container   │  │  Container   │  │  Container   │     │
│  │              │  │              │  │              │     │
│  │ • CLI        │  │ • Streamlit  │  │ • Celery     │     │
│  │ • Agents     │  │ • Real-time  │  │ • Beat       │     │
│  │ • Risk Mgmt  │  │ • Monitoring │  │ • Tasks      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │             │
│  ┌──────▼──────────────────▼──────────────────▼───────┐   │
│  │           Shared Network (ztrade-network)           │   │
│  └──────┬──────────────────┬──────────────────┬────────┘   │
│         │                  │                  │             │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐    │
│  │   Redis      │  │  PostgreSQL  │  │   Flower     │    │
│  │  Container   │  │  Container   │  │  Container   │    │
│  │              │  │              │  │              │    │
│  │ • Message    │  │ • Data       │  │ • Monitor    │    │
│  │   Broker     │  │   Storage    │  │   UI         │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Service Breakdown

#### 1. **Trading Service** (`ztrade-trading`)
- Main application container
- CLI commands
- Agent configurations
- Risk management
- Manual trading operations

#### 2. **Worker Service** (`ztrade-worker`)
- Celery worker processes
- Celery beat scheduler
- Autonomous trading loops
- Background tasks

#### 3. **Dashboard Service** (`ztrade-dashboard`)
- Streamlit web application
- Real-time monitoring
- Port 8501 exposed

#### 4. **Flower Service** (`ztrade-flower`)
- Celery monitoring UI
- Port 5555 exposed

#### 5. **Redis Service** (`redis`)
- Message broker for Celery
- Task queue storage
- Official Redis image

#### 6. **PostgreSQL Service** (`postgres`)
- Primary data storage
- Market data archive
- Sentiment data storage
- Backtest results
- Official PostgreSQL image

---

## Implementation Strategy

### Phase 1: Dockerization (Week 1)
1. Create base Python image
2. Multi-stage builds for optimization
3. Docker Compose for development
4. Volume mounts for hot-reload
5. Environment variable management

### Phase 2: Service Separation (Week 1-2)
1. Split monolithic app into services
2. Database connection pooling
3. Service-to-service communication
4. Health checks and dependencies

### Phase 3: Kubernetes Preparation (Week 2-3)
1. Create Kubernetes manifests
2. StatefulSets for stateful services
3. ConfigMaps and Secrets
4. Ingress configuration
5. Helm charts (optional)

### Phase 4: Production Hardening (Week 3-4)
1. Resource limits and requests
2. Liveness and readiness probes
3. Horizontal Pod Autoscaling (HPA)
4. Persistent volume claims
5. Monitoring and logging

---

## Docker Compose Structure

### Development (`docker-compose.dev.yml`)
```yaml
services:
  trading:
    build: .
    volumes:
      - .:/app  # Hot-reload
    env_file: .env

  worker:
    build: .
    command: celery worker
    volumes:
      - .:/app

  dashboard:
    build: .
    command: streamlit run dashboard.py
    ports:
      - "8501:8501"

  redis:
    image: redis:7-alpine

  postgres:
    image: postgres:16-alpine
    volumes:
      - pg-data:/var/lib/postgresql/data
```

### Production (`docker-compose.prod.yml`)
```yaml
services:
  trading:
    image: ztrade:latest
    # No volume mounts
    # Optimized for production

  # Similar for other services with:
  # - Resource limits
  # - Health checks
  # - Restart policies
  # - Logging configuration
```

---

## Kubernetes Architecture

### Deployments
- `trading-deployment`: Main application (1 replica)
- `worker-deployment`: Celery workers (3 replicas, HPA-enabled)
- `dashboard-deployment`: Streamlit UI (2 replicas)
- `flower-deployment`: Monitoring UI (1 replica)

### StatefulSets
- `redis-statefulset`: Message broker with persistence
- `postgres-statefulset`: Database with persistent storage

### Services
- `trading-service`: ClusterIP
- `dashboard-service`: LoadBalancer (external access)
- `flower-service`: LoadBalancer (external access)
- `redis-service`: ClusterIP
- `postgres-service`: ClusterIP

### ConfigMaps & Secrets
- `ztrade-config`: Non-sensitive configuration
- `ztrade-secrets`: API keys, credentials
- `postgres-secrets`: Database credentials

### Persistent Volumes
- `postgres-pvc`: 10Gi for database
- `redis-pvc`: 1Gi for Redis persistence

---

## Benefits

### Immediate Benefits
1. **Portability:** Run on any Docker host
2. **Isolation:** No dependency conflicts
3. **Easy Setup:** `docker-compose up` vs manual setup
4. **Consistency:** Same environment everywhere
5. **Version Control:** Infrastructure as code

### Future Benefits
1. **Scalability:** Easy Kubernetes migration
2. **High Availability:** Multi-replica deployments
3. **Auto-Scaling:** HPA for worker scaling
4. **Service Mesh:** Advanced networking (Istio, Linkerd)
5. **Cloud-Native:** Deploy to any cloud provider

---

## Consequences

### Positive
* Clean separation of services
* Independent scaling and deployment
* Better resource utilization
* Easier testing and development
* Production-ready architecture
* Clear migration path to Kubernetes

### Negative
* Additional orchestration complexity
* Learning curve for Docker/Kubernetes
* More configuration files to manage
* Network overhead between containers
* Need for container registry (production)

### Neutral
* PostgreSQL instead of SQLite (better for containers)
* Environment variables for configuration
* Volume management for data persistence

---

## Compliance

* All services use official base images when possible
* Security: Run as non-root user
* Secrets: Never commit credentials to images
* Logging: Structured JSON logs to stdout
* Monitoring: Health checks on all services
* Resource Limits: Prevent resource exhaustion

---

## Implementation Notes

### Development Workflow
1. `docker-compose -f docker-compose.dev.yml up`
2. Code changes auto-reload (volume mounts)
3. Access services: dashboard (8501), flower (5555)
4. Logs: `docker-compose logs -f [service]`

### Production Deployment
1. Build optimized images: `docker build -t ztrade:latest .`
2. Push to registry: `docker push your-registry/ztrade:latest`
3. Deploy to Kubernetes: `kubectl apply -f k8s/`
4. Monitor: Prometheus + Grafana

### Migration from Local
1. Export current state and configs
2. Import to containerized PostgreSQL
3. Update connection strings
4. Test in development mode
5. Deploy to production

---

## Related Decisions

* ADR-001: Asset-based architecture (supports service separation)
* ADR-002: Multi-source sentiment (each source can be containerized)
* ADR-004: Continuous trading loops (natural fit for worker containers)

---

## References

* [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
* [Kubernetes Documentation](https://kubernetes.io/docs/)
* [12-Factor App Methodology](https://12factor.net/)
* [Celery with Docker](https://docs.celeryq.dev/en/stable/userguide/configuration.html#new-lowercase-settings)
