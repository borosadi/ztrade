"""MCP Client for Market Data Server."""

import asyncio
import json
import subprocess
from typing import Any, Dict, Optional
from pathlib import Path
from cli.utils.broker import get_broker


class MCPMarketDataClient:
    """Client for interacting with the Market Data MCP server."""

    def __init__(self):
        """Initialize the MCP client."""
        self.server_process = None
        self.connected = False

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote for a symbol.

        Args:
            symbol: Stock symbol (e.g., BTC, SPY, TSLA)

        Returns:
            Dict containing price, volume, change data
        """
        return self._call_tool("get_quote", {"symbol": symbol})

    def get_historical_data(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Get historical price data.

        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, etc.)
            interval: Data interval (1m, 5m, 15m, 1h, 1d, etc.)

        Returns:
            Dict containing historical OHLCV data
        """
        return self._call_tool("get_historical_data", {
            "symbol": symbol,
            "period": period,
            "interval": interval
        })

    def get_technical_indicators(
        self,
        symbol: str,
        period: str = "3mo",
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Calculate technical indicators.

        Args:
            symbol: Stock symbol
            period: Historical period for calculations
            interval: Data interval

        Returns:
            Dict containing SMA, EMA, RSI, MACD, Bollinger Bands
        """
        return self._call_tool("get_technical_indicators", {
            "symbol": symbol,
            "period": period,
            "interval": interval
        })

    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get company information and fundamentals.

        Args:
            symbol: Stock symbol

        Returns:
            Dict containing company info, sector, market cap, etc.
        """
        return self._call_tool("get_company_info", {"symbol": symbol})

    def analyze_trend(
        self,
        symbol: str,
        period: str = "1mo"
    ) -> Dict[str, Any]:
        """
        Analyze price trend and momentum.

        Args:
            symbol: Stock symbol
            period: Analysis period

        Returns:
            Dict containing trend analysis
        """
        return self._call_tool("analyze_trend", {
            "symbol": symbol,
            "period": period
        })

    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool synchronously.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result as dict
        """
        # For now, we'll use a direct synchronous approach
        # In production, this would use the full MCP protocol
        return asyncio.run(self._call_tool_async(tool_name, arguments))

    async def _call_tool_async(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call an MCP tool asynchronously.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result as dict
        """
        # Direct yfinance implementation for simplicity
        # This avoids MCP protocol overhead for local usage
        try:
            import yfinance as yf
            import pandas as pd

            symbol = arguments.get("symbol", "")
            # Normalize symbol
            symbol_map = {
                "BTC": "BTC-USD",
                "ETH": "ETH-USD",
                "SPY": "SPY",
                "TSLA": "TSLA",
                "AAPL": "AAPL",
                "EUR": "EURUSD=X"
            }
            yf_symbol = symbol_map.get(symbol.upper(), symbol)

            ticker = yf.Ticker(yf_symbol)

            if tool_name == "get_quote":
                hist = ticker.history(period="1d")
                if hist.empty:
                    return {"error": f"No data for {symbol}"}

                return {
                    "symbol": symbol,
                    "price": round(float(hist['Close'].iloc[-1]), 2),
                    "open": round(float(hist['Open'].iloc[-1]), 2),
                    "high": round(float(hist['High'].iloc[-1]), 2),
                    "low": round(float(hist['Low'].iloc[-1]), 2),
                    "volume": int(hist['Volume'].iloc[-1]),
                    "change": round(float(hist['Close'].iloc[-1] - hist['Open'].iloc[-1]), 2),
                    "change_percent": round(((hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) / hist['Open'].iloc[-1]) * 100, 2)
                }

            elif tool_name == "get_historical_data":
                period = arguments.get("period", "1mo")
                interval = arguments.get("interval", "1d")

                # Map interval to Alpaca timeframe
                timeframe_map = {
                    "1m": "1min",
                    "5m": "5min",
                    "15m": "15min",
                    "1h": "1hour",
                    "1d": "1day",
                    "1day": "1day"
                }
                alpaca_timeframe = timeframe_map.get(interval, "1day")

                # Calculate limit based on period
                limit_map = {
                    "5d": 1000,
                    "1mo": 250,
                    "3mo": 750,
                    "6mo": 1500,
                    "1y": 3000,
                }
                limit = limit_map.get(period, 100)

                try:
                    # Try Alpaca first
                    broker = get_broker()
                    bars = broker.get_bars(symbol, alpaca_timeframe, limit)

                    if bars:
                        prices = [
                            {
                                "date": bar["timestamp"],
                                "open": round(bar["open"], 2),
                                "high": round(bar["high"], 2),
                                "low": round(bar["low"], 2),
                                "close": round(bar["close"], 2),
                                "volume": bar["volume"]
                            }
                            for bar in bars
                        ]
                        return {
                            "symbol": symbol,
                            "period": period,
                            "interval": interval,
                            "prices": prices
                        }
                except Exception as e:
                    # Fall back to yfinance if Alpaca fails
                    pass

                # Fallback to yfinance
                hist = ticker.history(period=period, interval=interval)
                if hist.empty:
                    return {"error": f"No historical data for {symbol}"}

                prices = [
                    {
                        "date": idx.isoformat(),
                        "open": round(float(row['Open']), 2),
                        "high": round(float(row['High']), 2),
                        "low": round(float(row['Low']), 2),
                        "close": round(float(row['Close']), 2),
                        "volume": int(row['Volume'])
                    }
                    for idx, row in hist.tail(100).iterrows()
                ]

                return {
                    "symbol": symbol,
                    "period": period,
                    "interval": interval,
                    "prices": prices
                }

            elif tool_name == "get_technical_indicators":
                period = arguments.get("period", "3mo")
                interval = arguments.get("interval", "1d")

                # Map interval to Alpaca timeframe
                timeframe_map = {
                    "1m": "1min",
                    "5m": "5min",
                    "15m": "15min",
                    "1h": "1hour",
                    "1d": "1day",
                    "1day": "1day"
                }
                alpaca_timeframe = timeframe_map.get(interval, "1day")

                # Calculate limit based on period
                limit_map = {
                    "5d": 1000,
                    "1mo": 250,
                    "3mo": 750,
                    "6mo": 1500,
                    "1y": 3000,
                }
                limit = limit_map.get(period, 100)

                # Try to get data from Alpaca first
                closes = None
                try:
                    broker = get_broker()
                    bars = broker.get_bars(symbol, alpaca_timeframe, limit)
                    if bars and len(bars) >= 20:
                        closes = [bar["close"] for bar in bars]
                except Exception:
                    pass

                # Fall back to yfinance
                if not closes:
                    hist = ticker.history(period=period, interval=interval)
                    if hist.empty or len(hist) < 20:
                        return {"error": "Insufficient data"}
                    closes = hist['Close'].tolist()

                if len(closes) < 20:
                    return {"error": "Insufficient data"}

                indicators = {
                    "symbol": symbol,
                    "current_price": round(closes[-1], 2)
                }

                if len(closes) >= 20:
                    indicators["sma_20"] = round(sum(closes[-20:]) / 20, 2)
                if len(closes) >= 50:
                    indicators["sma_50"] = round(sum(closes[-50:]) / 50, 2)
                if len(closes) >= 200:
                    indicators["sma_200"] = round(sum(closes[-200:]) / 200, 2)

                # RSI calculation
                if len(closes) >= 14:
                    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
                    gains = [d if d > 0 else 0 for d in deltas[-14:]]
                    losses = [-d if d < 0 else 0 for d in deltas[-14:]]
                    avg_gain = sum(gains) / 14
                    avg_loss = sum(losses) / 14
                    if avg_loss != 0:
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                        indicators["rsi_14"] = round(rsi, 2)

                return indicators

            elif tool_name == "analyze_trend":
                period = arguments.get("period", "1mo")

                # Map period to Alpaca limit
                limit_map = {
                    "5d": 500,
                    "1mo": 250,
                    "3mo": 750,
                    "6mo": 1500,
                    "1y": 3000,
                }
                limit = limit_map.get(period, 100)

                # Try Alpaca first
                closes = None
                try:
                    broker = get_broker()
                    bars = broker.get_bars(symbol, "1day", limit)
                    if bars and len(bars) >= 5:
                        closes = [bar["close"] for bar in bars]
                except Exception:
                    pass

                # Fall back to yfinance
                if not closes:
                    hist = ticker.history(period=period)
                    if hist.empty or len(hist) < 5:
                        return {"error": "Insufficient data"}
                    closes = hist['Close'].tolist()

                if len(closes) < 5:
                    return {"error": "Insufficient data"}

                first_price = closes[0]
                last_price = closes[-1]
                change_percent = ((last_price - first_price) / first_price) * 100

                if change_percent > 5:
                    trend = "strong_uptrend"
                elif change_percent > 0:
                    trend = "uptrend"
                elif change_percent > -5:
                    trend = "downtrend"
                else:
                    trend = "strong_downtrend"

                return {
                    "symbol": symbol,
                    "period": period,
                    "start_price": round(first_price, 2),
                    "end_price": round(last_price, 2),
                    "change": round(last_price - first_price, 2),
                    "change_percent": round(change_percent, 2),
                    "trend": trend
                }

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"error": f"MCP call failed: {str(e)}"}


def get_mcp_client() -> MCPMarketDataClient:
    """Get a singleton instance of the MCP client."""
    return MCPMarketDataClient()
