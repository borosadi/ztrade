-- Migration 002: Support fractional shares for crypto assets
-- Author: Ztrade Development Team
-- Date: 2025-11-14
-- Related: Fractional Bitcoin trading support

-- ============================================================================
-- Update backtest_trades to support fractional quantities
-- ============================================================================

-- Change quantity from INTEGER to DECIMAL(20, 8) to support crypto fractional shares
-- 20 total digits, 8 decimal places (standard for crypto precision)
ALTER TABLE backtest_trades
    ALTER COLUMN quantity TYPE DECIMAL(20, 8);

-- Update the check constraint to work with DECIMAL
ALTER TABLE backtest_trades
    DROP CONSTRAINT IF EXISTS backtest_trades_quantity_check;

ALTER TABLE backtest_trades
    ADD CONSTRAINT backtest_trades_quantity_check CHECK (quantity > 0);

COMMENT ON COLUMN backtest_trades.quantity IS 'Trade quantity (supports fractional shares for crypto assets, e.g., 0.05 BTC)';
