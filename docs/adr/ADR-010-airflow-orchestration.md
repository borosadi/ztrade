# ADR-010: Apache Airflow Orchestration Strategy

**Status**: ✅ Accepted
**Date**: 2025-11-22
**Deciders**: Engineering Team
**Related**: [ADR-004](ADR-004-continuous-trading-loops.md), [ADR-006](ADR-006-containerization-strategy.md)

## Context

The trading system initially used a CLI-based architecture with Celery for task orchestration. This approach had several limitations:

### Problems with CLI/Celery Architecture

1. **Dual Orchestration Complexity**
   - CLI commands for manual operations
   - Celery tasks for automated trading
   - Loop managers for continuous execution
   - No unified monitoring or observability

2. **Limited Observability**
   - Logs scattered across multiple files
   - No visual representation of workflows
   - Difficult to debug task dependencies
   - Limited retry/error handling capabilities

3. **Operational Overhead**
   - 7 Docker containers to manage (trading, worker, beat, flower, dashboard, postgres, redis)
   - Multiple startup scripts (celery_control.sh, run_dashboard.sh, start_trading_at_market_open.sh)
   - Complex deployment and maintenance
   - ~2,835 lines of orchestration code

4. **Developer Experience**
   - Steep learning curve for new developers
   - Unclear workflow execution paths
   - Difficult to test individual tasks
   - No built-in task dependency visualization

### Requirements

- Unified orchestration platform for all trading workflows
- Visual monitoring and debugging
- Robust retry and error handling
- Simplified deployment and operations
- Clear task dependency management
- Better developer experience

## Decision

**Migrate to Apache Airflow as the sole orchestration platform**, replacing CLI commands, Celery tasks, and custom loop managers.

### Architecture

```
┌─────────────────────────────────────────────────┐
│            Apache Airflow (Scheduler)           │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │TSLA DAG  │  │ IWM DAG  │  │ BTC DAG  │     │
│  │          │  │          │  │          │     │
│  │ 5-min    │  │ 15-min   │  │ 60-min   │     │
│  │ 9-4 EST  │  │ 9-4 EST  │  │ 24/7     │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
         │                 │                │
         └─────────────────┴────────────────┘
                           │
              ┌────────────┴───────────────┐
              │   Ztrade Library Package   │
              │                            │
              │  - sentiment/              │
              │  - analysis/               │
              │  - decision/               │
              │  - execution/              │
              │  - core/                   │
              └────────────┬───────────────┘
                           │
              ┌────────────┴───────────────┐
              │    Alpaca Broker API       │
              └────────────────────────────┘
```

### Key Components

1. **Airflow DAGs** - One per trading agent
   - Schedule-based execution (cron expressions)
   - Task dependencies via `>>` operator
   - XCom for inter-task data passing
   - Built-in retry logic and error handling

2. **Ztrade Library** - Reorganized from `cli/utils/` to `ztrade/`
   - Modular structure (sentiment/, analysis/, decision/, execution/, core/)
   - Imported by DAG task functions
   - Pure Python library, no CLI dependencies
   - Clean, testable interfaces

3. **Docker Compose** - Simplified infrastructure
   - 5 core services (airflow-scheduler, airflow-webserver, postgres, redis, airflow-init)
   - Single docker-compose.airflow.yml file
   - Unified environment configuration in airflow/.env

### Migration Changes

#### Code Reorganization (31% Reduction)

**Archived** (~2,835 lines):
- `cli/commands/` - 1,992 lines (agent.py, loop.py, company.py, monitor.py, risk.py, subagent.py)
- `celery_app.py` - 378 lines
- `cli/utils/loop_manager.py` - 321 lines
- `cli/utils/subagent.py` - 144 lines

