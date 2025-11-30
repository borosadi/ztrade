# Ztrade

[![CI](https://github.com/YOUR_USERNAME/ztrade/workflows/CI/badge.svg)](https://github.com/YOUR_USERNAME/ztrade/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI-powered autonomous trading system with Apache Airflow orchestration**

Ztrade is a fully autonomous trading platform where multiple AI agents trade different assets independently. Each agent has its own strategy, risk profile, and personality, operating under company-wide risk management.

## Key Features

- 🔄 **Apache Airflow Orchestration** - DAG-based workflow automation
- 🤖 **Multi-Agent Trading** - Independent agents for TSLA, IWM, BTC/USD
- 📊 **Multi-Source Sentiment** - News + Reddit + SEC + FinBERT analysis
- 📈 **Technical Analysis** - RSI, SMA, trend detection, volume analysis
- 🛡️ **Risk Management** - Multi-layer validation and circuit breakers
- 📦 **Full Containerization** - Docker Compose for easy deployment
- 💾 **PostgreSQL Database** - Historical data storage and backtesting
- 🎯 **Paper Trading** - Alpaca API for safe testing

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Apache Airflow                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ TSLA DAG │  │ IWM DAG  │  │  BTC DAG │                 │
│  │ (5-min)  │  │ (15-min) │  │ (1-hour) │                 │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                 │
└───────┼─────────────┼─────────────┼────────────────────────┘
        │             │             │
        └─────────────┴─────────────┘
                      │
        ┌─────────────┴──────────────┐
        │      Ztrade Library         │
        │  ┌──────────────────────┐  │
        │  │ Sentiment Analysis   │  │
        │  │ Technical Analysis   │  │
        │  │ Risk Validation      │  │
        │  │ Trade Execution      │  │
        │  └──────────────────────┘  │
        └────────────┬────────────────┘
                     │
        ┌────────────┴────────────┐
        │    Alpaca Broker API     │
        │    (Paper Trading)       │
        └──────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- Alpaca API keys (free paper trading account)
- Optional: Alpha Vantage, CoinGecko, Reddit API keys

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/ztrade.git
cd ztrade
```

### 2. Configure Environment

```bash
# Copy environment template
cp airflow/.env.example airflow/.env

# Edit airflow/.env and add your API keys:
# - ALPACA_API_KEY
# - ALPACA_SECRET_KEY
# - ALPHAVANTAGE_API_KEY (optional)
# - COINGECKO_API_KEY (optional)
# - REDDIT_CLIENT_ID/SECRET (optional)
```

### 3. Start Airflow

```bash
cd airflow
docker-compose -f docker-compose.airflow.yml up -d
```

**Airflow UI**: http://localhost:8080 (admin/admin)

### 4. View Trading DAGs

Navigate to Airflow UI and enable the DAGs:
- **agent_tsla_trading** - Tesla momentum trading (every 5 minutes, 9 AM-4 PM EST)
- **agent_iwm_trading** - Russell 2000 sentiment trading (every 15 minutes, 9 AM-4 PM EST)
- **agent_btc_trading** - Bitcoin 24/7 trading (every 60 minutes)

### 5. Monitor Trading

Click on any DAG to view:
- Task execution status
- XCom data passed between tasks
- Logs for each trading decision
- Performance metrics

## Trading DAG Workflow

Each trading DAG follows this pipeline:

```
1. Check Market Hours
   ↓
2. Fetch Market Data (Alpaca API)
   ↓
3. Analyze Sentiment (News + Reddit + SEC)
   ↓
4. Technical Analysis (RSI, SMA, trend, volume)
   ↓
5. Make Decision (60% sentiment + 40% technical)
   ↓
6. Validate Risk (position size, stop loss, limits)
   ↓
7. Execute Trade (if approved)
   ↓
8. Log Performance
```

## Active Trading Agents

| Agent | Asset | Strategy | Timeframe | Capital | Status |
|-------|-------|----------|-----------|---------|--------|
| **agent_tsla** | TSLA | Momentum | 5-min | $10,000 | ✅ Validated (91.2% win rate) |
| **agent_iwm** | IWM | Sentiment-Momentum | 15-min | $10,000 | 🆕 Ready |
| **agent_btc** | BTC/USD | Sentiment-Momentum | 1-hour | $10,000 | 🆕 Ready (24/7) |

## Managing the System

### Start/Stop Airflow

```bash
# Start all services
cd airflow
docker-compose -f docker-compose.airflow.yml up -d

# Stop all services
docker-compose -f docker-compose.airflow.yml down

# View logs
docker-compose -f docker-compose.airflow.yml logs -f airflow-scheduler
```

### Trigger DAGs Manually

```bash
# Trigger TSLA trading cycle
docker exec airflow-airflow-scheduler-1 airflow dags trigger agent_tsla_trading

# Check DAG status
docker exec airflow-airflow-scheduler-1 airflow dags list

# View recent DAG runs
docker exec airflow-airflow-scheduler-1 airflow dags list-runs -d agent_tsla_trading
```

### Database Operations

```bash
# Run migrations
docker exec airflow-airflow-scheduler-1 bash -c "cd /opt/airflow/ztrade && python db/migrate.py"

# View market data
docker exec airflow-postgres-1 psql -U airflow -d ztrade -c "SELECT symbol, COUNT(*) FROM market_bars GROUP BY symbol;"

# Backfill historical data
docker exec airflow-airflow-scheduler-1 bash -c "cd /opt/airflow/ztrade && python db/backfill_historical_data.py --symbols TSLA IWM --timeframes 5m 15m --days 60 --provider alphavantage"
```

## Development

### Project Structure

```
Ztrade/
├── ztrade/              # Core trading library
│   ├── sentiment/       # Multi-source sentiment analysis
│   ├── analysis/        # Technical indicators
│   ├── decision/        # Trading algorithms
│   ├── execution/       # Trade execution & risk
│   └── core/            # Config, database, logging
├── airflow/             # Airflow orchestration
│   ├── dags/            # Trading DAGs
│   ├── docker-compose.airflow.yml
│   └── .env             # API keys
├── agents/              # Agent configurations
├── config/              # System configuration
└── db/                  # Database migrations
```

### Adding a New Trading Agent

1. **Create Agent Config**:
   ```bash
   mkdir -p agents/agent_newasset
   # Create context.yaml and personality.yaml
   ```

2. **Create DAG**:
   ```bash
   cp airflow/dags/agent_tsla_dag.py airflow/dags/agent_newasset_dag.py
   # Update AGENT_ID, ASSET, schedule_interval
   ```

3. **Test**:
   ```bash
   # Check for errors
   docker exec airflow-airflow-scheduler-1 airflow dags list-import-errors

   # Trigger test run
   docker exec airflow-airflow-scheduler-1 airflow dags trigger agent_newasset_trading
   ```

### Using Ztrade Library

```python
# In your Airflow DAG
import sys
sys.path.insert(0, '/opt/airflow/ztrade')

from ztrade.broker import get_broker
from ztrade.market_data import get_market_data_provider
from ztrade.sentiment.aggregator import get_sentiment_aggregator
from ztrade.analysis.technical import TechnicalAnalyzer
from ztrade.decision.algorithmic import get_algorithmic_decision_maker
from ztrade.execution.risk import RiskValidator
from ztrade.execution.trade_executor import TradeExecutor

# Get broker
broker = get_broker()
quote = broker.get_latest_quote("TSLA")

# Analyze sentiment
aggregator = get_sentiment_aggregator()
sentiment = aggregator.get_aggregated_sentiment("TSLA")

# Make decision
decision_maker = get_algorithmic_decision_maker(
    sentiment_weight=0.6,
    technical_weight=0.4
)
decision = decision_maker.make_decision(
    sentiment_score=sentiment['score'],
    sentiment_confidence=sentiment['confidence'],
    technical_signal='buy',
    technical_confidence=0.8,
    current_price=quote['ask'],
    agent_config=config
)
```

### Running Tests

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run black .

# Lint
uv run ruff check .
```

## Risk Management

All agents operate under strict risk management rules:

- ✅ Maximum 10% capital per agent
- ✅ All trades have stop losses
- ✅ Daily loss limits with automatic halts
- ✅ Maximum 80% capital deployed
- ✅ Correlation monitoring (max 3 correlated positions)
- ✅ Position size caps (5% max)
- ✅ Full audit logging

## Backtesting

Historical backtesting framework available (currently archived with CLI):

```bash
# Note: Restore from .archive/cli-old/ to use

# Run backtest
python -m cli.commands.backtest run agent_tsla --start 2025-09-10 --end 2025-11-10

# View results
python -m cli.commands.backtest list
python -m cli.commands.backtest show <id> --trades
```

**Future**: Backtesting will be reimplemented as Airflow DAGs.

## Monitoring

### Airflow UI

- DAG runs and task status: http://localhost:8080
- Task logs and XCom data
- Execution times and retries
- Error tracking

### Database Queries

```sql
-- View recent trades
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;

-- View sentiment history
SELECT * FROM sentiment_history WHERE symbol = 'TSLA' ORDER BY timestamp DESC LIMIT 20;

-- View backtest results
SELECT * FROM backtest_runs ORDER BY end_date DESC;
```

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Complete architecture and development guide
- **[Trading Plan](trading_company_plan.md)** - System design and strategy
- **[ADRs](docs/adr/)** - Architectural decision records
- **[Guides](docs/guides/)** - Step-by-step task guides
- **[Sessions](docs/sessions/)** - Development session logs

## Technology Stack

- **Orchestration**: Apache Airflow 2.7+
- **Language**: Python 3.10+
- **Broker**: Alpaca API (alpaca-py)
- **Database**: PostgreSQL
- **Message Broker**: Redis
- **Sentiment**: VADER, FinBERT (transformers), Reddit (praw)
- **Analysis**: pandas, numpy, TA-Lib
- **Deployment**: Docker Compose

## Recent Changes (2025-11-22)

- ✅ Migrated from CLI/Celery to Airflow orchestration
- ✅ Reorganized codebase into `ztrade/` package (31% code reduction)
- ✅ Removed 7 old Docker containers (~6.8 GB cleanup)
- ✅ All CLI/Celery code preserved in `.archive/`
- ✅ 3 active trading DAGs verified operational

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details

## Disclaimer

**This is paper trading only.** Do not use with real money without extensive testing and validation. Past performance does not guarantee future results. Trading involves risk of loss.

## Support

- 📖 [Documentation](CLAUDE.md)
- 🐛 [Issues](https://github.com/YOUR_USERNAME/ztrade/issues)
- 💬 [Discussions](https://github.com/YOUR_USERNAME/ztrade/discussions)

---

**Status**: ✅ Operational (Paper Trading Mode)
**Last Updated**: 2025-11-22
**Version**: 4.0 (Airflow Migration)
