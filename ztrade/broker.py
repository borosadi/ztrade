"""Alpaca broker integration for trade execution."""
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import (
    CryptoLatestQuoteRequest,
    StockLatestQuoteRequest,
    CryptoBarsRequest,
    StockBarsRequest
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from dotenv import load_dotenv
from ztrade.core.logger import get_logger

load_dotenv()
logger = get_logger(__name__)


class Broker:
    """Alpaca broker interface for trading operations."""

    def __init__(self):
        """Initialize Alpaca API client."""
        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")
        base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

        if not api_key or not secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set")

        # Old API for trading operations
        self.api = tradeapi.REST(api_key, secret_key, base_url)

        # New API for crypto and stock data (alpaca-py)
        self.crypto_data_client = CryptoHistoricalDataClient(api_key, secret_key)
        self.stock_data_client = StockHistoricalDataClient(api_key, secret_key)

        logger.info(f"Broker initialized with base URL: {base_url}")

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information.

        Returns:
            Dict with account details (equity, cash, buying_power, etc.)
        """
        account = self.api.get_account()
        return {
            "equity": float(account.equity),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "portfolio_value": float(account.portfolio_value),
            "pattern_day_trader": account.pattern_day_trader,
            "trading_blocked": account.trading_blocked,
            "account_blocked": account.account_blocked,
        }

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions.

        Returns:
            List of position dicts
        """
        positions = self.api.list_positions()
        return [
            {
                "symbol": pos.symbol,
                "qty": float(pos.qty),
                "side": pos.side,
                "avg_entry_price": float(pos.avg_entry_price),
                "current_price": float(pos.current_price),
                "market_value": float(pos.market_value),
                "unrealized_pl": float(pos.unrealized_pl),
                "unrealized_plpc": float(pos.unrealized_plpc),
            }
            for pos in positions
        ]

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position for a specific symbol.

        Args:
            symbol: Stock/crypto symbol

        Returns:
            Position dict or None if no position
        """
        try:
            pos = self.api.get_position(symbol)
            return {
                "symbol": pos.symbol,
                "qty": float(pos.qty),
                "side": pos.side,
                "avg_entry_price": float(pos.avg_entry_price),
                "current_price": float(pos.current_price),
                "unrealized_pl": float(pos.unrealized_pl),
            }
        except Exception as e:
            logger.debug(f"No position found for {symbol}: {e}")
            return None

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Submit a trading order.

        Args:
            symbol: Stock/crypto symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            order_type: 'market', 'limit', 'stop', 'stop_limit'
            time_in_force: 'day', 'gtc', 'ioc', 'fok'
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders

        Returns:
            Order dict with id, status, filled info
        """
        order = self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force=time_in_force,
            limit_price=limit_price,
            stop_loss={"stop_price": stop_price} if stop_price else None,
        )

        logger.info(f"Order submitted: {side} {qty} {symbol} @ {order_type}")

        return {
            "id": order.id,
            "symbol": order.symbol,
            "qty": float(order.qty),
            "side": order.side,
            "type": order.type,
            "status": order.status,
        }

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled successfully
        """
        try:
            self.api.cancel_order(order_id)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_orders(self, status: str = "open") -> List[Dict[str, Any]]:
        """Get orders by status.

        Args:
            status: 'open', 'closed', 'all'

        Returns:
            List of order dicts
        """
        orders = self.api.list_orders(status=status)
        return [
            {
                "id": order.id,
                "symbol": order.symbol,
                "qty": float(order.qty),
                "side": order.side,
                "type": order.type,
                "status": order.status,
                "created_at": str(order.created_at),
            }
            for order in orders
        ]

    def close_position(self, symbol: str) -> bool:
        """Close an open position.

        Args:
            symbol: Symbol to close

        Returns:
            True if closed successfully
        """
        try:
            self.api.close_position(symbol)
            logger.info(f"Position closed: {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to close position {symbol}: {e}")
            return False

    def _is_crypto(self, symbol: str) -> bool:
        """Check if symbol is a crypto pair (contains /)."""
        return '/' in symbol

    def get_latest_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest quote for a symbol.

        Args:
            symbol: Stock/crypto symbol (e.g., "TSLA" or "BTC/USD")

        Returns:
            Quote dict with bid, ask, last price
        """
        try:
            # Use alpaca-py for crypto, old API for stocks
            if self._is_crypto(symbol):
                # Crypto: use alpaca-py
                request = CryptoLatestQuoteRequest(symbol_or_symbols=symbol)
                quotes = self.crypto_data_client.get_crypto_latest_quote(request)

                if symbol not in quotes:
                    logger.warning(f"No quote data for {symbol}")
                    return None

                quote = quotes[symbol]
                return {
                    "symbol": symbol,
                    "bid": float(quote.bid_price),
                    "ask": float(quote.ask_price),
                }
            else:
                # Stock: use old alpaca-trade-api
                quote = self.api.get_latest_quote(symbol)

                # Handle different quote object formats
                result = {"symbol": symbol}

                # Try to get bid/ask prices
                if hasattr(quote, 'bp'):
                    result["bid"] = float(quote.bp)
                elif hasattr(quote, 'bid_price'):
                    result["bid"] = float(quote.bid_price)

                if hasattr(quote, 'ap'):
                    result["ask"] = float(quote.ap)
                elif hasattr(quote, 'ask_price'):
                    result["ask"] = float(quote.ask_price)

                # Use ask price if available, otherwise bid, otherwise None
                if "ask" not in result and "bid" not in result:
                    logger.warning(f"No price data in quote for {symbol}")
                    return None

                return result

        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return None

    def _convert_timeframe(self, timeframe_str: str) -> TimeFrame:
        """Convert timeframe string to alpaca-py TimeFrame object."""
        # Map common timeframe strings to alpaca-py TimeFrame
        mapping = {
            '1min': TimeFrame(1, TimeFrameUnit.Minute),
            '1m': TimeFrame(1, TimeFrameUnit.Minute),
            '5min': TimeFrame(5, TimeFrameUnit.Minute),
            '5m': TimeFrame(5, TimeFrameUnit.Minute),
            '15min': TimeFrame(15, TimeFrameUnit.Minute),
            '15m': TimeFrame(15, TimeFrameUnit.Minute),
            '1hour': TimeFrame(1, TimeFrameUnit.Hour),
            '1h': TimeFrame(1, TimeFrameUnit.Hour),
            '4hour': TimeFrame(4, TimeFrameUnit.Hour),
            '4h': TimeFrame(4, TimeFrameUnit.Hour),
            '1day': TimeFrame(1, TimeFrameUnit.Day),
            '1d': TimeFrame(1, TimeFrameUnit.Day),
        }
        return mapping.get(timeframe_str, TimeFrame(1, TimeFrameUnit.Hour))

    def get_bars(
        self,
        symbol: str,
        timeframe: str = "1day",
        limit: int = 100,
        start: str = None,
        end: str = None
    ) -> List[Dict[str, Any]]:
        """Get historical price bars from Alpaca.

        Args:
            symbol: Stock/crypto symbol (e.g., "TSLA" or "BTC/USD")
            timeframe: Bar timeframe ('1min', '5min', '15min', '1hour', '1day', etc.)
            limit: Number of bars to fetch (max 10000)
            start: Start date/time (ISO format or datetime object)
            end: End date/time (ISO format or datetime object)

        Returns:
            List of bar dicts with OHLCV data
        """
        try:
            # Use alpaca-py for crypto, old API for stocks
            if self._is_crypto(symbol):
                # Crypto: use alpaca-py
                timeframe_obj = self._convert_timeframe(timeframe)

                # Calculate start/end if not provided
                if not end:
                    end = datetime.now()
                if not start:
                    # Calculate based on timeframe and limit
                    if timeframe_obj.unit == TimeFrameUnit.Minute:
                        start = end - timedelta(minutes=timeframe_obj.amount * limit)
                    elif timeframe_obj.unit == TimeFrameUnit.Hour:
                        start = end - timedelta(hours=timeframe_obj.amount * limit)
                    else:
                        start = end - timedelta(days=timeframe_obj.amount * limit)

                request = CryptoBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=timeframe_obj,
                    start=start,
                    end=end,
                    limit=min(limit, 10000)
                )

                bars_data = self.crypto_data_client.get_crypto_bars(request)

                # BarSet.data is a dict with symbol as key and list of Bar objects as value
                if symbol not in bars_data.data:
                    logger.warning(f"No bars available for {symbol}")
                    return []

                bars_list = bars_data.data[symbol]

                if not bars_list:
                    logger.warning(f"No bars available for {symbol}")
                    return []

                # Convert list of Bar objects to list of dicts
                result = []
                for bar in bars_list:
                    result.append({
                        "timestamp": bar.timestamp.isoformat() if hasattr(bar.timestamp, 'isoformat') else str(bar.timestamp),
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": float(bar.volume),
                    })

                logger.info(f"Fetched {len(result)} bars for {symbol} ({timeframe})")
                return result

            else:
                # Stock: use old alpaca-trade-api
                # Convert timeframe format for old API (5m → 5min)
                old_api_timeframe = timeframe
                if timeframe.endswith('m') and not timeframe.endswith('min'):
                    # Convert 5m → 5min, 15m → 15min
                    old_api_timeframe = timeframe.replace('m', 'min')
                elif timeframe.endswith('h'):
                    # Convert 1h → 1hour, 4h → 4hour
                    old_api_timeframe = timeframe.replace('h', 'hour')
                elif timeframe.endswith('d'):
                    # Convert 1d → 1day
                    old_api_timeframe = timeframe.replace('d', 'day')

                params = {
                    'limit': min(limit, 10000)
                }

                if start:
                    params['start'] = start
                if end:
                    params['end'] = end

                bars = self.api.get_bars(
                    symbol,
                    old_api_timeframe,
                    **params
                )

                if not bars or len(bars.df) == 0:
                    logger.warning(f"No bars available for {symbol}")
                    return []

                # Convert DataFrame to list of dicts
                result = []
                for idx, row in bars.df.iterrows():
                    result.append({
                        "timestamp": idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                        "open": float(row['open']),
                        "high": float(row['high']),
                        "low": float(row['low']),
                        "close": float(row['close']),
                        "volume": int(row['volume']),
                    })

                logger.info(f"Fetched {len(result)} bars for {symbol} ({timeframe})")
                return result

        except Exception as e:
            logger.error(f"Failed to get bars for {symbol}: {e}")
            return []


def get_broker() -> Broker:
    """Factory function to get a broker instance.

    Returns:
        Broker instance
    """
    return Broker()
