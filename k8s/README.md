# Kubernetes Deployment for Ztrade

This directory contains Kubernetes manifests for deploying Ztrade to a Kubernetes cluster.

---

## Directory Structure

```
k8s/
├── base/                    # Base Kubernetes resources
│   ├── namespace.yaml       # Namespace definition
│   ├── configmap.yaml       # Configuration
│   ├── secrets.yaml         # Secrets (not in git)
│   ├── postgres.yaml        # PostgreSQL StatefulSet
│   ├── redis.yaml           # Redis StatefulSet
│   ├── trading.yaml         # Trading Deployment
│   ├── worker.yaml          # Celery Worker Deployment
│   ├── beat.yaml            # Celery Beat Deployment
│   ├── dashboard.yaml       # Streamlit Dashboard Deployment
│   ├── flower.yaml          # Flower Deployment
│   ├── services.yaml        # All Service definitions
│   ├── ingress.yaml         # Ingress rules
│   └── pvc.yaml             # Persistent Volume Claims
│
├── overlays/
│   ├── dev/                 # Development overlay
│   │   ├── kustomization.yaml
│   │   └── patches/
│   │
│   └── prod/                # Production overlay
│       ├── kustomization.yaml
│       ├── patches/
│       └── hpa.yaml         # Horizontal Pod Autoscaler
│
└── README.md                # This file
```

---

## Prerequisites

1. **Kubernetes Cluster**
   - Minikube (local development)
   - GKE, EKS, AKS (cloud)
   - Kind (local testing)

2. **Tools**
   ```bash
   # kubectl
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

   # kustomize (optional, kubectl has built-in support)
   kubectl kustomize --help
   ```

3. **Container Registry**
   - Docker Hub, GCR, ECR, ACR, or private registry
   - Build and push image: `docker build -t your-registry/ztrade:latest .`

---

## Quick Start

### 1. Create Secrets

```bash
# Create secrets file (DO NOT commit this)
cat > k8s/base/secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: ztrade-secrets
  namespace: ztrade
type: Opaque
stringData:
  ALPACA_API_KEY: "your_key_here"
  ALPACA_SECRET_KEY: "your_secret_here"
  POSTGRES_PASSWORD: "your_password_here"
  FLOWER_PASSWORD: "your_password_here"
EOF
```

### 2. Deploy to Development

```bash
# Apply base + dev overlay
kubectl apply -k k8s/overlays/dev/

# Check status
kubectl get pods -n ztrade

# View logs
kubectl logs -f -n ztrade deployment/ztrade-trading
```

### 3. Deploy to Production

```bash
# Apply base + prod overlay
kubectl apply -k k8s/overlays/prod/

# Check status
kubectl get all -n ztrade
```

---

## Service Architecture

### Deployments

| Service | Replicas | CPU | Memory | Notes |
|---------|----------|-----|--------|-------|
| **trading** | 1 | 1-2 | 1-2Gi | Main application |
| **worker** | 3 | 2-4 | 2-4Gi | HPA enabled |
| **beat** | 1 | 0.25-0.5 | 256-512Mi | Single instance only |
| **dashboard** | 2 | 0.5-1 | 512Mi-1Gi | External access |
| **flower** | 1 | 0.25-0.5 | 256-512Mi | External access |

### StatefulSets

| Service | Replicas | Storage | Notes |
|---------|----------|---------|-------|
| **postgres** | 1 | 10Gi | PVC required |
| **redis** | 1 | 1Gi | Optional persistence |

---

## Access Services

### Port Forwarding (Development)

```bash
# Dashboard
kubectl port-forward -n ztrade svc/ztrade-dashboard 8501:8501

# Flower
kubectl port-forward -n ztrade svc/ztrade-flower 5555:5555

# PostgreSQL (debugging)
kubectl port-forward -n ztrade svc/ztrade-postgres 5432:5432
```

### Ingress (Production)

Access via configured domain:
- Dashboard: https://dashboard.ztrade.example.com
- Flower: https://flower.ztrade.example.com

---

## Scaling

### Manual Scaling

```bash
# Scale workers
kubectl scale deployment ztrade-worker --replicas=5 -n ztrade

# Scale dashboard
kubectl scale deployment ztrade-dashboard --replicas=3 -n ztrade
```

### Horizontal Pod Autoscaling (HPA)

```bash
# Apply HPA (production only)
kubectl apply -f k8s/overlays/prod/hpa.yaml

# Check HPA status
kubectl get hpa -n ztrade

# HPA will scale workers based on:
# - CPU utilization (target: 70%)
# - Memory utilization (target: 80%)
# - Min replicas: 2
# - Max replicas: 10
```

---

## Monitoring

### Resource Usage

```bash
# Pod resource usage
kubectl top pods -n ztrade

# Node resource usage
kubectl top nodes
```

### Logs

