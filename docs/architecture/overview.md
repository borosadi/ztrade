# Architecture Overview

High-level overview of the Ztrade trading system architecture.

---

## System Design

The system uses a hierarchical architecture:

```
You (Company Manager) → CLI Commands
         ↓
Trading Company System (Risk Manager & Oversight)
         ↓
    Trading Agents (agent_spy, agent_tsla, agent_aapl)
         ↓
External Services (Alpaca API + News + Reddit + SEC)
```

---

## Core Principles

### 1. Agent Autonomy
Each agent operates independently with:
- **Specialization**: Single asset focus with specific strategy
- **Autonomy**: Independent market analysis and trade decisions
- **Accountability**: All decisions logged with rationale
- **Personality**: Distinct decision-making style

### 2. Multi-Layer Risk Management
- **Agent Level**: Position sizing, stop losses, daily limits
- **Company Level**: Total exposure, correlation monitoring, circuit breakers
- **Manual Override**: Company manager has final authority

### 3. Hybrid Decision-Making
- **Traditional TA**: Fast, deterministic technical analysis (RSI, SMA, trend)
- **Multi-Source Sentiment**: News + Reddit + SEC filings aggregation
- **AI Synthesis**: Claude Code subagents combine signals for final decisions

---

## Directory Structure

```
Ztrade/
├── agents/              # Trading agent configurations
│   ├── agent_spy/
│   │   ├── context.yaml
│   │   ├── personality.md
│   │   ├── state.json
│   │   ├── performance.json
│   │   └── learning.json
│   ├── agent_tsla/
│   └── agent_aapl/
│
├── cli/                 # Command-line interface
│   ├── main.py
│   ├── commands/        # Command groups
│   │   ├── agent.py
│   │   ├── company.py
│   │   ├── loop.py
│   │   ├── monitor.py
│   │   └── risk.py
│   └── utils/           # Utilities
│       ├── broker.py
│       ├── market_data.py
│       ├── sentiment_aggregator.py
│       ├── news_analyzer.py
│       ├── reddit_analyzer.py
│       ├── sec_analyzer.py
│       ├── performance_tracker.py
│       ├── technical_analyzer.py
│       ├── loop_manager.py
│       └── subagent.py
│
├── config/              # System configuration
│   ├── company_config.yaml
│   ├── risk_limits.yaml
│   └── broker_config.yaml
│
├── oversight/           # Risk and monitoring
│   ├── subagent_requests/
│   ├── subagent_responses/
│   ├── sentiment_performance/
│   ├── loop_state/
│   ├── daily_reports/
│   └── audit_log.json
│
├── logs/                # Structured logging
│   ├── trades/
│   ├── agent_decisions/
│   └── system/
│
├── docs/                # Documentation
│   ├── adr/             # Architecture decisions
│   ├── sessions/        # Development logs
│   ├── guides/          # How-to guides
│   └── architecture/    # Architecture docs
│
├── celery_app.py        # Celery task orchestration
├── celery_control.sh    # Celery management script
└── CLAUDE.md            # Project overview for Claude Code
```

---

## Data Flow

### Trading Cycle Flow

```
1. Market Data Fetch
   ├─ Alpaca API (real-time quotes + historical bars)
   └─ Technical Analysis (RSI, SMA, trend, volume)
        ↓
2. Sentiment Analysis
   ├─ News (Alpaca/Benzinga) - 40% weight
   ├─ Reddit (r/wallstreetbets, r/stocks) - 25% weight
   └─ SEC (EDGAR filings) - 25% weight
        ↓
3. Decision Request
   ├─ Create request file (oversight/subagent_requests/)
   └─ Wait for subagent response (60s timeout)
        ↓
4. Claude Code Subagent
   ├─ Read agent context + personality
   ├─ Analyze market data + sentiment
   └─ Generate trading decision
        ↓
5. Risk Validation
   ├─ Check confidence threshold
   ├─ Validate position size
   ├─ Check daily limits
   └─ Verify correlation limits
        ↓
6. Trade Execution
   ├─ Submit order to Alpaca (or simulate in dry-run)
   └─ Update agent state
        ↓
7. Logging & Tracking
   ├─ Log decision to agent_decisions/
   ├─ Log trade to trades/
   ├─ Track sentiment performance
   └─ Update performance metrics
```

