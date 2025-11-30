# Ztrade Airflow Orchestration

Production-grade trading system using **Apache Airflow** for DAG-based orchestration. Each trading agent runs as an independent DAG with explicit task dependencies for the complete trading pipeline.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Apache Airflow Scheduler                     │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  agent_tsla  │  │  agent_iwm   │  │  agent_btc   │          │
│  │     DAG      │  │     DAG      │  │     DAG      │          │
│  │              │  │              │  │              │          │
│  │  Every 5min  │  │  Every 15min │  │  Every 1hr   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
      ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
      │  PostgreSQL  │ │   Alpaca    │ │   Redis    │
      │  (Airflow +  │ │  Broker API │ │   Cache    │
      │   Ztrade)    │ └─────────────┘ └────────────┘
      └──────────────┘
```

## Trading Pipeline (Each DAG)

Each agent DAG executes these tasks in sequence:

```
1. check_market_hours      → Verify market is open (EST timezone)
        ↓
2. fetch_market_data        → Get current price, quotes
        ↓
3. analyze_sentiment    ──┐
   analyze_technical    ──┼──→ Parallel execution
                         ┘
        ↓
4. make_decision            → Algorithmic decision (60% sentiment, 40% technical)
        ↓
5. validate_risk            → Risk rules validation
        ↓
6. execute_trade            → Submit order to broker (if approved)
        ↓
7. log_performance          → Store metrics & performance data
```

## Quick Start

### 1. Setup Environment

```bash
cd airflow

# Copy and configure environment
cp .env.airflow .env
# Edit .env with your API keys
```

### 2. Start Airflow

```bash
# Start all services (Airflow + PostgreSQL + Redis)
docker-compose -f docker-compose.airflow.yml up -d

# Wait for initialization (30-60 seconds)
# Watch logs
docker-compose -f docker-compose.airflow.yml logs -f airflow-init
```

### 3. Access Airflow UI

```
URL: http://localhost:8080
Username: admin
Password: admin
```

### 4. Enable DAGs

In the Airflow UI:
1. Navigate to DAGs page
2. Enable the agent DAGs:
   - `agent_tsla_trading` (5-minute cycles)
   - `agent_iwm_trading` (15-minute cycles)
   - `agent_btc_trading` (1-hour cycles, 24/7)

### 5. Monitor Trading

- **DAG Runs**: View execution history
- **Task Logs**: Detailed logs for each pipeline step
- **XCom**: Inspect data passed between tasks
- **Gantt Chart**: Visualize task timing

## DAG Schedules

| Agent | Asset | Schedule | Active Hours | Timezone |
|-------|-------|----------|--------------|----------|
| **agent_tsla** | TSLA | Every 5 min | 9:30 AM - 4:00 PM | EST |
| **agent_iwm** | IWM | Every 15 min | 9:30 AM - 4:00 PM | EST |
| **agent_btc** | BTC/USD | Every 1 hour | 24/7 | All |

## Configuration

### Environment Variables

Required in `.env`:

```bash
# Airflow
AIRFLOW_UID=50000
_AIRFLOW_WWW_USER_USERNAME=admin
_AIRFLOW_WWW_USER_PASSWORD=admin

# Trading APIs
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Market Data
ALPHAVANTAGE_API_KEY=your_key
COINGECKO_API_KEY=your_key

# Sentiment Analysis
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
```

### Task Retry Policy

Default retry settings (in `default_args`):
- **Retries**: 2
- **Retry Delay**: 30 seconds
- **Email on Failure**: Disabled (configure SMTP to enable)

### Parallel Execution

- Sentiment and technical analysis run in parallel
- Max 1 DAG run per agent at a time (`max_active_runs=1`)
- LocalExecutor: tasks run on same machine
- For scaling: switch to CeleryExecutor

## Management Commands

### Start/Stop Services

```bash
# Start
docker-compose -f docker-compose.airflow.yml up -d

# Stop
docker-compose -f docker-compose.airflow.yml down

# Stop and remove data
docker-compose -f docker-compose.airflow.yml down -v
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.airflow.yml logs -f

# Specific service
docker-compose -f docker-compose.airflow.yml logs -f airflow-scheduler

# Airflow task logs (in UI or CLI)
docker-compose -f docker-compose.airflow.yml exec airflow-webserver \
  airflow tasks logs agent_tsla_trading fetch_market_data 2024-11-20T10:00:00+00:00
```

### CLI Access

```bash
# Airflow CLI
docker-compose -f docker-compose.airflow.yml exec airflow-webserver airflow --help

# List DAGs
docker-compose -f docker-compose.airflow.yml exec airflow-webserver airflow dags list

