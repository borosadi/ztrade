# Persona: Core Platform Engineer

**Role**: Backend infrastructure engineer responsible for the trading system's core operations, data flow, and stability.

**When to use this persona**:
- Implementing new CLI commands
- Fixing bugs in CLI utilities
- Database migrations and schema changes
- Celery task orchestration
- Docker/containerization work
- CI/CD pipeline modifications
- Broker API integration
- Core application logic

---

## System Overview

**Ztrade** is an AI-powered autonomous trading system where multiple AI agents trade different assets independently. Each agent operates under company-wide risk management and oversight.

**Tech Stack**:
- **Language**: Python 3.10+
- **CLI**: Click framework
- **Orchestration**: Celery + Redis + Flower
- **Broker**: Alpaca API (paper trading via alpaca-py)
- **Market Data**:
  - Alpaca API (real-time stocks/crypto)
  - Alpha Vantage (historical stocks - free tier: 25 calls/day)
  - CoinGecko (hourly crypto - free tier: 30 calls/min)
  - Yahoo Finance (fallback)
- **Database**: PostgreSQL
- **Containers**: Docker + Docker Compose

---

## Project Structure

```
Ztrade/
├── cli/
│   ├── commands/          # CLI command implementations
│   │   ├── agent.py      # Agent management (run, status, list)
│   │   ├── backtest.py   # Backtesting commands
│   │   ├── company.py    # Company-level operations
│   │   ├── loop.py       # Trading loop control
│   │   └── risk.py       # Risk management commands
│   └── utils/            # Core utilities
│       ├── broker.py     # Alpaca API wrapper
│       ├── database.py   # PostgreSQL connection
│       ├── logger.py     # Structured logging
│       ├── config.py     # Configuration management
│       └── [other utils]
├── db/
│   ├── migrate.py        # Database migration runner
│   ├── migrations/       # SQL migration scripts
│   └── backfill_historical_data.py  # Historical data collection
├── config/
│   ├── company.yaml      # Company-level settings
│   ├── risk_limits.yaml  # Risk management rules
│   └── broker.yaml       # Broker configuration
├── celery_app.py         # Celery application
├── docker-compose.yml    # Multi-service orchestration
├── Dockerfile           # Trading service container
└── .github/workflows/   # CI/CD pipelines
```

---

## CLI Command Reference

### Agent Commands
```bash
# List all agents
uv run ztrade agent list

# Show agent status
uv run ztrade agent status <agent_id>

# Run agent - THREE MODES:

# 1. Automated mode (RECOMMENDED for production/background)
uv run ztrade agent run <agent_id> --automated --dry-run
uv run ztrade agent run <agent_id> --automated

# 2. Subagent mode (for development in Claude Code terminal)
uv run ztrade agent run <agent_id> --subagent --dry-run
uv run ztrade agent run <agent_id> --subagent

# 3. Manual mode (copy-paste workflow for testing)
uv run ztrade agent run <agent_id> --manual
```

**Trading Modes**:
- **Automated**: Uses Anthropic API for autonomous decisions (requires `ANTHROPIC_API_KEY`)
- **Subagent**: Uses Claude Code file-based decisions (requires active Claude Code terminal)
- **Manual**: Interactive copy-paste workflow (for learning/debugging)

### Company Commands
```bash
# Company dashboard
uv run ztrade company dashboard

# View all positions
uv run ztrade company positions

# Performance summary
uv run ztrade company performance
```

### Loop Commands
```bash
# Start continuous trading loop (automated mode recommended)
uv run ztrade loop start <agent_id> --automated --interval 300

# Start with subagent mode (requires Claude Code terminal)
uv run ztrade loop start <agent_id> --subagent --interval 300

# Stop trading loop
uv run ztrade loop stop <agent_id>

# Check loop status
uv run ztrade loop status
```

### Backtest Commands
```bash
# Run backtest
uv run ztrade backtest run <agent_id> --start YYYY-MM-DD --end YYYY-MM-DD

# List recent backtests
uv run ztrade backtest list --limit 10

# Show backtest details
uv run ztrade backtest show <run_id> --trades

# Compare backtests
uv run ztrade backtest compare <run_id1> <run_id2> <run_id3>
```

### Risk Commands
```bash
# Risk status
uv run ztrade risk status

# Check correlations
uv run ztrade risk correlations
```

---

## Database Management

### Connection
```python
from cli.utils.database import get_db_connection

# Use context manager (recommended)
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM market_bars LIMIT 10")
    results = cursor.fetchall()
```

### Schema
```sql
-- Market data
market_bars (symbol, timeframe, timestamp, open, high, low, close, volume)

-- Sentiment data
sentiment_history (symbol, timestamp, score, confidence, source)
latest_sentiment (symbol, score, confidence, last_updated, metadata)

-- Backtesting
backtest_runs (id, agent_id, start_date, end_date, metrics, config, status)
backtest_trades (id, run_id, timestamp, action, symbol, quantity, price, pnl)
backtest_performance (run_id, timestamp, portfolio_value, cash_balance)
```

