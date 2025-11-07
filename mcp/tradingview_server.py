#!/usr/bin/env python3
"""Market Data MCP Server - Provides TradingView-style market data analytics."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any

import yfinance as yf
import pandas as pd
import numpy as np
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server


# Initialize MCP server
app = Server("market-data-server")


# Symbol mapping for common crypto and stocks
SYMBOL_MAP = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "SPY": "SPY",
    "TSLA": "TSLA",
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "GOOGL": "GOOGL",
    "AMZN": "AMZN",
    "EUR": "EURUSD=X",
    "EUR/USD": "EURUSD=X",
}


def normalize_symbol(symbol: str) -> str:
    """Normalize symbol to Yahoo Finance format."""
    symbol = symbol.upper().strip()
    return SYMBOL_MAP.get(symbol, symbol)


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """Calculate Relative Strength Index."""
    if len(prices) < period + 1:
        return None

    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None


def calculate_macd(prices: pd.Series, fast=12, slow=26, signal=9) -> dict:
    """Calculate MACD indicator."""
    if len(prices) < slow:
        return None

    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line

    return {
        "macd": float(macd.iloc[-1]),
        "signal": float(signal_line.iloc[-1]),
        "histogram": float(histogram.iloc[-1])
    }


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available market data tools."""
    return [
        Tool(
            name="get_quote",
            description="Get real-time quote for a symbol (price, volume, change)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., TSLA, BTC, SPY)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_historical_data",
            description="Get historical price data with OHLCV",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max",
                        "default": "1mo"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Data interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo",
                        "default": "1d"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_technical_indicators",
            description="Calculate technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    },
                    "period": {
                        "type": "string",
                        "description": "Historical period for calculations",
                        "default": "3mo"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Data interval",
                        "default": "1d"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_company_info",
            description="Get company information and fundamentals",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="analyze_trend",
            description="Analyze price trend and momentum",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol"
                    },
                    "period": {
                        "type": "string",
                        "description": "Analysis period",
                        "default": "1mo"
                    }
                },
                "required": ["symbol"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    try:
        if name == "get_quote":
            symbol = normalize_symbol(arguments["symbol"])
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get current quote
            hist = ticker.history(period="1d")
            if hist.empty:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"No data available for {symbol}"})
                )]

            current_price = float(hist['Close'].iloc[-1])
            volume = int(hist['Volume'].iloc[-1])

            # Calculate daily change
            open_price = float(hist['Open'].iloc[-1])
            change = current_price - open_price
            change_percent = (change / open_price) * 100

            quote_data = {
                "symbol": arguments["symbol"],
                "yf_symbol": symbol,
                "price": round(current_price, 2),
                "open": round(open_price, 2),
                "high": round(float(hist['High'].iloc[-1]), 2),
                "low": round(float(hist['Low'].iloc[-1]), 2),
                "volume": volume,
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "timestamp": datetime.now().isoformat()
            }

            return [TextContent(type="text", text=json.dumps(quote_data, indent=2))]

        elif name == "get_historical_data":
            symbol = normalize_symbol(arguments["symbol"])
            period = arguments.get("period", "1mo")
            interval = arguments.get("interval", "1d")

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)

            if hist.empty:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"No historical data for {symbol}"})
                )]

            # Convert to dict format
            data = {
                "symbol": arguments["symbol"],
                "period": period,
                "interval": interval,
                "data_points": len(hist),
                "start_date": hist.index[0].isoformat(),
                "end_date": hist.index[-1].isoformat(),
                "latest": {
                    "date": hist.index[-1].isoformat(),
                    "open": round(float(hist['Open'].iloc[-1]), 2),
                    "high": round(float(hist['High'].iloc[-1]), 2),
                    "low": round(float(hist['Low'].iloc[-1]), 2),
                    "close": round(float(hist['Close'].iloc[-1]), 2),
                    "volume": int(hist['Volume'].iloc[-1])
                },
                "prices": [
                    {
                        "date": idx.isoformat(),
                        "close": round(float(row['Close']), 2),
                        "volume": int(row['Volume'])
                    }
                    for idx, row in hist.tail(20).iterrows()
                ]
            }

            return [TextContent(type="text", text=json.dumps(data, indent=2))]

        elif name == "get_technical_indicators":
            symbol = normalize_symbol(arguments["symbol"])
            period = arguments.get("period", "3mo")
            interval = arguments.get("interval", "1d")

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)

            if hist.empty or len(hist) < 20:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Insufficient data for indicators"})
                )]

            closes = hist['Close']

            # Calculate indicators
            indicators = {
                "symbol": arguments["symbol"],
                "current_price": round(float(closes.iloc[-1]), 2),
                "sma_20": round(float(closes.rolling(window=20).mean().iloc[-1]), 2) if len(closes) >= 20 else None,
                "sma_50": round(float(closes.rolling(window=50).mean().iloc[-1]), 2) if len(closes) >= 50 else None,
                "sma_200": round(float(closes.rolling(window=200).mean().iloc[-1]), 2) if len(closes) >= 200 else None,
                "ema_12": round(float(closes.ewm(span=12, adjust=False).mean().iloc[-1]), 2),
                "ema_26": round(float(closes.ewm(span=26, adjust=False).mean().iloc[-1]), 2),
                "rsi_14": round(calculate_rsi(closes, 14), 2) if calculate_rsi(closes, 14) else None,
            }

            # MACD
            macd_data = calculate_macd(closes)
            if macd_data:
                indicators["macd"] = {
                    "macd": round(macd_data["macd"], 2),
                    "signal": round(macd_data["signal"], 2),
                    "histogram": round(macd_data["histogram"], 2)
                }

            # Bollinger Bands
            if len(closes) >= 20:
                sma20 = closes.rolling(window=20).mean()
                std20 = closes.rolling(window=20).std()
                indicators["bollinger_bands"] = {
                    "upper": round(float(sma20.iloc[-1] + 2 * std20.iloc[-1]), 2),
                    "middle": round(float(sma20.iloc[-1]), 2),
                    "lower": round(float(sma20.iloc[-1] - 2 * std20.iloc[-1]), 2)
                }

            return [TextContent(type="text", text=json.dumps(indicators, indent=2))]

        elif name == "get_company_info":
            symbol = normalize_symbol(arguments["symbol"])
            ticker = yf.Ticker(symbol)
            info = ticker.info

            company_data = {
                "symbol": arguments["symbol"],
                "name": info.get("longName", info.get("shortName", "N/A")),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "description": info.get("longBusinessSummary", "N/A")[:500]  # Truncate
            }

            return [TextContent(type="text", text=json.dumps(company_data, indent=2))]

        elif name == "analyze_trend":
            symbol = normalize_symbol(arguments["symbol"])
            period = arguments.get("period", "1mo")

            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if hist.empty or len(hist) < 5:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Insufficient data for trend analysis"})
                )]

            closes = hist['Close']

            # Calculate trend
            first_price = float(closes.iloc[0])
            last_price = float(closes.iloc[-1])
            change = last_price - first_price
            change_percent = (change / first_price) * 100

            # Determine trend direction
            if change_percent > 5:
                trend = "strong_uptrend"
            elif change_percent > 0:
                trend = "uptrend"
            elif change_percent > -5:
                trend = "downtrend"
            else:
                trend = "strong_downtrend"

            # Calculate volatility
            returns = closes.pct_change().dropna()
            volatility = float(returns.std()) * 100

            analysis = {
                "symbol": arguments["symbol"],
                "period": period,
                "start_price": round(first_price, 2),
                "end_price": round(last_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "trend": trend,
                "volatility": round(volatility, 2),
                "average_volume": int(hist['Volume'].mean()),
                "data_points": len(hist)
            }

            return [TextContent(type="text", text=json.dumps(analysis, indent=2))]

        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"})
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
