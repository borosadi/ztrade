# CLAUDE.md

This file provides quick-reference guidance to Claude Code when working with this repository.

---

## 🎯 Context Optimization: Persona System

**IMPORTANT**: For most development tasks, **use a specialized persona file instead of this full document** to reduce token usage by 75% and improve focus.

### Quick Selector

| Your Task | Use This Persona |
|-----------|------------------|
| Airflow/DAGs/Database/Docker/Infrastructure | [Core Platform Engineer](.claude/personas/core-platform-engineer.md) |
| Agents/Strategies/Sentiment/Technical Analysis | [Agent Specialist](.claude/personas/agent-specialist.md) |
| Dashboard/UI/Charts/Visualization | [Dashboard Developer](.claude/personas/dashboard-developer.md) |
| Backtesting/Risk/Data Analysis/Performance | [Risk & Data Analyst](.claude/personas/risk-data-analyst.md) |
| Cross-cutting concerns or initial orientation | This file (CLAUDE.md) |

**📚 Full guide**: [.claude/personas/README.md](.claude/personas/README.md)

**Benefits**:
- ✅ 75% token reduction (3K vs 15K tokens)
- ✅ 4x more interactions per session
- ✅ Focused, relevant context
- ✅ Faster responses

**When to use this full file**: Initial orientation, cross-cutting architectural changes, strategic decisions affecting multiple systems.

---

## Project Overview

**Ztrade** is an AI-powered autonomous trading system where multiple AI agents trade different assets independently. Each agent has its own strategy, risk profile, and personality, operating under company-wide risk management and oversight.

**Key Technologies:**
- **Orchestration**: Apache Airflow (DAG-based workflows)
- **AI**: Algorithmic decision-making with multi-source sentiment analysis
- **Broker**: Alpaca API (paper trading via alpaca-py)
- **Market Data**:
  - Alpaca API (real-time stocks/crypto)
  - Alpha Vantage (historical stocks)
  - CoinGecko (hourly crypto - BTC, ETH, SOL, etc.)
  - Yahoo Finance (fallback)
- **Database**: PostgreSQL (market data, backtest results)
- **Message Broker**: Redis (Airflow backend)
- **Language**: Python 3.10+
- **Deployment**: Docker Compose

---

## Current System Status (Updated 2025-11-30)

### Active Trading Agents (13)

**Stock Agents (7)** - Trade during market hours (Mon-Fri, 9:30 AM - 4:00 PM EST)

| Agent | Asset | Strategy | Timeframe | Schedule | Status | Notes |
|-------|-------|----------|-----------|----------|--------|-------|
| **agent_tsla** | TSLA | Sentiment-Momentum | 5-min | Every 5 min | ✅ Validated | 91.2% win rate in backtest |
| **agent_iwm** | IWM | Sentiment-Momentum | 15-min | Every 15 min | 🆕 Ready | Small-cap sentiment edge |
| **agent_pltr** | PLTR | Sentiment-Momentum | 15-min | Every 15 min | 🆕 Ready | AI/defense narratives |
| **agent_roku** | ROKU | Sentiment-Momentum | 15-min | Every 15 min | 🆕 Ready | Streaming sector volatility |
| **agent_net** | NET | Sentiment-Momentum | 15-min | Every 15 min | 🆕 Ready | Cloud/security narratives |
| **agent_snap** | SNAP | Sentiment-Momentum | 15-min | Every 15 min | 🆕 Ready | Social media sentiment |
| **agent_ddog** | DDOG | Sentiment-Momentum | 15-min | Every 15 min | 🆕 Ready | DevOps/observability sector |

**Crypto Agents (6)** - Trade 24/7