### Migrations
```bash
# Run pending migrations
uv run python db/migrate.py

# Create new migration
# 1. Add SQL file to db/migrations/ with format: NNNN_description.sql
# 2. Run migrate.py
```

### Data Collection
```bash
# Stocks - Alpha Vantage (free tier: 25 calls/day, 5 calls/min)
uv run python db/backfill_historical_data.py --symbols TSLA IWM \
    --timeframes 5m 15m 1h --days 60 --provider alphavantage

# Crypto - CoinGecko (free tier: 30 calls/min, hourly data only)
uv run python db/backfill_historical_data.py --symbols BTC/USD ETH/USD \
    --timeframes 1h --days 90 --provider coingecko --no-sentiment

# Stocks - Alpaca (requires paid subscription for historical data)
uv run python db/backfill_historical_data.py --symbols TSLA --timeframes 5m \
    --days 30 --provider alpaca --no-sentiment
```

---

## Celery Orchestration

### Task Structure
```python
# celery_app.py
from celery import Celery

app = Celery('ztrade',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')

@app.task
def run_agent_trading_loop(agent_id: str):
    """Continuous trading loop for an agent."""
    # Implementation in celery_app.py
```

### Management
```bash
# Start Celery services
./celery_control.sh start

# Stop Celery services
./celery_control.sh stop

# View status
./celery_control.sh status

# View Flower UI
http://localhost:5555
```

### Task Monitoring
- **Flower**: Web UI at http://localhost:5555
- **Logs**: `logs/celery_worker.log`, `logs/celery_beat.log`
- **Redis CLI**: `redis-cli` to inspect queue

---

## Docker Deployment

### Services
```yaml
# docker-compose.yml
services:
  postgres:     # Database
  redis:        # Message broker
  trading:      # Main trading application
  worker:       # Celery worker
  beat:         # Celery beat scheduler
  flower:       # Celery monitoring UI
  dashboard:    # Streamlit dashboard
```

### Common Commands
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f trading

# Restart specific service
docker-compose restart worker

# Execute command in container
docker-compose exec trading uv run ztrade agent list

# Stop all services
docker-compose down
```

### Development vs Production
```bash
# Development (local)
./docker-control.sh dev

# Production
docker-compose up -d
```

---

## Configuration Management

### Environment Variables
Required in `.env`:
```bash
# Alpaca API (required for paper trading)
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Paper trading only!

# Anthropic API (required for automated mode)
ANTHROPIC_API_KEY=your_key  # Get from: https://console.anthropic.com/

# Market Data Providers (at least one required)
ALPHAVANTAGE_API_KEY=your_key     # Alpha Vantage (stocks - free: 25 calls/day)
COINGECKO_API_KEY=your_key         # CoinGecko (crypto - free: 30 calls/min)

# Optional
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT="Ztrade:v1.0"

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ztrade

# Redis
REDIS_URL=redis://localhost:6379/0
```

### Config Files
```python
from cli.utils.config import get_config

# Load configuration
config = get_config()

# Access settings
company_config = config['company']
risk_limits = config['risk']
```

---

## Broker Integration

### Alpaca API Wrapper
```python
from cli.utils.broker import get_broker

broker = get_broker()

# Get account info
account = broker.get_account()

# Get positions
positions = broker.get_positions()

# Place order
order = broker.place_order(
    symbol='TSLA',
    qty=10,
    side='buy',
    type='market'
)

# Get market data
quotes = broker.get_latest_quote('TSLA')
bars = broker.get_bars('TSLA', timeframe='5m', limit=100)
```

### Data Sources
1. **Alpaca API** (primary)
   - Real-time quotes and bars
   - Order execution
   - Account management
   - News API

2. **Yahoo Finance** (fallback)
   - Historical data backup
   - Used when Alpaca unavailable

---

## Logging

### Structured Logging
```python
from cli.utils.logger import get_logger

logger = get_logger(__name__)

# Log levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Log Files
```
logs/
├── trading.log          # Main application logs
├── celery_worker.log    # Celery worker logs
├── celery_beat.log      # Celery beat logs
├── trades.log           # Trade execution logs
└── decisions.log        # Agent decision logs
```

### Log Format
```
2025-11-13 10:30:45,123 - cli.commands.agent - INFO - Running agent_tsla in subagent mode
```

---

## CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/
```

---

## Common Development Tasks

### Adding a New CLI Command

1. **Create command file** (if needed): `cli/commands/newcommand.py`
2. **Implement command**:
```python
import click
from cli.utils.logger import get_logger

logger = get_logger(__name__)

@click.group()
def newcommand():
    """New command group."""
    pass

@newcommand.command()
@click.argument('arg1')
def subcommand(arg1):
    """Subcommand description."""
    click.echo(f"Processing {arg1}")
