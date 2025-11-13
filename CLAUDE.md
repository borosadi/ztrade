# CLAUDE.md

This file provides quick-reference guidance to Claude Code when working with this repository.

---

## Project Overview

**Ztrade** is an AI-powered autonomous trading system where multiple AI agents trade different assets independently. Each agent has its own strategy, risk profile, and personality, operating under company-wide risk management and oversight.

**Key Technologies:**
- **AI**: Claude Code subagents (no API key required) for trading decisions
- **Broker**: Alpaca API (paper trading via alpaca-py)
- **Market Data**: Alpaca API (real-time) + Yahoo Finance (fallback)
- **Orchestration**: Celery + Redis + Flower
- **CLI**: Python Click framework
- **Language**: Python 3.10+

---

## Current System Status (Updated 2025-11-13)

### Active Trading Agents (3)

| Agent | Asset | Strategy | Timeframe | Risk | Capital | Status | Sentiment Alpha |
|-------|-------|----------|-----------|------|---------|--------|----------------|
| **agent_tsla** | TSLA | Momentum | 5-min | Aggressive (3% SL) | $10,000 | ✅ Validated | 10-15% (proven: 91.2% win rate) |
| **agent_iwm** | IWM | Sentiment-Momentum | 15-min | Mod-Aggressive (2.5% SL) | $10,000 | 🆕 Ready | 20-30% (small-cap edge) |
| **agent_btc** | BTC/USD | Sentiment-Momentum | 1-hour | Aggressive (4% SL) | $10,000 | 🆕 Ready | 40-60% (crypto edge, 24/7) |

### Archived Agents (Removed - No Sentiment Edge)

| Agent | Asset | Archived | Reason |
|-------|-------|----------|--------|
| agent_spy | SPY | 2025-11-13 | HFT-dominated, 0% sentiment edge |
| agent_aapl | AAPL | 2025-11-13 | Mega-cap, limited edge |

**Strategy**: Trade only where sentiment creates exploitable edge. Avoid HFT-dominated markets.

### System Capabilities

**✅ Working:**
- Real-time market data (Alpaca API)
- Multi-source sentiment analysis (News + Reddit + SEC)
- **✅ FinBERT sentiment analysis**
  - Domain-specific financial sentiment (ProsusAI/finbert)
  - VADER-compatible API for drop-in replacement
  - Batch processing support
  - GPU acceleration (CUDA/MPS)
