# ADR-007: Data Collection Service and Backtesting Framework

**Status**: Accepted
**Date**: 2025-11-10
**Deciders**: Development Team

---

## Context

Before deploying agents to paper trading, we need:

1. **Historical Data Collection**: Continuous ingestion of market data (bars, quotes, sentiment) for analysis and backtesting
2. **Backtesting Framework**: Ability to validate trading strategies against historical data without risking capital

Current gaps:
- No persistent historical data storage
- No way to test strategies before deployment
- Limited ability to analyze strategy performance over time
- No mechanism for continuous data collection

---

## Decision

We will implement:

### 1. Data Collection Service

**Database Schema**:
```sql
-- Historical OHLCV bars
CREATE TABLE market_bars (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    timeframe VARCHAR(10) NOT NULL,  -- '1m', '5m', '15m', '1h', '1d'
    open DECIMAL(12, 4) NOT NULL,
    high DECIMAL(12, 4) NOT NULL,
    low DECIMAL(12, 4) NOT NULL,
    close DECIMAL(12, 4) NOT NULL,
    volume BIGINT NOT NULL,
    vwap DECIMAL(12, 4),
    trade_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timestamp, timeframe)
);

-- Historical sentiment data
CREATE TABLE sentiment_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    source VARCHAR(20) NOT NULL,  -- 'news', 'reddit', 'sec'
    sentiment VARCHAR(20) NOT NULL,  -- 'positive', 'negative', 'neutral'
    score DECIMAL(5, 4) NOT NULL,  -- -1.0 to 1.0
    confidence DECIMAL(5, 4) NOT NULL,  -- 0.0 to 1.0
    metadata JSONB,  -- Source-specific data
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timestamp, source)
);

-- Backtesting runs
CREATE TABLE backtest_runs (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    initial_capital DECIMAL(12, 2) NOT NULL,
    final_capital DECIMAL(12, 2),
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    max_drawdown DECIMAL(12, 2),
    sharpe_ratio DECIMAL(6, 4),
    config JSONB,  -- Agent config snapshot
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Backtesting trades
CREATE TABLE backtest_trades (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES backtest_runs(id),
    timestamp TIMESTAMPTZ NOT NULL,
    action VARCHAR(10) NOT NULL,  -- 'buy', 'sell'
    symbol VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(12, 4) NOT NULL,
    pnl DECIMAL(12, 2),
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_market_bars_symbol_time ON market_bars(symbol, timestamp DESC);
CREATE INDEX idx_market_bars_timeframe ON market_bars(timeframe, timestamp DESC);
CREATE INDEX idx_sentiment_symbol_time ON sentiment_history(symbol, timestamp DESC);
CREATE INDEX idx_sentiment_source ON sentiment_history(source, timestamp DESC);
CREATE INDEX idx_backtest_runs_agent ON backtest_runs(agent_id, created_at DESC);
CREATE INDEX idx_backtest_trades_run ON backtest_trades(run_id, timestamp);
```

**Collection Tasks** (Celery):
- `collect_market_bars`: Fetch and store OHLCV data for all tracked symbols
- `collect_sentiment`: Fetch and store multi-source sentiment data
- `backfill_historical_data`: One-time backfill for historical data

**Schedule**:
- Market bars: Every 1 minute during market hours
- Sentiment: Every 15 minutes during market hours
- Backfill: On-demand via CLI

### 2. Backtesting Framework

**Components**:

1. **Backtesting Engine** (`cli/utils/backtesting_engine.py`):
   - Replay historical data chronologically
   - Simulate agent decision-making
   - Track positions and P&L
   - Generate performance metrics

2. **CLI Commands** (`cli/commands/backtest.py`):
   ```bash
   # Run backtest for agent
   uv run ztrade backtest run agent_spy --start 2024-01-01 --end 2024-12-31

   # List backtest runs
   uv run ztrade backtest list

   # View backtest results
   uv run ztrade backtest show <run_id>

   # Compare multiple runs
   uv run ztrade backtest compare <run_id1> <run_id2>
   ```

3. **Performance Metrics**:
   - Total return (%)
   - Sharpe ratio
   - Maximum drawdown
   - Win rate
   - Average trade P&L
   - Risk-adjusted return

**Workflow**:
```
1. Load historical data from database
2. Initialize simulated portfolio
3. For each timestamp:
   a. Load market context (bars + sentiment)
   b. Run agent decision logic
   c. Execute simulated trades
   d. Update portfolio state
4. Calculate final metrics
5. Store results in database
6. Generate report
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Data Collection Service                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Celery Beat (Scheduler)                                │
│       │                                                  │
│       ├──> collect_market_bars (every 1 min)            │
│       │    ├──> Alpaca API ──> market_bars table        │
│       │                                                  │
│       └──> collect_sentiment (every 15 min)             │
│            ├──> News API ──> sentiment_history          │
│            ├──> Reddit API ──> sentiment_history        │
│            └──> SEC API ──> sentiment_history           │
│                                                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Backtesting Framework                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  CLI Command: ztrade backtest run                       │
│       │                                                  │
│       ├──> Load historical data (market_bars +          │
│       │    sentiment_history)                           │
│       │                                                  │
│       ├──> Initialize BacktestEngine                    │
│       │    ├──> Simulated Portfolio                     │
│       │    ├──> Agent Config                            │
│       │    └──> Risk Rules                              │
│       │                                                  │
│       ├──> For each timestamp:                          │
│       │    ├──> Build market context                    │
│       │    ├──> Run agent decision logic                │
│       │    ├──> Execute simulated trade                 │
│       │    └──> Update portfolio state                  │
│       │                                                  │
│       ├──> Calculate metrics                            │
│       │                                                  │
│       └──> Store results (backtest_runs +               │
│            backtest_trades tables)                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Collection Flow
```
Market Open
    │
    ├──> Celery Beat: collect_market_bars
    │         ├──> Fetch 1min bars from Alpaca
    │         └──> INSERT INTO market_bars
    │
    └──> Celery Beat: collect_sentiment (every 15min)
              ├──> Fetch news sentiment
              ├──> Fetch Reddit sentiment
              ├──> Fetch SEC sentiment
              └──> INSERT INTO sentiment_history
