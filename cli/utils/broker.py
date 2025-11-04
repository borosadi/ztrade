"""Alpaca broker integration for trade execution."""
import os
from typing import Optional, List, Dict, Any
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv
from cli.utils.logger import get_logger

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

        self.api = tradeapi.REST(api_key, secret_key, base_url)
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
        except Exception:
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

    def get_latest_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest quote for a symbol.

        Args:
            symbol: Stock/crypto symbol

        Returns:
            Quote dict with bid, ask, last price
        """
        try:
            quote = self.api.get_latest_quote(symbol)
            return {
                "symbol": symbol,
                "bid": float(quote.bp),
                "ask": float(quote.ap),
                "bid_size": float(quote.bs),
                "ask_size": float(quote.as_),
            }
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return None


def get_broker() -> Broker:
    """Factory function to get a broker instance.

    Returns:
        Broker instance
    """
    return Broker()
