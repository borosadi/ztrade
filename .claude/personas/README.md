# Ztrade Persona System

## Problem Statement

The Ztrade codebase has grown to a size where providing complete project context for every development task is inefficient and exceeds AI model token limits. A monolithic context file forces the AI to process extensive, irrelevant information (e.g., agent personalities when working on database schema), resulting in:

- Wasted tokens
- Slower development cycles
- Rapid consumption of usage quotas
- Reduced focus and accuracy

## Solution: Role-Based Context Modularization

We've split the project context into **4 specialized personas**, each containing only the information needed for that specific role. When initiating a development session, provide the AI with **only the relevant persona file** to:

- ✅ Dramatically reduce prompt size (80-90% reduction)
- ✅ Focus AI on the task at hand
- ✅ Enable faster, more numerous interactions
- ✅ Improve response quality and relevance

---

## The Four Personas

### 1. [Core Platform Engineer](core-platform-engineer.md)

**"The Backend Infrastructure Specialist"**

**Use when working on**:
- CLI commands implementation
- Database operations and migrations
- Celery task orchestration
- Docker and containerization
- CI/CD pipelines
- Broker API integration
- Core application logic
- Configuration management

**Examples**:
- "Add a new CLI command for portfolio rebalancing"
- "Fix database connection pooling issue"
- "Optimize Celery worker performance"
- "Update Docker Compose for new service"
- "Implement retry logic in broker API calls"

**Focus Areas**: `cli/`, `db/`, `config/`, `celery_app.py`, `docker-compose.yml`

**Excluded**: Agent strategies, dashboard UI, backtesting internals

---

### 2. [Agent Specialist](agent-specialist.md)

**"The Quantitative Strategist"**

**Use when working on**:
- Creating new trading agents
- Tuning agent personalities and strategies
- Improving sentiment analysis
- Enhancing technical indicators
- Analyzing agent performance
- Adjusting trading parameters
- Investigating decision-making logic

**Examples**:
- "Create a new ETH/USD crypto agent"
- "Improve FinBERT sentiment accuracy for tech stocks"
- "Add MACD indicator to technical analysis"
- "Analyze why agent_iwm is underperforming"
- "Tune TSLA agent's confidence threshold"

**Focus Areas**: `agents/`, `cli/utils/sentiment_*.py`, `cli/utils/technical_analyzer.py`

**Excluded**: Docker config, dashboard UI, database migrations

---

### 3. [Dashboard Developer](dashboard-developer.md)

**"The Frontend Engineer"**

**Use when working on**:
- Adding dashboard features
- Creating charts and visualizations
- Improving layout and UX
- Fixing UI bugs
- Connecting to new data sources
- Performance optimization
- Adding metrics displays

**Examples**:
- "Add a candlestick chart for agent positions"
- "Create a sentiment heatmap visualization"
- "Fix slow dashboard loading times"
- "Add agent performance comparison table"
- "Improve mobile responsiveness"

**Focus Areas**: `dashboard.py`, `run_dashboard.sh`

**Excluded**: Agent logic, Celery tasks, risk management, backtesting engine

---

### 4. [Risk & Data Analyst](risk-data-analyst.md)

**"The Performance and Risk Specialist"**

**Use when working on**:
- Running and analyzing backtests
- Improving backtesting engine
- Adjusting risk limits
- Building performance reports
- Managing historical data
- Strategy optimization
- Walk-forward testing
- Monte Carlo simulations

**Examples**:
- "Backtest the new IWM agent on 60 days of data"
- "Analyze why AAPL backtests show extreme variance"
- "Implement walk-forward parameter optimization"
- "Update risk limits for crypto volatility"
- "Backfill 90 days of BTC historical data"

**Focus Areas**: `cli/commands/backtest.py`, `cli/utils/backtesting_engine.py`, `config/risk_limits.yaml`, `oversight/`

**Excluded**: Agent personalities, dashboard UI, Docker setup

---

## How to Choose the Right Persona

### Decision Tree

```
START: What is the primary task?

├─ Working on UI/visualization?
│  └─→ Dashboard Developer

├─ Working on trading strategy or agent behavior?
│  └─→ Agent Specialist

├─ Working on backtesting, risk, or data analysis?
│  └─→ Risk & Data Analyst

└─ Working on infrastructure, CLI, DB, or orchestration?
   └─→ Core Platform Engineer
```

---

### By File/Directory

**If editing files in**:

| Directory/File | Persona |
|----------------|---------|
| `cli/commands/` | Core Platform Engineer |
| `cli/utils/broker.py`, `database.py`, `config.py`, `logger.py` | Core Platform Engineer |
| `cli/utils/sentiment_*.py`, `technical_analyzer.py`, `finbert_analyzer.py` | Agent Specialist |
| `cli/commands/backtest.py`, `cli/utils/backtesting_engine.py` | Risk & Data Analyst |
| `agents/*/` | Agent Specialist |
| `dashboard.py` | Dashboard Developer |
| `db/migrations/`, `db/migrate.py` | Core Platform Engineer |
| `db/backfill_historical_data.py` | Risk & Data Analyst |
| `config/company.yaml`, `broker.yaml` | Core Platform Engineer |
| `config/risk_limits.yaml` | Risk & Data Analyst |
| `oversight/` | Risk & Data Analyst |
| `celery_app.py`, `docker-compose.yml`, `Dockerfile` | Core Platform Engineer |