```bash
# Stream logs
kubectl logs -f -n ztrade deployment/ztrade-worker

# Last 100 lines
kubectl logs --tail=100 -n ztrade deployment/ztrade-trading

# Previous container (after crash)
kubectl logs -p -n ztrade pod/ztrade-worker-xxx
```

### Events

```bash
# View events
kubectl get events -n ztrade --sort-by='.lastTimestamp'
```

---

## Troubleshooting

### Pod Not Starting

```bash
# Describe pod for events
kubectl describe pod -n ztrade ztrade-worker-xxx

# Common issues:
# - Image pull errors
# - Resource constraints
# - ConfigMap/Secret not found
# - Volume mount issues
```

### Database Connection Issues

```bash
# Check PostgreSQL pod
kubectl get pods -n ztrade -l app=postgres

# Check PostgreSQL logs
kubectl logs -n ztrade statefulset/ztrade-postgres

# Test connection
kubectl exec -it -n ztrade deployment/ztrade-trading -- bash
> psql postgresql://ztrade:password@ztrade-postgres:5432/ztrade
```

### Worker Not Processing Tasks

```bash
# Check Redis
kubectl get pods -n ztrade -l app=redis

# Check worker logs
kubectl logs -f -n ztrade deployment/ztrade-worker

# Check Flower UI
kubectl port-forward -n ztrade svc/ztrade-flower 5555:5555
# Open http://localhost:5555
```

---

## Backup and Restore

### Backup PostgreSQL

```bash
# Backup database
kubectl exec -n ztrade statefulset/ztrade-postgres -- \
  pg_dump -U ztrade ztrade > backup-$(date +%Y%m%d).sql

# Backup to PVC
kubectl exec -n ztrade statefulset/ztrade-postgres -- \
  pg_dump -U ztrade ztrade -f /var/lib/postgresql/data/backup.sql
```

### Restore PostgreSQL

```bash
# Restore from backup
kubectl exec -i -n ztrade statefulset/ztrade-postgres -- \
  psql -U ztrade ztrade < backup-20251109.sql
```

---

## Updating

### Rolling Update

```bash
# Update image
kubectl set image deployment/ztrade-worker \
  ztrade-worker=your-registry/ztrade:v2.0 -n ztrade

# Watch rollout
kubectl rollout status deployment/ztrade-worker -n ztrade
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/ztrade-worker -n ztrade

# Rollback to specific revision
kubectl rollout undo deployment/ztrade-worker --to-revision=2 -n ztrade
```

---

## Cleanup

### Delete All Resources

```bash
# Delete namespace (removes everything)
kubectl delete namespace ztrade

# Or delete specific overlay
kubectl delete -k k8s/overlays/dev/
```

### Preserve Data

```bash
# Delete deployments but keep StatefulSets
kubectl delete deployment --all -n ztrade

# PVCs will persist even after pod deletion
```

---

## Production Best Practices

### 1. **Resource Limits**
- Always set resource requests and limits
- Use HPA for worker scaling
- Monitor resource usage

### 2. **Security**
- Use Secrets for sensitive data
- Enable RBAC
- Use NetworkPolicies
- Run as non-root user

### 3. **High Availability**
- Multiple replicas for stateless services
- Pod anti-affinity for spreading pods
- PodDisruptionBudgets for maintenance

### 4. **Monitoring**
- Prometheus + Grafana for metrics
- ELK/Loki for log aggregation
- Alertmanager for notifications

### 5. **Backups**
- Automated PostgreSQL backups
- PVC snapshots
- Disaster recovery plan

---

## Example Commands

### Full Deployment (Development)

```bash
# 1. Create namespace
kubectl apply -f k8s/base/namespace.yaml

# 2. Create secrets
kubectl apply -f k8s/base/secrets.yaml

# 3. Deploy everything
kubectl apply -k k8s/overlays/dev/

# 4. Wait for ready
kubectl wait --for=condition=ready pod -l app=ztrade -n ztrade --timeout=300s

# 5. Check status
kubectl get all -n ztrade

# 6. Access dashboard
kubectl port-forward -n ztrade svc/ztrade-dashboard 8501:8501
```

### Full Deployment (Production)

```bash
# 1. Build and push image
docker build -t your-registry/ztrade:v1.0 .
docker push your-registry/ztrade:v1.0

# 2. Update image in prod overlay
# Edit k8s/overlays/prod/kustomization.yaml

# 3. Deploy
kubectl apply -k k8s/overlays/prod/

# 4. Verify
kubectl get all -n ztrade
kubectl top pods -n ztrade

# 5. Access via ingress
# https://dashboard.ztrade.example.com
```

---

## Next Steps

1. Create all manifest files in `k8s/base/`
2. Configure overlays for dev/prod
3. Set up ingress controller (nginx, traefik)
4. Configure monitoring (Prometheus)
5. Set up CI/CD pipeline
6. Implement GitOps (ArgoCD, Flux)

---

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [12-Factor App](https://12factor.net/)