| Agent | Asset | Strategy | Timeframe | Schedule | Status | Notes |
|-------|-------|----------|-----------|----------|--------|-------|
| **agent_btc** | BTC/USD | Sentiment-Momentum | 1-hour | Every hour | 🆕 Ready | Flagship crypto, 40-60% sentiment edge |
| **agent_eth** | ETH/USD | Sentiment-Momentum | 1-hour | Every hour | 🆕 Ready | DeFi ecosystem narratives |
| **agent_sol** | SOL/USD | Sentiment-Momentum | 1-hour | Every hour | 🆕 Ready | NFT/ecosystem sentiment |
| **agent_doge** | DOGE/USD | Sentiment-Momentum | 1-hour | Every hour | 🆕 Ready | Meme coin, Elon-driven narratives |
| **agent_shib** | SHIB/USD | Sentiment-Momentum | 1-hour | Every hour | 🆕 Ready | Meme coin, Shib Army sentiment |
| **agent_xrp** | XRP/USD | Sentiment-Momentum | 1-hour | Every hour | 🆕 Ready | Regulatory/SEC lawsuit sentiment |

### Archived Agents (Removed - No Sentiment Edge)

| Agent | Asset | Archived | Reason |
|-------|-------|----------|--------|
| agent_spy | SPY | 2025-11-13 | HFT-dominated, 0% sentiment edge |
| agent_aapl | AAPL | 2025-11-13 | Mega-cap, limited edge |

**Portfolio Strategy**:
- Focus on sentiment-driven volatility in mid-cap stocks and crypto
- Diversified across sectors (tech, streaming, crypto ecosystems)
- Mix of market-hours (stocks) and 24/7 (crypto) trading
- Avoid HFT-dominated mega-cap stocks and major indices

### System Capabilities

**✅ Working:**
- Apache Airflow orchestration (DAG-based workflows)
- Real-time market data (Alpaca API)
- Multi-source sentiment analysis (News + Reddit + SEC)
- **✅ FinBERT sentiment analysis**
  - Domain-specific financial sentiment (ProsusAI/finbert)
  - VADER-compatible API for drop-in replacement
  - Batch processing support
  - GPU acceleration (CUDA/MPS)
- Performance tracking for sentiment sources
- Traditional technical analysis (RSI, SMA, trend, volume, support/resistance)
- Hybrid decision-making (TA + Sentiment synthesis)
- Algorithmic decision-making (60% sentiment, 40% technical)
- Risk validation and circuit breakers
- Paper trading execution
- Historical data collection (PostgreSQL with 10,735 bars across 3 symbols)
- **✅ Backtesting framework (FULLY FUNCTIONAL)**
  - Event-driven portfolio simulation
  - 100-bar trend analysis (captures 8-hour trends on 5m timeframe)
  - Directional signal synthesis (ignores neutral noise)
  - Smart position sizing (handles % and $ configs)
  - Type-safe calculations (Decimal → float conversions)
  - TSLA validation: 34 trades, 91.2% win rate, 8.51% return
- Full Docker containerization (Airflow stack)

**📋 Strategic Initiatives:**
- **Backtest Validation**: Validate all 13 agents through backtesting (IWM, BTC, ETH, SOL, DOGE, SHIB, XRP, PLTR, ROKU, NET, SNAP, DDOG)
- **Multi-Agent Trading**: Run all 13 agents simultaneously (7 stocks + 6 crypto)
- **Performance Monitoring**: Track sentiment alpha across different asset classes
- **Risk Correlation**: Monitor correlation between agents to ensure diversification
- **Sector Rotation**: Dynamically adjust capital allocation based on sentiment heat maps
- **Strategy Optimization**: Walk-forward testing and parameter tuning per agent

---

## Quick Start

### Starting Airflow

```bash
# Start all Airflow services
cd airflow
docker-compose -f docker-compose.airflow.yml up -d

# Check service status
docker-compose -f docker-compose.airflow.yml ps

# View logs
docker-compose -f docker-compose.airflow.yml logs -f airflow-scheduler
docker-compose -f docker-compose.airflow.yml logs -f airflow-webserver

# Stop services
docker-compose -f docker-compose.airflow.yml down
```