- Performance tracking for sentiment sources
- Continuous autonomous trading loops
- Traditional technical analysis (RSI, SMA, trend, volume, support/resistance)
- Hybrid decision-making (TA + Sentiment + AI synthesis)
- Claude Code subagent decisions (file-based, 60s timeout)
- Risk validation and circuit breakers
- Paper trading execution
- Celery orchestration with Flower web UI
- Real-time web dashboard (Streamlit at http://localhost:8501)
- Historical data collection (PostgreSQL with 10,735 bars across 3 symbols)
- **✅ Backtesting framework (FULLY FUNCTIONAL)**
  - Event-driven portfolio simulation
  - 100-bar trend analysis (captures 8-hour trends on 5m timeframe)
  - Directional signal synthesis (ignores neutral noise)
  - Smart position sizing (handles % and $ configs)
  - Type-safe calculations (Decimal → float conversions)
  - TSLA validation: 34 trades, 91.2% win rate, 8.51% return
- Full Docker containerization (7 services: postgres, redis, trading, worker, beat, flower, dashboard)

**📋 Strategic Initiatives:**
- **IWM Validation**: Backtest IWM to validate 20-30% sentiment alpha hypothesis
- **BTC Validation**: Backtest BTC to validate 40-60% crypto sentiment edge
- **ETH Expansion**: Add Ethereum agent (DeFi sentiment, 24/7 trading)
- **Mid-Cap Rotation**: Test rotating between 3-5 mid-caps based on sentiment heat
- Multi-agent simultaneous trading (TSLA + IWM + BTC concurrently)
- Strategy optimization and walk-forward testing

---

## Quick Start

### Running Agents

```bash
# Run TSLA agent (proven winner)
uv run ztrade agent run agent_tsla --subagent --dry-run

# Run IWM agent (small-cap sentiment edge)
uv run ztrade agent run agent_iwm --subagent --dry-run

# Run BTC agent (crypto sentiment edge, 24/7)
uv run ztrade agent run agent_btc --subagent --dry-run

# Start continuous loops (production)
uv run ztrade loop start agent_tsla
uv run ztrade loop start agent_iwm
uv run ztrade loop start agent_btc

# Celery orchestration (all agents)
./celery_control.sh start
# Web UI: http://localhost:5555
```

### Monitoring Dashboard

```bash
# Start real-time web dashboard
./run_dashboard.sh
# Dashboard: http://localhost:8501

# Or manually
uv run streamlit run dashboard.py
```

### Common Commands

```bash
# Agent management
uv run ztrade agent list
uv run ztrade agent status agent_spy

# Company overview
uv run ztrade company dashboard
uv run ztrade company positions

# Risk monitoring
uv run ztrade risk status
uv run ztrade risk correlations

# Loop control
uv run ztrade loop status
uv run ztrade loop stop agent_spy

# Backtesting (FULLY FUNCTIONAL ✅)
uv run ztrade backtest run agent_tsla --start 2025-09-10 --end 2025-11-10
uv run ztrade backtest list --limit 10
uv run ztrade backtest show 8 --trades
uv run ztrade backtest compare 6 7 8

# Database & Data Collection
python db/backfill_historical_data.py --days 60 --timeframes 5m 15m 1h 1d
python db/migrate.py                  # Run pending migrations
```

**Full command reference:** [docs/guides/development-commands.md](docs/guides/development-commands.md)

---

## Documentation Index

### 📋 Architecture Decisions
- [ADR Index](docs/adr/README.md) - All architectural decisions
- [ADR-001](docs/adr/ADR-001-asset-based-architecture.md) - Asset-based agent architecture
- [ADR-002](docs/adr/ADR-002-multi-source-sentiment.md) - Multi-source sentiment analysis
- [ADR-003](docs/adr/ADR-003-performance-tracking.md) - Performance tracking system
- [ADR-004](docs/adr/ADR-004-continuous-trading-loops.md) - Continuous trading loops
- [ADR-006](docs/adr/ADR-006-containerization-strategy.md) - Docker & Kubernetes containerization
- [ADR-007](docs/adr/ADR-007-data-collection-backtesting.md) - Historical data collection & backtesting
- [ADR-008](docs/adr/ADR-008-finbert-sentiment-analysis.md) - FinBERT sentiment analysis
- [ADR-009](docs/adr/ADR-009-sentiment-driven-asset-selection.md) - Sentiment-driven asset selection (small-caps vs large-caps)

### 📖 Guides
- [Development Commands](docs/guides/development-commands.md) - All CLI commands and workflows
- [Common Tasks](docs/guides/common-tasks.md) - Step-by-step task guides
- [Configuration](docs/guides/configuration.md) - Complete configuration reference
- [Dashboard Guide](docs/guides/dashboard-guide.md) - Real-time monitoring dashboard
- [Docker Deployment](docs/guides/docker-deployment.md) - Containerized deployment guide

### 🏗️ Architecture
- [Architecture Overview](docs/architecture/overview.md) - System design and data flow

### 📝 Development Sessions
- [Session Index](docs/sessions/README.md) - All development session logs
- [2025-11-10 PM](docs/sessions/2025-11-10-backtest-debugging.md) - Backtest debugging (~2hrs, 2 files)
- [2025-11-10 AM](docs/sessions/2025-11-10-data-backtesting-docker.md) - Data collection + Docker (~3hrs, 13 files)
- [2025-11-08](docs/sessions/2025-11-08-sentiment-loops-celery.md) - Sentiment + Loops + Celery (~4.5hrs, 13 files)

---

## Key Architectural Principles

### 1. Agent Autonomy
- Each agent operates independently with its own strategy and personality
- No inter-agent coordination required
- Clean ownership of positions and state
- See: [ADR-001](docs/adr/ADR-001-asset-based-architecture.md)

### 2. Multi-Layer Risk Management
- **Agent Level**: Position sizing, stop losses, daily trade limits
- **Company Level**: Total exposure caps, correlation monitoring, circuit breakers
- **Manual Override**: Company manager has final authority

### 3. Hybrid Decision-Making
- **Traditional TA**: Fast, deterministic (RSI, SMA, trend) - <10ms
- **Multi-Source Sentiment**: News (40%) + Reddit (25%) + SEC (25%)
- **AI Synthesis**: Claude Code subagent combines signals for final decision
- See: [ADR-002](docs/adr/ADR-002-multi-source-sentiment.md)

### 4. Subagent Communication
- File-based requests/responses (`oversight/subagent_requests/`, `oversight/subagent_responses/`)
- 60-second timeout for decisions
- No API keys required (uses Claude Code terminal access)
- Complete context provided: market data, sentiment, agent state, personality

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
1. Create agent directory and config files
2. Define strategy and personality
3. Test with dry-run mode
4. Paper trade before live trading

**Detailed guide:** [docs/guides/common-tasks.md#adding-a-new-trading-agent](docs/guides/common-tasks.md#adding-a-new-trading-agent)

### Implementing a New Feature
1. Check if an ADR is needed (significant architectural decision)
2. Create feature branch
3. Implement with tests
4. Update documentation
5. Create pull request

### Creating an ADR
1. Use template in [docs/adr/README.md](docs/adr/README.md)
2. Document context, decision, rationale, consequences
3. Link from this file

---

## Agent Decision Flow (Subagent Mode)

```
1. Fetch market data (Alpaca API: quotes + bars)
2. Run technical analysis (RSI, SMA, trend, volume)
3. Fetch multi-source sentiment (News + Reddit + SEC)
4. Create decision request file
5. Wait for Claude Code subagent response (60s timeout)
6. Subagent analyzes context + personality → decision
7. Validate decision against risk rules
8. Execute trade (or simulate in dry-run)
9. Log decision and track performance
```

**Detailed flow:** [docs/architecture/overview.md#data-flow](docs/architecture/overview.md#data-flow)

---

## Environment Variables

Required in `.env`:
```bash
# Alpaca API (required)
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Optional
ANTHROPIC_API_KEY=your_key              # Only for automated mode
REDDIT_CLIENT_ID=your_id                # For Reddit sentiment
REDDIT_CLIENT_SECRET=your_secret        # For Reddit sentiment
REDDIT_USER_AGENT="Ztrade:v1.0"        # For Reddit sentiment
```

**Full configuration guide:** [docs/guides/configuration.md](docs/guides/configuration.md)

---

## Directory Structure

```
Ztrade/
├── agents/              # Trading agent configs (context, personality, state)
├── cli/                 # CLI implementation (commands + utils)
├── config/              # System configuration (company, risk, broker)
├── oversight/           # Risk management and monitoring
├── logs/                # Structured logging (trades, decisions, system)
├── docs/                # Documentation (adr, sessions, guides, architecture)
├── celery_app.py        # Celery task orchestration
├── celery_control.sh    # Celery management script
└── CLAUDE.md            # This file
```

**Detailed structure:** [docs/architecture/overview.md#directory-structure](docs/architecture/overview.md#directory-structure)

---

## Dependencies

**Core:**
- `alpaca-py>=0.9.0` - Alpaca trading + news API
- `click>=8.1.0` - CLI framework
- `celery>=5.5.3` - Task orchestration
- `flower>=2.0.1` - Web monitoring UI
- `redis>=7.0.1` - Message broker

**Analysis:**
- `vaderSentiment>=3.3.2` - Sentiment analysis
- `praw>=7.7.1` - Reddit API wrapper
- `pandas>=2.0.0`, `numpy>=1.24.0` - Data analysis
- `yfinance==0.2.40` - Yahoo Finance fallback

**Full dependency list:** [requirements.txt](requirements.txt)

---

## References

- **Project README**: [README.md](README.md) - Getting started guide
- **Trading Plan**: [trading_company_plan.md](trading_company_plan.md) - Complete system design
- **Gemini Notes**: [GEMINI.md](GEMINI.md) - Alternative AI integration notes
- **Celery Setup**: [CELERY_SETUP.md](CELERY_SETUP.md) - Celery orchestration guide

---

## Code Patterns

### Using Multi-Source Sentiment

```python
from cli.utils.sentiment_aggregator import get_sentiment_aggregator

aggregator = get_sentiment_aggregator()
sentiment = aggregator.get_aggregated_sentiment("TSLA")

# Returns: score, confidence, sources_used, agreement_level, source_breakdown
```

### Tracking Performance

```python
from cli.utils.performance_tracker import get_performance_tracker

tracker = get_performance_tracker()
trade_id = tracker.log_trade_with_sentiment(...)
tracker.log_trade_outcome(trade_id, ...)
report = tracker.generate_report(lookback_days=30)
```

**More patterns:** [docs/guides/common-tasks.md](docs/guides/common-tasks.md)

---

## Current Focus (2025-11-10 PM)

- ✅ **Completed Today**:
  - **AM Session**: Historical data collection + backtesting framework + Docker containerization
  - **PM Session**: Backtesting system debugging - 4 critical bugs fixed
    - ✅ Trend analysis: 10 bars → 100 bars lookback
    - ✅ Type conversions: Decimal → float handling
    - ✅ Signal synthesis: Ignore neutral signals
    - ✅ Position sizing: Handle % and $ configs
  - **Result**: TSLA backtest: 34 trades, 91.2% win rate, 8.51% return ✅
- 🎯 **Next**:
  - Strategy optimization and parameter tuning
  - Multi-timeframe analysis (5m + 1h + 1d aggregation)
  - Walk-forward testing and Monte Carlo simulation
  - Multi-agent simultaneous trading
- 📊 **Goal**: 3-6 months paper trading validation before any live trading

---

## Notes for Claude Code

- **Always use paper trading** - `ALPACA_BASE_URL` must be paper trading endpoint
- **Never skip risk validation** - All trades must pass risk checks
- **Document architectural decisions** - Create ADRs for significant changes
- **Test before deploying** - Use dry-run mode, then paper trading
- **Update documentation** - Keep guides and ADRs current with code changes
- **Follow the plan** - See [trading_company_plan.md](trading_company_plan.md) for development phases

---

**Last Updated**: 2025-11-10
**Documentation Version**: 2.1 (Data Collection + Backtesting)
- Backtest Debugging