---

## Component Responsibilities

### CLI Layer (`cli/`)
- **Purpose**: User interface and command orchestration
- **Key Components**:
  - Command groups (agent, company, risk, monitor, loop)
  - Input validation and argument parsing
  - Output formatting and display

### Utilities Layer (`cli/utils/`)
- **Purpose**: Reusable business logic
- **Key Components**:
  - Market data fetching and technical analysis
  - Multi-source sentiment aggregation
  - Broker API integration
  - Performance tracking
  - Loop management and scheduling

### Agent Layer (`agents/`)
- **Purpose**: Trading agent configurations and state
- **Key Components**:
  - Agent personality and strategy definitions
  - State persistence (positions, P&L, trade count)
  - Performance history
  - Learning data

### Oversight Layer (`oversight/`)
- **Purpose**: Risk management and monitoring
- **Key Components**:
  - Subagent request/response communication
  - Performance tracking data
  - Loop state persistence
  - Audit logs and compliance

### Configuration Layer (`config/`)
- **Purpose**: System-wide settings
- **Key Components**:
  - Company capital and risk limits
  - Broker credentials and settings
  - Risk management rules

---

## Technology Stack

### Core Technologies
- **Language**: Python 3.10+
- **CLI Framework**: Click
- **AI**: Claude Code subagents (no API key required)
- **Broker**: Alpaca API (paper trading)
- **Orchestration**: Celery + Redis + Flower

### Data Sources
- **Market Data**: Alpaca API (primary), yfinance (fallback)
- **News**: Alpaca News API (Benzinga)
- **Reddit**: PRAW (Python Reddit API Wrapper)
- **SEC**: EDGAR API

### Analysis Libraries
- **Sentiment**: VADER Sentiment
- **Technical**: pandas, numpy (custom technical_analyzer.py)
- **Performance**: Custom performance_tracker.py

---

## Deployment Modes

### 1. Development Mode
- Paper trading only
- Dry-run mode for testing
- Manual execution via CLI
- Single-agent testing

### 2. Production Mode
- Celery orchestration
- Automated scheduling
- Multi-agent coordination
- Web monitoring via Flower (http://localhost:5555)

---

## Scalability Considerations

### Horizontal Scaling
- Each agent runs independently
- Can deploy multiple workers for Celery
- Redis handles distributed task queue
- No shared state between agents

### Vertical Scaling
- Technical analysis is fast (<10ms)
- Sentiment analysis cached per cycle
- Market data fetched once per cycle
- Subagent timeout prevents blocking (60s)

---

## Security Considerations

### API Key Management
- All credentials in `.env` (not committed)
- Environment variable validation on startup
- Separate keys for paper vs live trading

### Risk Controls
- Hard-coded position size limits
- Mandatory stop losses
- Daily loss circuit breakers
- Correlation monitoring
- Manual override always available

### Audit Trail
- All trades logged with timestamp
- All decisions logged with rationale
- All risk checks logged
- Compliance-ready audit log

---

## Future Architecture Enhancements

### Planned Improvements
- Background daemon process (detached from terminal)
- Holiday calendar integration
- Advanced sentiment models (FinBERT)
- Custom trading dashboard
- Multi-timeframe analysis
- Portfolio optimization
- Performance-based capital allocation

### Under Consideration
- WebSocket real-time data feeds
- Microservices architecture
- Database backend (PostgreSQL/TimescaleDB)
- GraphQL API for monitoring
- Machine learning backtesting framework
