-- Migration 001: Create tables for historical market data and backtesting
-- Author: Ztrade Development Team
-- Date: 2025-11-10
-- Related: ADR-007

-- ============================================================================
-- Historical OHLCV Bars Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS market_bars (
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
    CONSTRAINT unique_bar UNIQUE(symbol, timestamp, timeframe)
);

COMMENT ON TABLE market_bars IS 'Historical OHLCV bar data for all tracked symbols';
COMMENT ON COLUMN market_bars.timeframe IS 'Bar interval: 1m, 5m, 15m, 1h, 1d';
COMMENT ON COLUMN market_bars.vwap IS 'Volume-weighted average price';

-- ============================================================================
-- Historical Sentiment Data Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS sentiment_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    source VARCHAR(20) NOT NULL,  -- 'news', 'reddit', 'sec'
    sentiment VARCHAR(20) NOT NULL,  -- 'positive', 'negative', 'neutral'
    score DECIMAL(5, 4) NOT NULL CHECK (score BETWEEN -1.0 AND 1.0),
    confidence DECIMAL(5, 4) NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    metadata JSONB,  -- Source-specific data (articles, posts, filings)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_sentiment UNIQUE(symbol, timestamp, source)
);

COMMENT ON TABLE sentiment_history IS 'Historical sentiment data from multiple sources';
COMMENT ON COLUMN sentiment_history.source IS 'Data source: news, reddit, sec';
COMMENT ON COLUMN sentiment_history.metadata IS 'Source-specific details (article count, post count, filing count)';

-- ============================================================================
-- Backtesting Runs Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS backtest_runs (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    initial_capital DECIMAL(12, 2) NOT NULL,
    final_capital DECIMAL(12, 2),
    total_return_pct DECIMAL(8, 4),  -- Percentage return
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    max_drawdown DECIMAL(12, 2),
    sharpe_ratio DECIMAL(6, 4),
    win_rate DECIMAL(5, 4),  -- Percentage
    avg_trade_pnl DECIMAL(12, 2),
    config JSONB NOT NULL,  -- Snapshot of agent config used
    status VARCHAR(20) DEFAULT 'completed',  -- 'running', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

COMMENT ON TABLE backtest_runs IS 'Historical backtesting runs for all agents';
COMMENT ON COLUMN backtest_runs.config IS 'Complete agent configuration snapshot';
COMMENT ON COLUMN backtest_runs.sharpe_ratio IS 'Risk-adjusted return metric';

-- ============================================================================
-- Backtesting Trades Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS backtest_trades (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES backtest_runs(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('buy', 'sell')),
    symbol VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price DECIMAL(12, 4) NOT NULL CHECK (price > 0),
    commission DECIMAL(8, 2) DEFAULT 0,
    pnl DECIMAL(12, 2),  -- Profit/loss for this trade
    portfolio_value DECIMAL(12, 2),  -- Total portfolio value after trade
    cash_balance DECIMAL(12, 2),  -- Cash balance after trade
    reason TEXT,  -- Decision reason (technical signal, sentiment, etc.)
    metadata JSONB,  -- Additional context (market conditions, sentiment scores)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE backtest_trades IS 'Individual trades from backtesting runs';
COMMENT ON COLUMN backtest_trades.reason IS 'Why this trade was made';
COMMENT ON COLUMN backtest_trades.metadata IS 'Market context at time of trade';

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Market bars indexes
CREATE INDEX IF NOT EXISTS idx_market_bars_symbol_time
    ON market_bars(symbol, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_market_bars_timeframe
    ON market_bars(timeframe, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_market_bars_symbol_timeframe
    ON market_bars(symbol, timeframe, timestamp DESC);

-- Sentiment history indexes
CREATE INDEX IF NOT EXISTS idx_sentiment_symbol_time
    ON sentiment_history(symbol, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_sentiment_source
    ON sentiment_history(source, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_sentiment_symbol_source_time
    ON sentiment_history(symbol, source, timestamp DESC);

-- Backtesting indexes
CREATE INDEX IF NOT EXISTS idx_backtest_runs_agent
    ON backtest_runs(agent_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_backtest_runs_dates
    ON backtest_runs(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_backtest_trades_run
    ON backtest_trades(run_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_backtest_trades_symbol
    ON backtest_trades(symbol, timestamp);

-- ============================================================================
-- Helpful Views
-- ============================================================================

-- Latest sentiment for each symbol/source combination
CREATE OR REPLACE VIEW latest_sentiment AS
SELECT DISTINCT ON (symbol, source)
    symbol,
    source,
    sentiment,
    score,
    confidence,
    timestamp,
    metadata
FROM sentiment_history
ORDER BY symbol, source, timestamp DESC;

COMMENT ON VIEW latest_sentiment IS 'Most recent sentiment for each symbol and source';

-- Backtest performance summary
CREATE OR REPLACE VIEW backtest_performance AS
SELECT
    br.id,
    br.agent_id,
    br.start_date,
    br.end_date,
    br.initial_capital,
    br.final_capital,
    br.total_return_pct,
    br.total_trades,
    br.win_rate,
    br.sharpe_ratio,
    br.max_drawdown,
    br.avg_trade_pnl,
    (br.final_capital - br.initial_capital) as total_pnl,
    EXTRACT(EPOCH FROM (br.end_date - br.start_date)) / 86400 as trading_days,
    br.created_at
FROM backtest_runs br
WHERE br.status = 'completed'
ORDER BY br.created_at DESC;

COMMENT ON VIEW backtest_performance IS 'Summary of completed backtesting runs with calculated metrics';

-- ============================================================================
-- Grant Permissions (adjust as needed for production)
-- ============================================================================

-- Grant to ztrade user (matches docker-compose config)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ztrade;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ztrade;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ztrade;
