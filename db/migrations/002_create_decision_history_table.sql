-- Migration 002: Create table for live trading decision history (SQLite)
-- Author: Ztrade Development Team
-- Date: 2025-11-28
-- Purpose: Track all trading decisions (buy/sell/hold) with full context
-- Database: SQLite

-- ============================================================================
-- Live Trading Decision History Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS decision_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    agent_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('buy', 'sell', 'hold')),
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),

    -- Sentiment inputs
    sentiment_score REAL CHECK (sentiment_score BETWEEN -1.0 AND 1.0),
    sentiment_confidence REAL CHECK (sentiment_confidence BETWEEN 0.0 AND 1.0),
    sentiment_sources TEXT,  -- JSON array - ['news', 'reddit', 'sec']

    -- Technical inputs
    technical_signal TEXT CHECK (technical_signal IN ('buy', 'sell', 'neutral')),
    technical_confidence REAL CHECK (technical_confidence BETWEEN 0.0 AND 1.0),

    -- Trade details (for buy/sell decisions)
    quantity REAL CHECK (quantity >= 0),  -- Supports fractional shares (crypto)
    price REAL CHECK (price >= 0),
    stop_loss REAL,

    -- Decision rationale and metadata
    rationale TEXT,
    trade_approved INTEGER,  -- Boolean: 0 = rejected/hold, 1 = approved
    rejection_reason TEXT,  -- Risk rejection reason if not approved
    trade_executed INTEGER,  -- Boolean: 0 = not executed, 1 = executed
    order_id TEXT,  -- Broker order ID if executed

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Query decisions by agent
CREATE INDEX IF NOT EXISTS idx_decision_agent_time
    ON decision_history(agent_id, timestamp DESC);

-- Query decisions by symbol
CREATE INDEX IF NOT EXISTS idx_decision_symbol_time
    ON decision_history(symbol, timestamp DESC);

-- Query decisions by decision type
CREATE INDEX IF NOT EXISTS idx_decision_type_time
    ON decision_history(decision, timestamp DESC);

-- Query approved/executed trades
CREATE INDEX IF NOT EXISTS idx_decision_approved
    ON decision_history(trade_approved, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_decision_executed
    ON decision_history(trade_executed, timestamp DESC);

-- Composite index for agent analysis
CREATE INDEX IF NOT EXISTS idx_decision_agent_symbol_time
    ON decision_history(agent_id, symbol, timestamp DESC);