**Airflow UI**: http://localhost:8080 (admin/admin)

### Managing DAGs

```bash
# List all DAGs
docker exec airflow-airflow-scheduler-1 airflow dags list

# Trigger a DAG manually
docker exec airflow-airflow-scheduler-1 airflow dags trigger agent_tsla_trading

# Check DAG status
docker exec airflow-airflow-scheduler-1 airflow dags list-runs -d agent_tsla_trading

# Pause/Unpause a DAG
docker exec airflow-airflow-scheduler-1 airflow dags pause agent_tsla_trading
docker exec airflow-airflow-scheduler-1 airflow dags unpause agent_tsla_trading

# Check for import errors
docker exec airflow-airflow-scheduler-1 airflow dags list-import-errors
```

### Active DAGs (13 Trading Agents)

**Stock DAGs (7)** - Market hours only (Mon-Fri, 9:30 AM - 4:00 PM EST):
1. **agent_tsla_trading** - TSLA sentiment-momentum (every 5 minutes)
2. **agent_iwm_trading** - IWM sentiment-momentum (every 15 minutes)
3. **agent_pltr_trading** - PLTR sentiment-momentum (every 15 minutes)
4. **agent_roku_trading** - ROKU sentiment-momentum (every 15 minutes)
5. **agent_net_trading** - NET sentiment-momentum (every 15 minutes)
6. **agent_snap_trading** - SNAP sentiment-momentum (every 15 minutes)
7. **agent_ddog_trading** - DDOG sentiment-momentum (every 15 minutes)

**Crypto DAGs (6)** - 24/7 trading:
8. **agent_btc_trading** - BTC/USD sentiment-momentum (every 60 minutes)
9. **agent_eth_trading** - ETH/USD sentiment-momentum (every 60 minutes)
10. **agent_sol_trading** - SOL/USD sentiment-momentum (every 60 minutes)
11. **agent_doge_trading** - DOGE/USD sentiment-momentum (every 60 minutes)
12. **agent_shib_trading** - SHIB/USD sentiment-momentum (every 60 minutes)
13. **agent_xrp_trading** - XRP/USD sentiment-momentum (every 60 minutes)

### Database Operations

```bash
# Run database migrations
docker exec airflow-airflow-scheduler-1 bash -c "cd /opt/airflow/ztrade && python db/migrate.py"

# Check database tables
docker exec airflow-postgres-1 psql -U airflow -d ztrade -c "\dt"

# View market data
docker exec airflow-postgres-1 psql -U airflow -d ztrade -c "SELECT symbol, timeframe, COUNT(*) as bar_count FROM market_bars GROUP BY symbol, timeframe;"

# Backfill historical data (stocks - Alpha Vantage)
docker exec airflow-airflow-scheduler-1 bash -c "cd /opt/airflow/ztrade && python db/backfill_historical_data.py --symbols TSLA IWM --timeframes 5m 15m 1h --days 60 --provider alphavantage"

# Backfill historical data (crypto - CoinGecko)
docker exec airflow-airflow-scheduler-1 bash -c "cd /opt/airflow/ztrade && python db/backfill_historical_data.py --symbols BTC/USD ETH/USD --timeframes 1h --days 90 --provider coingecko --no-sentiment"
```

### Backtesting (ARCHIVED - CLI commands no longer available)

Note: Backtesting functionality is currently archived. To use backtesting, you can:
1. Restore the CLI from `.archive/cli-old/`
2. Create new Airflow DAGs for backtesting workflows
3. Run backtest scripts directly: `python -m cli.commands.backtest ...`

---

## Documentation Index