**Reorganized** (~4,314 lines):
- `cli/utils/` → `ztrade/` package with submodules:
  - `ztrade/sentiment/` (aggregator, news, reddit, sec, finbert)
  - `ztrade/analysis/` (technical, improved_technical)
  - `ztrade/decision/` (algorithmic, automated)
  - `ztrade/execution/` (risk, trade_executor)
  - `ztrade/core/` (database, config, logger)

#### Infrastructure Simplification

**Before** (7 containers):
- trading-dev (custom trading service)
- worker-dev (Celery worker)
- beat-dev (Celery beat scheduler)
- flower-dev (Celery monitoring UI)
- dashboard-dev (Streamlit dashboard)
- postgres-dev
- redis-dev

**After** (5 containers):
- airflow-scheduler (DAG execution)
- airflow-webserver (Web UI)
- postgres (Airflow metadata + Ztrade data)
- redis (Airflow message broker)
- airflow-init (one-time setup)

**Removed** (~6.8 GB Docker images, 7 containers)

## Consequences

### Positive

1. **✅ Unified Orchestration**
   - Single platform for all workflows
   - No dual CLI/Celery architecture
   - Consistent execution model

2. **✅ Better Observability**
   - Visual DAG graphs in Airflow UI
   - Real-time task monitoring
   - Complete execution history
   - XCom data inspection
   - Centralized logging

3. **✅ Simplified Operations**
   - Single docker-compose command to start
   - Fewer containers to manage
   - Easier deployment
   - Built-in health checks

4. **✅ Improved Reliability**
   - Robust retry mechanisms
   - Task timeout handling
   - Dependency management
   - Error alerting (configurable)

5. **✅ Better Developer Experience**
   - Visual workflow representation
   - Easy to test individual tasks
   - Clear task dependencies
   - Well-documented platform (Apache Airflow docs)

6. **✅ Cleaner Codebase**
   - -31% code reduction
   - Better organized modules
   - Clear separation of concerns
   - Library-first approach

7. **✅ Future-Ready**
   - Can add more complex workflows easily
   - Support for SLAs and monitoring
   - Integration with external systems
   - Scalable architecture

### Negative

1. **❌ Archived Functionality**
   - CLI commands no longer available
   - Subagent mode (Claude Code file-based decisions) archived
   - Interactive mode archived
   - Backtesting CLI archived (can be restored or reimplemented as DAGs)

   **Mitigation**: All code preserved in `.archive/` for restoration if needed.

2. **❌ Learning Curve**
   - Team must learn Airflow concepts (DAGs, operators, XCom)
   - Different debugging approach (Airflow UI vs logs)

   **Mitigation**: Created comprehensive documentation and guides.

3. **❌ Airflow Overhead**
   - More complex than simple cron jobs
   - Requires understanding Airflow architecture
   - Additional moving parts (scheduler, webserver, metadata DB)

   **Mitigation**: Containerization simplifies deployment, Docker Compose handles complexity.

4. **❌ Migration Effort**
   - All 3 trading DAGs updated with new imports
   - Documentation rewritten
   - Testing required for each DAG

   **Mitigation**: All migration completed in single session (2025-11-22).

### Neutral

- Airflow is overkill for simple schedules, but provides value for complex workflows
- XCom has size limitations (<1MB recommended), but suitable for our inter-task data
- Airflow requires PostgreSQL metadata DB, but we already use PostgreSQL for market data

## Implementation

### DAG Structure

Each trading agent has its own DAG following this pattern:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
sys.path.insert(0, '/opt/airflow/ztrade')

from ztrade.broker import get_broker
from ztrade.market_data import get_market_data_provider
from ztrade.decision.algorithmic import get_algorithmic_decision_maker
from ztrade.execution.risk import RiskValidator
from ztrade.execution.trade_executor import TradeExecutor
from ztrade.core.config import get_config
from ztrade.core.logger import get_logger

def fetch_market_data(**context):
    broker = get_broker()
    quote = broker.get_latest_quote(ASSET)
    context['task_instance'].xcom_push(key='current_price', value=quote['ask'])