# Trigger DAG manually
docker-compose -f docker-compose.airflow.yml exec airflow-webserver \
  airflow dags trigger agent_tsla_trading

# Test specific task
docker-compose -f docker-compose.airflow.yml exec airflow-webserver \
  airflow tasks test agent_tsla_trading fetch_market_data 2024-11-20
```

## Monitoring & Alerts

### Airflow UI Features

1. **DAG View**: Visual task graph
2. **Tree View**: Historical run timeline
3. **Gantt Chart**: Task duration analysis
4. **Task Logs**: Detailed execution logs
5. **XCom**: Inter-task data inspection

### Custom Metrics

Each `log_performance` task stores:
- Timestamp
- Asset & price
- Sentiment score & confidence
- Technical signal & confidence
- Decision & rationale
- Trade execution status

### Email Alerts (Optional)

Configure SMTP in `airflow.cfg`:

```ini
[smtp]
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
smtp_user = your_email@gmail.com
smtp_password = your_app_password
smtp_port = 587
smtp_mail_from = airflow@ztrade.local
```

Then enable in DAG `default_args`:
```python
'email_on_failure': True,
'email_on_retry': False,
'email': ['your_email@gmail.com'],
```

## Troubleshooting

### DAG not showing up

```bash
# Check DAG parsing errors
docker-compose -f docker-compose.airflow.yml exec airflow-scheduler \
  airflow dags list-import-errors

# Refresh DAGs
docker-compose -f docker-compose.airflow.yml restart airflow-scheduler
```

### Task failures

1. Check task logs in UI
2. Verify environment variables
3. Test task manually:
   ```bash
   docker-compose -f docker-compose.airflow.yml exec airflow-webserver \
     airflow tasks test agent_tsla_trading fetch_market_data 2024-11-20
   ```

### Database connection errors

```bash
# Check PostgreSQL status
docker-compose -f docker-compose.airflow.yml ps postgres

# Check connection
docker-compose -f docker-compose.airflow.yml exec postgres \
  psql -U airflow -c "SELECT version();"
```

### Import errors (Ztrade modules not found)

Verify volume mounts in `docker-compose.airflow.yml`:
```yaml
volumes:
  - .:/opt/airflow/ztrade  # Ztrade codebase mounted
```

## Production Deployment

### Recommendations

1. **Use CeleryExecutor** for scaling:
   - Uncomment Celery worker in `docker-compose.airflow.yml`
   - Update `AIRFLOW__CORE__EXECUTOR=CeleryExecutor`

2. **External PostgreSQL**:
   - Use managed database (RDS, Cloud SQL)
   - Update connection string in `.env`

3. **Secrets Management**:
   - Use Airflow Connections for API keys
   - Or AWS Secrets Manager / HashiCorp Vault

4. **Monitoring**:
   - Enable Prometheus metrics
   - Set up Grafana dashboards
   - Configure StatsD

5. **High Availability**:
   - Run multiple schedulers (Airflow 2.x supports this)
   - Use load balancer for webservers

### Security Checklist

- [ ] Change default admin password
- [ ] Enable authentication (LDAP/OAuth)
- [ ] Use HTTPS for webserver
- [ ] Rotate Fernet key
- [ ] Enable audit logs
- [ ] Restrict network access
- [ ] Use read-only database user for DAGs

## Development

### Adding New Agents

1. Copy existing DAG:
   ```bash
   cp dags/agent_tsla_dag.py dags/agent_new_dag.py
   ```

2. Update:
   - `AGENT_ID`
   - `ASSET`
   - `INTERVAL_MINUTES`
   - `schedule_interval`

3. Refresh Airflow to detect new DAG

### Custom Tasks

Create custom operators in `airflow/plugins/`:

```python
from airflow.models import BaseOperator

class ZtradeOperator(BaseOperator):
    def execute(self, context):
        # Your logic here
        pass
```

## Architecture Decisions

### Why Airflow?

✅ **Orchestration**: Explicit task dependencies
✅ **Monitoring**: Rich UI for debugging
✅ **Scheduling**: Cron-based with backfill support
✅ **Retries**: Built-in retry logic
✅ **Scaling**: Celery/Kubernetes executors
✅ **Python-native**: Easy integration with Ztrade

### Alternative Options Considered

- **Celery Beat** (current): Limited UI, basic scheduling
- **Prefect**: Modern, but less mature ecosystem
- **Dagster**: Asset-centric, more complex
- **Temporal**: Workflow-centric, overkill for this use case

## Support

For issues:
1. Check Airflow logs
2. Review DAG import errors
3. Test tasks manually
4. Check [Airflow Docs](https://airflow.apache.org/docs/)

## License

Same as Ztrade main project