### 📋 Architecture Decisions
- [ADR Index](docs/adr/README.md) - All architectural decisions
- [ADR-001](docs/adr/ADR-001-asset-based-architecture.md) - Asset-based agent architecture
- [ADR-002](docs/adr/ADR-002-multi-source-sentiment.md) - Multi-source sentiment analysis
- [ADR-003](docs/adr/ADR-003-performance-tracking.md) - Performance tracking system
- [ADR-004](docs/adr/ADR-004-continuous-trading-loops.md) - Continuous trading loops (ARCHIVED - replaced by Airflow)
- [ADR-006](docs/adr/ADR-006-containerization-strategy.md) - Docker & Kubernetes containerization
- [ADR-007](docs/adr/ADR-007-data-collection-backtesting.md) - Historical data collection & backtesting
- [ADR-008](docs/adr/ADR-008-finbert-sentiment-analysis.md) - FinBERT sentiment analysis
- [ADR-009](docs/adr/ADR-009-sentiment-driven-asset-selection.md) - Sentiment-driven asset selection
- [ADR-010](docs/adr/ADR-010-airflow-orchestration.md) - Airflow orchestration strategy (NEW)

### 📖 Guides
- [Airflow Operations Guide](docs/guides/airflow-operations.md) - Complete Airflow workflow guide (NEW)
- [Development Commands](docs/guides/development-commands.md) - All Docker/Airflow commands (UPDATED)
- [Common Tasks](docs/guides/common-tasks.md) - Step-by-step task guides (UPDATED)
- [Configuration](docs/guides/configuration.md) - Complete configuration reference
- [Dashboard Guide](docs/guides/dashboard-guide.md) - Real-time monitoring dashboard (ARCHIVED)
- [Docker Deployment](docs/guides/docker-deployment.md) - Containerized deployment guide (UPDATED)

### 🏗️ Architecture
- [Architecture Overview](docs/architecture/overview.md) - System design and data flow (UPDATED)

### 📝 Development Sessions
- [Session Index](docs/sessions/README.md) - All development session logs
- [2025-11-22](docs/sessions/2025-11-22-infrastructure-cleanup.md) - Airflow migration & cleanup (~3hrs, 31% code reduction)
- [2025-11-10 PM](docs/sessions/2025-11-10-backtest-debugging.md) - Backtest debugging (~2hrs, 2 files)
- [2025-11-10 AM](docs/sessions/2025-11-10-data-backtesting-docker.md) - Data collection + Docker (~3hrs, 13 files)
- [2025-11-08](docs/sessions/2025-11-08-sentiment-loops-celery.md) - Sentiment + Loops + Celery (~4.5hrs, 13 files)

---

## Key Architectural Principles

### 1. Airflow-Native Orchestration
- All trading workflows implemented as Airflow DAGs
- Task dependencies managed through Airflow operators
- XCom for inter-task data passing
- Built-in retry logic, scheduling, monitoring
- See: [ADR-010](docs/adr/ADR-010-airflow-orchestration.md)

### 2. Agent Autonomy
- Each agent operates independently with its own strategy and personality
- No inter-agent coordination required
- Clean ownership of positions and state
- See: [ADR-001](docs/adr/ADR-001-asset-based-architecture.md)

### 3. Multi-Layer Risk Management
- **Agent Level**: Position sizing, stop losses, daily trade limits
- **Company Level**: Total exposure caps, correlation monitoring, circuit breakers
- **Manual Override**: Company manager has final authority

### 4. Hybrid Decision-Making
- **Traditional TA**: Fast, deterministic (RSI, SMA, trend) - <10ms
- **Multi-Source Sentiment**: News (40%) + Reddit (25%) + SEC (25%)
- **Algorithmic Synthesis**: 60% sentiment + 40% technical weighted decision
- See: [ADR-002](docs/adr/ADR-002-multi-source-sentiment.md)

---

## Risk Management Rules (Non-Negotiable)