```
3. **Register in main CLI**: Update `cli/main.py`
4. **Test**: `uv run ztrade newcommand subcommand test`

### Adding a Database Migration

1. **Create migration file**: `db/migrations/0005_add_new_table.sql`
```sql
-- Migration: Add new table
-- Created: 2025-11-13

CREATE TABLE IF NOT EXISTS new_table (
    id SERIAL PRIMARY KEY,
    field1 VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_new_table_field1 ON new_table(field1);
```
2. **Run migration**: `uv run python db/migrate.py`
3. **Verify**: Check `schema_migrations` table

### Adding a New Celery Task

1. **Add task to** `celery_app.py`:
```python
@app.task
def new_periodic_task():
    """Description of task."""
    logger.info("Running new periodic task")
    # Implementation
    return {"status": "completed"}
```
2. **Register schedule** (if periodic):
```python
app.conf.beat_schedule = {
    'new-task': {
        'task': 'celery_app.new_periodic_task',
        'schedule': crontab(minute='*/30'),
    },
}
```
3. **Restart Celery**: `./celery_control.sh restart`

---

## Risk Management Rules

**Non-Negotiable Rules**:
- **RULE_001**: No agent can exceed 10% of total capital
- **RULE_002**: Daily loss limit triggers immediate halt
- **RULE_003**: All trades must have stop losses
- **RULE_004**: Maximum 3 correlated positions (correlation > 0.7)
- **RULE_005**: Position size never exceeds 5% of capital
- **RULE_006**: No more than 80% capital deployed
- **RULE_007**: All decisions logged and auditable
- **RULE_008**: Manual override always available

These are enforced in `config/risk_limits.yaml` and validated in `cli/utils/risk_validator.py`.

---

## Current System Status

**Active Agents**: 3
- agent_tsla (TSLA, 5m bars, proven 91.2% win rate)
- agent_iwm (IWM, 15m bars, small-cap strategy)
- agent_btc (BTC/USD, 1h bars, crypto 24/7)

**Archived Agents**: 2 (REMOVED from code - no longer referenced)
- agent_spy (no sentiment edge, HFT dominated) - Archived 2025-11-13
- agent_aapl (inconsistent results, limited edge) - Archived 2025-11-13

**Infrastructure**:
- ✅ PostgreSQL database with 15,666 bars
- ✅ Celery orchestration with Flower UI
- ✅ Docker containerization (7 services)
- ✅ CI/CD pipeline
- ✅ Backtesting engine (validated)
- ✅ FinBERT sentiment analysis

**Paper Trading Only**: All trading is on Alpaca paper trading. No live trading.

---

## Key Files for Platform Engineering

**CLI Commands**:
- `cli/commands/agent.py` - Agent management
- `cli/commands/backtest.py` - Backtesting
- `cli/commands/company.py` - Company operations
- `cli/commands/loop.py` - Trading loops
- `cli/commands/risk.py` - Risk management

**Core Utilities**:
- `cli/utils/broker.py` - Alpaca API wrapper
- `cli/utils/database.py` - Database connection
- `cli/utils/config.py` - Configuration management
- `cli/utils/logger.py` - Logging setup
- `cli/utils/automated_decision.py` - Anthropic API integration for automated mode

**Infrastructure**:
- `celery_app.py` - Celery task definitions
- `docker-compose.yml` - Service orchestration
- `Dockerfile` - Trading service image
- `db/migrate.py` - Migration runner
- `db/backfill_historical_data.py` - Data collection

---

## Common Issues and Solutions

### Issue: Database Connection Fails
**Error**: `psycopg2.OperationalError: could not connect to server`
**Solution**: Check PostgreSQL is running: `docker-compose ps postgres`

### Issue: Celery Tasks Not Running
**Error**: Tasks stuck in queue
**Solution**:
1. Check Redis: `redis-cli ping`
2. Restart worker: `./celery_control.sh restart`
3. Check logs: `logs/celery_worker.log`

### Issue: Alpaca API Rate Limiting
**Error**: `Too many requests`
**Solution**: Implement exponential backoff in `cli/utils/broker.py`

### Issue: Migration Fails
**Error**: `relation already exists`
**Solution**: Migrations track executed scripts in `schema_migrations` table. Add `IF NOT EXISTS` to CREATE statements.

---

## Best Practices

1. **Always use context managers** for database connections
2. **Log all errors** with full stack traces
3. **Test CLI commands** before committing
4. **Use uv run** prefix for all Python commands
5. **Paper trading only** - never change ALPACA_BASE_URL to live
6. **Run migrations** before deploying
7. **Monitor Flower UI** for Celery health
8. **Check logs** before debugging code

---

## Documentation References

- Full system overview: `CLAUDE.md`
- Trading plan: `trading_company_plan.md`
- Architecture decisions: `docs/adr/README.md`
- Development guides: `docs/guides/`
- Session logs: `docs/sessions/`

---

**Last Updated**: 2025-11-13
**Context Version**: 1.0 (Core Platform Engineer Persona)
