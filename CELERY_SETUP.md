# Celery + Flower Setup for Ztrade

This document explains the Celery orchestration setup for autonomous trading loops.

## Quick Start

### Start All Services
```bash
./celery_control.sh start
```

This starts:
- **Redis** (message broker)
- **Celery Worker** (executes tasks)
- **Celery Beat** (scheduler for periodic tasks)
- **Flower** (web UI at http://localhost:5555)

### Open Flower Web UI
```bash
open http://localhost:5555
```

Flower provides:
- Real-time task monitoring
- Worker status and performance
- Task history and results
- Task graphs and statistics

### Check Status
```bash
./celery_control.sh status
```

### View Logs
```bash
# Worker logs (task execution)
./celery_control.sh logs worker

# Beat logs (scheduler)
./celery_control.sh logs beat

# Flower logs (web UI)
./celery_control.sh logs flower
```

### Send Test Task
```bash
./celery_control.sh test
```

### Stop All Services
```bash
./celery_control.sh stop
```

---

## Architecture

### Components

**1. Redis (Message Broker)**
- Stores task queue
- Stores task results
- Running on: `localhost:6379`

**2. Celery Worker**
- Executes tasks from queue
- Concurrency: 8 workers (prefork)
- Logs: `/tmp/celery_worker.log`

**3. Celery Beat (Scheduler)**
- Schedules periodic tasks
- Sends tasks to queue on schedule
- Logs: `/tmp/celery_beat.log`

**4. Flower (Web UI)**
- Monitoring dashboard
- URL: http://localhost:5555
- Logs: `/tmp/flower.log`

### Task Flow

```
Celery Beat (Scheduler)
    ↓ Every 5 min
Task Queue (Redis)
    ↓
Celery Worker
    ↓
Trading Cycle Execution
    ↓
Task Result (Redis)
    ↓
Flower Dashboard
```

---

## Scheduled Tasks

Configured in `celery_app.py` → `app.conf.beat_schedule`:

### 1. Agent SPY - Every 5 Minutes
```python
'agent-spy-trading-cycle': {
    'task': 'ztrade.trading_cycle',
    'schedule': timedelta(minutes=5),
    'args': ('agent_spy', True, True),  # dry_run=True, manual=True
}
```

### 2. Agent TSLA - Every 5 Minutes
```python
'agent-tsla-trading-cycle': {
    'task': 'ztrade.trading_cycle',
    'schedule': timedelta(minutes=5),
    'args': ('agent_tsla', True, True),
}
```

### 3. Agent AAPL - Every 1 Hour
```python
'agent-aapl-trading-cycle': {
    'task': 'ztrade.trading_cycle',
    'schedule': timedelta(hours=1),
    'args': ('agent_aapl', True, True),
}
```

### 4. Test Task - Every 1 Minute
```python
'test-task': {
    'task': 'ztrade.test_task',
    'schedule': timedelta(minutes=1),
}
```

---

## Manual Task Execution

You can manually trigger tasks without waiting for the schedule:

### Python API
```python
from celery_app import trading_cycle, test_task

# Send task to queue
result = trading_cycle.delay('agent_spy', dry_run=True, manual=True)

# Get task ID
print(f"Task ID: {result.id}")

# Wait for result (blocking)
result.get(timeout=60)
```

### CLI
```bash
# Send test task
uv run python3 -c "from celery_app import test_task; test_task.delay()"

# Send trading cycle
uv run python3 -c "from celery_app import trading_cycle; trading_cycle.delay('agent_spy')"
```

---

## Configuration

### Celery Settings
Located in `celery_app.py`:

```python
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/New_York',  # EST for market hours
    enable_utc=False,
    task_track_started=True,
    task_time_limit=600,  # 10 minute max per task
    worker_prefetch_multiplier=1,  # Process one task at a time
)
```

### Changing Schedule
Edit `celery_app.py` → `app.conf.beat_schedule` and restart beat:

```bash
./celery_control.sh restart
```

---

## Monitoring with Flower

### Key Features

**Tasks Page** (`/tasks`)
- List of all tasks (active, succeeded, failed)
- Filter by status, time, worker
- Click task for details (args, result, traceback)

**Workers Page** (`/workers`)
- Worker status (online/offline)
- Active tasks per worker
- Worker configuration

**Monitor Page** (`/monitor`)
- Real-time task stream
- Success/failure rate graphs
- Task completion timeline

**Broker Page** (`/broker`)
- Redis connection status
- Queue length
- Message statistics

---

## Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis
```

### Worker Not Picking Up Tasks
```bash
# Check worker is running
./celery_control.sh status

# View worker logs
./celery_control.sh logs worker

# Restart worker
./celery_control.sh restart
```

### Beat Not Scheduling Tasks
```bash
# Check beat logs
./celery_control.sh logs beat

# Ensure beat is running
pgrep -f "celery.*beat"

# Restart beat
./celery_control.sh restart
```

### Flower Not Accessible
```bash
# Check if Flower is running
curl http://localhost:5555

# Check Flower logs
./celery_control.sh logs flower

# Restart Flower
./celery_control.sh restart
```

---

## Production Considerations

### Current Setup (Development)
- ✅ Single machine
- ✅ Redis on localhost
- ✅ Worker in foreground
- ✅ Perfect for development and testing

### For Production (Future)
1. **Dedicated Redis Server**
   - Persistent storage
   - Password authentication
   - Backup strategy

2. **Systemd/Supervisor for Workers**
   - Auto-restart on failure
   - Log rotation
   - Resource limits

3. **Multiple Workers**
   - Dedicated worker per agent
   - Separate queues for priority

4. **Monitoring**
   - Prometheus + Grafana
   - Email/Slack alerts
   - SLA tracking

5. **Security**
   - Flower authentication
   - SSL/TLS for Redis
   - Firewall rules

---

## Comparison: Celery vs Custom Loop Manager

| Feature | Custom loop_manager.py | Celery + Flower |
|---------|------------------------|-----------------|
| **Web UI** | ❌ No | ✅ Flower |
| **Task History** | ⚠️ JSON files | ✅ Redis backend |
| **Monitoring** | ⚠️ Log files | ✅ Real-time dashboard |
| **Retries** | ❌ Manual | ✅ Automatic with backoff |
| **Distributed** | ❌ Single process | ✅ Multiple workers |
| **Scheduling** | ⚠️ Custom | ✅ Cron + timedelta |
| **Learning Curve** | ✅ Simple | ⚠️ Medium |
| **Setup Time** | ✅ 5 min | ⚠️ 30 min |
| **Production Ready** | ⚠️ Basic | ✅ Battle-tested |

**Recommendation**:
- **Development**: Both work fine, use whichever you prefer
- **Production (3+ agents)**: Celery is better for fault tolerance and monitoring

---

## Next Steps

1. **Test Periodic Tasks**
   - Wait 5 minutes and check Flower for automatic task execution
   - Verify trading cycles run on schedule

2. **Adjust Schedules**
   - Modify intervals in `celery_app.py`
   - Restart beat: `./celery_control.sh restart`

3. **Add Market Hours Filter**
   - Integrate `LoopSchedule.is_market_hours()` into tasks
   - Skip execution if outside market hours

4. **Build Custom Dashboard**
   - Streamlit dashboard showing P&L, sentiment, positions
   - Celery provides task infrastructure, custom dashboard shows trading metrics

5. **Performance Tracking Integration**
   - Add `performance_tracker.log_trade_with_sentiment()` to trading cycle
   - Track which sentiment sources lead to profitable trades