- **RULE_001**: No agent can exceed 10% of total capital
- **RULE_002**: Daily loss limit triggers immediate halt
- **RULE_003**: All trades must have stop losses
- **RULE_004**: Maximum 3 correlated positions (correlation > 0.7)
- **RULE_005**: Position size never exceeds 5% of capital
- **RULE_006**: No more than 80% capital deployed
- **RULE_007**: All decisions logged and auditable
- **RULE_008**: Manual override always available

---

## Development Workflow

### Adding a New Agent

1. **Create Agent Configuration**:
   ```bash
   mkdir -p agents/agent_newasset
   # Create context.yaml and personality.yaml
   ```

2. **Create Airflow DAG**:
   ```bash
   cp airflow/dags/agent_tsla_dag.py airflow/dags/agent_newasset_dag.py
   # Update AGENT_ID, ASSET, INTERVAL_MINUTES, schedule_interval
   ```

3. **Test DAG**:
   ```bash
   # Check for import errors
   docker exec airflow-airflow-scheduler-1 airflow dags list-import-errors

   # Trigger test run
   docker exec airflow-airflow-scheduler-1 airflow dags trigger agent_newasset_trading
   ```

4. **Monitor in Airflow UI**:
   - Navigate to http://localhost:8080
   - View DAG runs, task logs, execution times