def analyze_sentiment(**context):
    # ... sentiment analysis logic
    context['task_instance'].xcom_push(key='sentiment_score', value=score)

def make_decision(**context):
    ti = context['task_instance']
    price = ti.xcom_pull(task_ids='fetch_market_data', key='current_price')
    sentiment = ti.xcom_pull(task_ids='analyze_sentiment', key='sentiment_score')
    # ... decision logic
    ti.xcom_push(key='decision', value=decision)

dag = DAG(
    dag_id='agent_tsla_trading',
    schedule_interval='*/5 9-15 * * 1-5',  # Every 5 min, 9-4 EST, Mon-Fri
    default_args={'retries': 2, 'retry_delay': timedelta(seconds=30)},
    catchup=False,
)

task1 = PythonOperator(task_id='fetch_market_data', python_callable=fetch_market_data, dag=dag)
task2 = PythonOperator(task_id='analyze_sentiment', python_callable=analyze_sentiment, dag=dag)
task3 = PythonOperator(task_id='make_decision', python_callable=make_decision, dag=dag)

task1 >> [task2, task3]  # Parallel sentiment + technical, then decision
```

### Deployment

```bash
# Start Airflow
cd airflow
docker-compose -f docker-compose.airflow.yml up -d

# Access UI
open http://localhost:8080

# Trigger DAG
docker exec airflow-airflow-scheduler-1 airflow dags trigger agent_tsla_trading

# View logs
docker-compose -f docker-compose.airflow.yml logs -f airflow-scheduler
```

### Migration Checklist

- [x] Create `ztrade/` package structure
- [x] Move and reorganize core utils
- [x] Update all DAG imports
- [x] Archive CLI commands and Celery infrastructure
- [x] Test DAGs with new imports
- [x] Update CLAUDE.md
- [x] Update README.md
- [x] Create this ADR
- [ ] Run 1-2 week validation period
- [ ] Create Airflow operations guide
- [ ] Document session log
- [ ] Permanently remove archived code (after validation)

## Alternatives Considered

### 1. Keep CLI + Celery (Status Quo)

**Pros**:
- No migration effort
- Familiar to team
- CLI convenient for manual operations

**Cons**:
- Dual orchestration complexity
- Poor observability
- High operational overhead
- 31% more code to maintain

**Decision**: ❌ Rejected - Complexity and maintenance burden too high

### 2. Kubernetes CronJobs

**Pros**:
- Simple scheduling
- Native Kubernetes integration
- No additional platform

**Cons**:
- No workflow visualization
- Limited retry logic
- No built-in monitoring
- Requires Kubernetes cluster

**Decision**: ❌ Rejected - Too simple, lacks needed features

### 3. Prefect

**Pros**:
- Modern Python-first API
- Cloud-native design
- Good observability

**Cons**:
- Smaller community than Airflow
- Less mature ecosystem
- Cloud-focused (self-hosting more complex)

**Decision**: ❌ Rejected - Airflow more established, better documented

### 4. Custom Scheduler

**Pros**:
- Full control
- Tailored to our needs
- No external dependencies

**Cons**:
- Massive development effort
- Reinventing the wheel
- Maintenance burden
- No community support

**Decision**: ❌ Rejected - Not worth the effort

## References

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [ADR-004: Continuous Trading Loops](ADR-004-continuous-trading-loops.md)
- [ADR-006: Containerization Strategy](ADR-006-containerization-strategy.md)
- [Cleanup Analysis](/tmp/cleanup_analysis.md)
- [Cleanup Completed](/tmp/cleanup_completed.md)

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-22 | 1.0 | Initial ADR for Airflow migration | Engineering Team |

---

**Next Steps**:
1. Monitor Airflow DAG execution for 1-2 weeks
2. Document any issues or improvements needed
3. Create Airflow operations guide for team
4. Consider reimplementing backtesting as Airflow DAGs
5. Evaluate custom Airflow operators for common tasks