```

### Backtesting Flow
```
User: ztrade backtest run agent_spy --start 2024-01-01 --end 2024-12-31
    │
    ├──> Load agent config
    │
    ├──> SELECT * FROM market_bars WHERE timestamp BETWEEN ... ORDER BY timestamp
    │
    ├──> SELECT * FROM sentiment_history WHERE timestamp BETWEEN ...
    │
    ├──> For timestamp in chronological order:
    │     ├──> Build market context (bars + sentiment)
    │     ├──> Run technical analysis
    │     ├──> Get agent decision (buy/sell/hold)
    │     ├──> Execute simulated trade
    │     ├──> Update portfolio (cash, positions, P&L)
    │     └──> Record trade in backtest_trades
    │
    ├──> Calculate final metrics:
    │     ├──> Total return
    │     ├──> Sharpe ratio
    │     ├──> Max drawdown
    │     ├──> Win rate
    │     └──> Risk-adjusted return
    │
    └──> INSERT INTO backtest_runs + Display report
```

---

## Rationale

### Why Continuous Data Collection?

1. **Historical Context**: Need data for backtesting and analysis
2. **Gap Prevention**: Avoid missing critical market data
3. **Sentiment History**: Track sentiment changes over time
4. **Pattern Recognition**: Identify recurring patterns

### Why Backtesting Framework?

1. **Risk Mitigation**: Validate strategies before risking capital
2. **Strategy Optimization**: Compare different parameters
3. **Performance Prediction**: Estimate expected returns
4. **Confidence Building**: Prove strategy effectiveness

### Design Choices

**PostgreSQL over NoSQL**:
- Time-series queries with SQL
- ACID guarantees for trade data
- Relational integrity for backtest runs
- Excellent indexing for time-based queries

**Celery Tasks for Collection**:
- Scheduled execution during market hours
- Fault tolerance and retry logic
- Monitoring via Flower
- Scales with worker count

**Separate Backtesting Tables**:
- Isolate backtest data from live trading
- Compare multiple backtest runs
- Track strategy evolution over time

---

## Consequences

### Positive

✅ **Data-Driven Decisions**: Historical data for analysis
✅ **Strategy Validation**: Test before deploying
✅ **Performance Tracking**: Compare strategies objectively
✅ **Risk Reduction**: Identify failures in backtesting
✅ **Continuous Improvement**: Optimize based on backtest results
✅ **Audit Trail**: Complete history of all backtests

### Negative

⚠️ **Storage Growth**: Database size increases over time
⚠️ **Collection Costs**: API rate limits and data quotas
⚠️ **Complexity**: Additional services to maintain
⚠️ **Backtest Limitations**: Past performance ≠ future results

### Mitigations

- Implement data retention policies (e.g., keep 2 years)
- Use efficient data compression
- Monitor API usage and costs
- Clearly document backtest assumptions and limitations
- Regular database maintenance and optimization

---

## Implementation Plan

### Phase 1: Database Schema (Week 1)
- [ ] Create migration scripts
- [ ] Add database models
- [ ] Create indexes
- [ ] Test schema performance

### Phase 2: Data Collection (Week 1-2)
- [ ] Implement collection tasks
- [ ] Add to Celery Beat schedule
- [ ] Create backfill command
- [ ] Test during market hours

### Phase 3: Backtesting Engine (Week 2-3)
- [ ] Build core engine
- [ ] Implement portfolio simulation
- [ ] Add performance metrics
- [ ] Test with sample data

### Phase 4: CLI & Integration (Week 3-4)
- [ ] Create CLI commands
- [ ] Add to Docker setup
- [ ] Update documentation
- [ ] End-to-end testing

---

## References

- [Time-Series Data in PostgreSQL](https://www.timescale.com/blog/time-series-data-postgresql/)
- [Backtesting Best Practices](https://www.quantstart.com/articles/backtesting-systematic-trading-strategies-in-python-considerations-and-open-source-frameworks/)
- [Alpaca Market Data API](https://alpaca.markets/docs/api-references/market-data-api/)

---

## Related ADRs

- [ADR-001: Asset-Based Agent Architecture](ADR-001-asset-based-architecture.md)
- [ADR-002: Multi-Source Sentiment Analysis](ADR-002-multi-source-sentiment.md)
- [ADR-003: Performance Tracking System](ADR-003-performance-tracking.md)
- [ADR-004: Continuous Trading Loops](ADR-004-continuous-trading-loops.md)
- [ADR-006: Containerization Strategy](ADR-006-containerization-strategy.md)