**Detailed guide:** [docs/guides/common-tasks.md#adding-a-new-trading-agent](docs/guides/common-tasks.md#adding-a-new-trading-agent)

### Creating a New Airflow DAG

1. Create DAG file in `airflow/dags/`
2. Import Ztrade modules:
   ```python
   from ztrade.broker import get_broker
   from ztrade.market_data import get_market_data_provider
   from ztrade.decision.algorithmic import get_algorithmic_decision_maker
   from ztrade.execution.risk import RiskValidator
   from ztrade.execution.trade_executor import TradeExecutor
   from ztrade.core.config import get_config
   from ztrade.core.logger import get_logger
   ```
3. Define task functions using `**context` parameter
4. Use `context['task_instance'].xcom_push/pull()` for inter-task communication
5. Set up task dependencies with `>>` operator

### Creating an ADR

1. Use template in [docs/adr/README.md](docs/adr/README.md)
2. Document context, decision, rationale, consequences
3. Link from this file

---

## Agent Decision Flow (Airflow DAG)

```
1. Check market hours (TimeSensor or Python check)
2. Fetch market data (Alpaca API: quotes + bars) → XCom
3. Analyze sentiment (News + Reddit + SEC) → XCom
4. Perform technical analysis (RSI, SMA, trend, volume) → XCom
5. Make algorithmic decision (60% sentiment + 40% technical) → XCom
6. Validate decision against risk rules → XCom (approved/rejected)
7. Execute trade (if approved, or skip if HOLD/rejected) → XCom
8. Log performance metrics (database or monitoring system)
```

**Detailed flow:** [docs/architecture/overview.md#data-flow](docs/architecture/overview.md#data-flow)

---

## Environment Variables

Required in `airflow/.env`:
```bash
# Airflow settings
AIRFLOW_UID=50000
AIRFLOW_PROJ_DIR=.
_AIRFLOW_WWW_USER_USERNAME=admin
_AIRFLOW_WWW_USER_PASSWORD=admin

# Alpaca API (required for paper trading)
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Market Data Providers (at least one required)
ALPHAVANTAGE_API_KEY=your_key          # Alpha Vantage (stocks - free tier: 25 calls/day)
COINGECKO_API_KEY=your_key              # CoinGecko (crypto - free tier: 30 calls/min)

# Optional
ANTHROPIC_API_KEY=your_key              # For future AI-based decision modes
REDDIT_CLIENT_ID=your_id                # For Reddit sentiment
REDDIT_CLIENT_SECRET=your_secret        # For Reddit sentiment
REDDIT_USER_AGENT="Ztrade:v1.0"        # For Reddit sentiment
```

**Full configuration guide:** [docs/guides/configuration.md](docs/guides/configuration.md)

---

## Directory Structure

```
Ztrade/
├── ztrade/              # Core trading library (NEW - organized structure)
│   ├── sentiment/       # Multi-source sentiment analysis
│   │   ├── aggregator.py
│   │   ├── news.py
│   │   ├── reddit.py
│   │   ├── sec.py
│   │   └── finbert.py
│   ├── analysis/        # Technical analysis
│   │   ├── technical.py
│   │   └── improved_technical.py
│   ├── decision/        # Decision-making algorithms
│   │   ├── algorithmic.py
│   │   └── automated.py
│   ├── execution/       # Trade execution and risk
│   │   ├── risk.py
│   │   └── trade_executor.py
│   ├── core/            # Core infrastructure
│   │   ├── database.py
│   │   ├── config.py
│   │   └── logger.py
│   ├── broker.py
│   └── market_data.py
├── airflow/             # Apache Airflow orchestration
│   ├── dags/            # Trading DAGs (13 agents: 7 stocks + 6 crypto)
│   ├── logs/            # Airflow task logs
│   ├── config/          # Airflow configuration
│   ├── plugins/         # Custom Airflow plugins (future)
│   ├── docker-compose.airflow.yml
│   └── .env             # Airflow environment variables
├── agents/              # Trading agent configs (context, personality, state)
├── config/              # System configuration (company, risk, broker)
├── oversight/           # Risk management and monitoring
├── db/                  # Database migrations and scripts
├── logs/                # Structured logging (trades, decisions, system)
├── docs/                # Documentation (adr, sessions, guides, architecture)
├── .archive/            # Archived code (CLI, Celery, old Docker)
│   ├── cli-old/         # Old CLI commands and orchestration
│   └── docker-old/      # Old Docker and Celery infrastructure
└── CLAUDE.md            # This file
```

**Detailed structure:** [docs/architecture/overview.md#directory-structure](docs/architecture/overview.md#directory-structure)

---

## Dependencies

**Core:**
- `apache-airflow>=2.7.0` - Workflow orchestration
- `alpaca-py>=0.9.0` - Alpaca trading + news API
- `redis>=7.0.1` - Message broker for Airflow
- `psycopg2-binary>=2.9.0` - PostgreSQL adapter

**Analysis:**
- `vaderSentiment>=3.3.2` - Sentiment analysis
- `transformers>=4.30.0` - FinBERT model
- `torch>=2.0.0` - PyTorch for FinBERT
- `praw>=7.7.1` - Reddit API wrapper
- `pandas>=2.0.0`, `numpy>=1.24.0` - Data analysis
- `yfinance==0.2.40` - Yahoo Finance fallback

**Full dependency list:** [requirements.txt](requirements.txt)

---

## References

- **Project README**: [README.md](README.md) - Getting started guide
- **Trading Plan**: [trading_company_plan.md](trading_company_plan.md) - Complete system design
- **Airflow Documentation**: https://airflow.apache.org/docs/

---

## Code Patterns

### Using Multi-Source Sentiment

```python
from ztrade.sentiment.aggregator import get_sentiment_aggregator

aggregator = get_sentiment_aggregator()
sentiment = aggregator.get_aggregated_sentiment("TSLA")

# Returns: score, confidence, sources_used, agreement_level, source_breakdown
```

### Creating an Airflow Task

```python
from airflow.operators.python import PythonOperator

def my_task_function(**context):
    """Task function with context."""
    ti = context['task_instance']

    # Pull data from previous task
    data = ti.xcom_pull(task_ids='previous_task', key='my_key')

    # Do work
    result = process_data(data)

    # Push result for next task
    ti.xcom_push(key='result', value=result)

    return result

# Create task in DAG
task = PythonOperator(
    task_id='my_task',
    python_callable=my_task_function,
    dag=dag,
)
```

### Importing Ztrade Modules in DAGs

```python
import sys
sys.path.insert(0, '/opt/airflow/ztrade')

from ztrade.broker import get_broker
from ztrade.market_data import get_market_data_provider
from ztrade.decision.algorithmic import get_algorithmic_decision_maker
from ztrade.execution.risk import RiskValidator
from ztrade.execution.trade_executor import TradeExecutor
from ztrade.core.config import get_config
from ztrade.core.logger import get_logger
```

**More patterns:** [docs/guides/common-tasks.md](docs/guides/common-tasks.md)

---

## Current Focus (2025-11-30)

- ✅ **Completed Recently**:
  - **Portfolio Expansion**: Added 10 new trading agents (6 crypto + 4 stocks) - now 13 total agents
  - **Agent Diversity**:
    - Stocks: TSLA, IWM, PLTR, ROKU, NET, SNAP, DDOG (7 agents)
    - Crypto: BTC, ETH, SOL, DOGE, SHIB, XRP (6 agents)
  - **24/7 Coverage**: Crypto agents provide continuous market exposure
  - **Sector Diversification**: Tech, streaming, cloud, social media, DeFi, meme coins
  - **Infrastructure Cleanup** (2025-11-22): Migrated from CLI/Celery to Airflow-only orchestration
  - **Code Reorganization** (2025-11-22): Created new `ztrade/` package (31% code reduction)

- 🎯 **Next**:
  - **Backtest All Agents**: Validate sentiment alpha for all 10 new agents
  - **Data Collection**: Backfill historical data for all assets (60-90 days)
  - **Risk Correlation Analysis**: Ensure portfolio diversification
  - **Multi-Agent Monitoring**: Track all 13 agents simultaneously in Airflow UI
  - **Performance Comparison**: Compare sentiment alpha across asset classes

- 📊 **Goal**:
  - Validate all 13 agents through backtesting
  - 3-6 months paper trading validation before any live trading
  - Target portfolio: $130K allocated across 13 agents ($10K each)

---

## Notes for Claude Code

- **Always use paper trading** - `ALPACA_BASE_URL` must be paper trading endpoint
- **Never skip risk validation** - All trades must pass risk checks
- **Document architectural decisions** - Create ADRs for significant changes
- **Test in Airflow first** - Use Airflow UI to manually trigger and test DAGs
- **Update documentation** - Keep guides and ADRs current with code changes
- **Follow the plan** - See [trading_company_plan.md](trading_company_plan.md) for development phases
- **Airflow best practices**:
  - Use XCom for small data only (<1MB)
  - Implement idempotent tasks (can be retried safely)
  - Set appropriate retries and retry delays
  - Use task dependencies (`>>`) for workflow clarity
  - Monitor Airflow UI for errors and performance

---

## Archived Components

The following components have been archived but are not deleted. They can be restored from `.archive/` if needed:

**Archived (2025-11-22)**:
- CLI commands (`cli/commands/`) - 1,992 lines
- Celery orchestration (`celery_app.py`) - 378 lines
- Loop manager (`cli/utils/loop_manager.py`) - 321 lines
- Subagent mode (`cli/utils/subagent.py`) - 144 lines
- Old Docker infrastructure (7 containers)
- Dashboard scripts (`run_dashboard.sh`)
- Trading startup scripts (`start_trading_at_market_open.sh`)

**Total Archived**: ~2,835 lines of code (31% reduction)

**Reason**: Replaced by Airflow DAG-based orchestration for better observability, reliability, and maintainability.

---

**Last Updated**: 2025-11-30
**Documentation Version**: 4.1 (Portfolio Expansion)
- **New**: Expanded from 3 to 13 trading agents (7 stocks + 6 crypto)
- **New**: Added sector diversification (tech, streaming, cloud, social, DeFi, meme)
- **New**: 24/7 trading coverage with crypto agents
- Migrated from CLI/Celery to Airflow orchestration (2025-11-22)
- Reorganized codebase into `ztrade/` package (31% code reduction)
- All 13 trading DAGs configured and ready for validation
