"""Stub MCP client for market data fallback.

This is a minimal implementation to unblock trading loops.
The MCP (Model Context Protocol) integration with Alpha Vantage
can be fully implemented later if needed.

For now, all calls return error responses, and market_data.py
will fall back to Alpaca API and local calculations.
"""
from typing import Dict, Any
from ztrade.core.logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """Stub MCP client that returns empty/error responses."""

    def __init__(self):
        logger.info("MCP Client initialized (stub mode - all calls will use fallback paths)")

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get quote - returns error to trigger Alpaca fallback."""
        return {"error": "MCP client stub - use Alpaca instead"}

    def get_technical_indicators(
        self, symbol: str, period: str = "3mo", interval: str = "1d"
    ) -> Dict[str, Any]:
        """Get technical indicators - returns error to trigger local calculation."""
        return {"error": "MCP client stub - using local calculations"}

    def analyze_trend(self, symbol: str, period: str = "1mo") -> Dict[str, Any]:
        """Analyze trend - returns error to trigger local analysis."""
        return {"error": "MCP client stub - using local trend analysis"}

    def get_historical_data(
        self, symbol: str, period: str = "1mo", interval: str = "1d"
    ) -> Dict[str, Any]:
        """Get historical data - returns error to trigger Alpaca bars."""
        return {"error": "MCP client stub - using Alpaca historical bars"}


def get_mcp_client() -> MCPClient:
    """Factory function to get MCP client."""
    return MCPClient()
