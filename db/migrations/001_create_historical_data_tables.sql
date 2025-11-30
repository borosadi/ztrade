-- Migration 001: Create tables for historical market data and backtesting (SQLite)
-- Author: Ztrade Development Team
-- Date: 2025-11-26
-- Related: ADR-007
-- Database: SQLite

-- ============================================================================
-- Historical OHLCV Bars Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS market_bars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    timeframe TEXT NOT NULL,  -- '1m', '5m', '15m', '1h', '1d'
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    vwap REAL,
    trade_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp, timeframe)
);

-- ============================================================================
-- Historical Sentiment Data Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS sentiment_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    source TEXT NOT NULL,  -- 'news', 'reddit', 'sec'
    sentiment TEXT NOT NULL,  -- 'positive', 'negative', 'neutral'
    score REAL NOT NULL CHECK (score BETWEEN -1.0 AND 1.0),
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    metadata TEXT,  -- JSON string - Source-specific data (articles, posts, filings)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp, source)
);

-- ============================================================================
-- Backtesting Runs Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS backtest_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    initial_capital REAL NOT NULL,
    final_capital REAL,
    total_return_pct REAL,  -- Percentage return
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    max_drawdown REAL,
    sharpe_ratio REAL,
    win_rate REAL,  -- Percentage
    avg_trade_pnl REAL,
    config TEXT NOT NULL,  -- JSON string - Snapshot of agent config used
    status TEXT DEFAULT 'completed',  -- 'running', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ============================================================================
-- Backtesting Trades Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS backtest_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES backtest_runs(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('buy', 'sell')),
    symbol TEXT NOT NULL,
    quantity REAL NOT NULL CHECK (quantity > 0),  -- Supports fractional shares (crypto)
    price REAL NOT NULL CHECK (price > 0),
    commission REAL DEFAULT 0,
    pnl REAL,  -- Profit/loss for this trade
    portfolio_value REAL,  -- Total portfolio value after trade
    cash_balance REAL,  -- Cash balance after trade
    reason TEXT,  -- Decision reason (technical signal, sentiment, etc.)
    metadata TEXT,  -- JSON string - Additional context (market conditions, sentiment scores)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

-- Note: SQLite doesn't support CREATE OR REPLACE VIEW in the same way as PostgreSQL
-- Views will be created separately if they don't exist