---

### By Task Type

| Task | Persona |
|------|---------|
| Fix a bug in `ztrade agent run` command | Core Platform Engineer |
| Create new ETH agent | Agent Specialist |
| Add sentiment heatmap to dashboard | Dashboard Developer |
| Analyze backtest results | Risk & Data Analyst |
| Implement database connection pooling | Core Platform Engineer |
| Tune RSI thresholds for TSLA | Agent Specialist |
| Fix slow dashboard rendering | Dashboard Developer |
| Run walk-forward optimization | Risk & Data Analyst |
| Add new Celery task | Core Platform Engineer |
| Improve FinBERT accuracy | Agent Specialist |
| Create portfolio correlation chart | Dashboard Developer |
| Backfill historical crypto data | Risk & Data Analyst |

---

## Example Usage Sessions

### Example 1: CLI Bug Fix

**Task**: Fix the `ztrade agent list` command showing incorrect status

**Persona**: Core Platform Engineer

**Why**: Working on CLI command logic, not agent strategies or UI

**Context to provide**: `.claude/personas/core-platform-engineer.md`

---

### Example 2: New Trading Agent

**Task**: Create a new agent for ETH/USD with 2-hour bars

**Persona**: Agent Specialist

**Why**: Creating agent configuration, personality, and strategy

**Context to provide**: `.claude/personas/agent-specialist.md`

---

### Example 3: Dashboard Enhancement

**Task**: Add a candlestick chart for recent trades

**Persona**: Dashboard Developer

**Why**: Pure UI/visualization work

**Context to provide**: `.claude/personas/dashboard-developer.md`

---

### Example 4: Backtest Analysis

**Task**: Analyze why SPY agent had zero trades in backtest

**Persona**: Risk & Data Analyst

**Why**: Investigating backtest results and analyzing data

**Context to provide**: `.claude/personas/risk-data-analyst.md`

---

## Multi-Persona Tasks

**Some tasks may span multiple personas**. In these cases:

1. **Start with the primary persona** (where most work will be done)
2. **Switch personas** if the task changes focus
3. **Note the switch** explicitly to the AI

### Example: End-to-End Feature

**Task**: Add a new "portfolio rebalancing" feature

**Breakdown**:
1. **Core Platform Engineer**: Implement CLI command and core logic
2. **Agent Specialist**: Adjust agent configurations for rebalancing
3. **Dashboard Developer**: Add rebalancing status to dashboard
4. **Risk & Data Analyst**: Backtest rebalancing strategy

**Approach**: Work sequentially, switching personas at each phase

---

## Persona File Sizes

**Context reduction** compared to full `CLAUDE.md`:

| Persona | Tokens (approx) | Reduction |
|---------|-----------------|-----------|
| Full CLAUDE.md | ~15,000 | 0% |
| Core Platform Engineer | ~3,500 | 77% |
| Agent Specialist | ~4,800 | 68% |
| Dashboard Developer | ~2,200 | 85% |
| Risk & Data Analyst | ~3,800 | 75% |

**Average reduction: 76%**

This means you can have **4x more interactions** within the same token budget!

---

## When to Use Full CLAUDE.md

**Use the full `CLAUDE.md` when**:
- Starting a new development session (initial orientation)
- Working on cross-cutting concerns (e.g., refactoring entire architecture)
- Onboarding new developers
- Creating high-level documentation
- Making strategic decisions affecting multiple systems

**Otherwise**: Use a persona file for focused, efficient development.

---

## Maintenance

### Keeping Personas Updated

When making significant changes:

1. **Update the relevant persona file** (not all 4 + CLAUDE.md)
2. **Update CLAUDE.md** if it's a major architectural change
3. **Update this README** if personas need reclassification

### Adding New Personas

If a new specialized role emerges (e.g., "ML Engineer" for model training):

1. Create `.claude/personas/new-persona.md`
2. Extract relevant context from existing personas
3. Update this README with decision tree logic
4. Update CLAUDE.md to reference the new persona

---

## Best Practices

1. **Always choose one persona** - don't mix contexts
2. **Be explicit** - tell the AI which persona you're using
3. **Switch personas deliberately** - announce when changing focus
4. **Keep personas focused** - resist urge to add "just one more thing"
5. **Update immediately** - when you add features, update the relevant persona

---

## Quick Reference Card

**Print and keep handy:**

```
┌─────────────────────────────────────────────────────────────┐
│              ZTRADE PERSONA QUICK SELECTOR                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CLI/DB/Docker/Celery     → Core Platform Engineer         │
│  Agents/Sentiment/TA      → Agent Specialist               │
│  Dashboard/UI/Charts      → Dashboard Developer            │
│  Backtest/Risk/Data       → Risk & Data Analyst            │
│                                                             │
│  Cross-cutting concerns   → Full CLAUDE.md                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Questions?

If unsure which persona to use:

1. Check the decision tree above
2. Look at the file/directory table
3. Default to **Core Platform Engineer** if still uncertain
4. You can always switch personas mid-session

---

**Last Updated**: 2025-11-13
**System Version**: 1.0
