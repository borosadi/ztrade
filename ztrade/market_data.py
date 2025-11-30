"""Market data and technical analysis utilities."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ztrade.broker import get_broker
from ztrade.core.mcp_client import get_mcp_client
from ztrade.sentiment.aggregator import get_sentiment_aggregator
from ztrade.core.database import market_data_store
from ztrade.core.logger import get_logger

logger = get_logger(__name__)


class MarketDataProvider:
    """Provides market data and technical analysis for trading decisions."""

    def __init__(self):
        self.broker = get_broker()
        self.mcp_client = get_mcp_client()
        self.sentiment_aggregator = get_sentiment_aggregator()

    def get_market_context(
        self, symbol: str, timeframe: str = "15m", lookback_periods: int = 100
    ) -> Dict[str, Any]:
        """
        Get comprehensive market context for a symbol.

        Args:
            symbol: Asset symbol (e.g., 'TSLA', 'IWM', 'BTC/USD')
            timeframe: Time interval (5m, 15m, 1h, 4h, daily)
            lookback_periods: Number of historical periods to analyze

        Returns:
            Dict with market context including:
            - current_price
            - price_change_24h
            - volume_analysis
            - technical_indicators
            - trend_analysis
            - support_resistance levels
        """
        context = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Get current price from Alpaca (primary) or MCP (fallback)
            try:
                # Try Alpaca first for real-time data
                quote = self.broker.get_latest_quote(symbol)
                if quote:
                    context["current_price"] = quote.get("ask", quote.get("bid", 0))
                    context["quote"] = {
                        "symbol": symbol,
                        "bid": quote.get("bid", 0),
                        "ask": quote.get("ask", 0),
                        "price": quote.get("ask", quote.get("bid", 0))
                    }
                    logger.info(f"Alpaca quote for {symbol}: ${context['current_price']:.2f}")
                else:
                    # Fallback to Yahoo Finance via MCP
                    quote_data = self.mcp_client.get_quote(symbol)
                    if "error" not in quote_data:
                        context["current_price"] = quote_data.get("price", 0)
                        context["quote"] = quote_data
                    else:
                        logger.warning(f"No quote available for {symbol}")
                        context["current_price"] = 0
            except Exception as e:
                logger.warning(f"Could not fetch quote for {symbol}: {e}")
                context["current_price"] = 0

            # Get technical indicators from MCP
            try:
                indicators = self.mcp_client.get_technical_indicators(symbol, period="3mo", interval=self._convert_timeframe(timeframe))
                if "error" not in indicators:
                    context["technical_indicators"] = indicators
            except Exception as e:
                logger.warning(f"Could not fetch indicators for {symbol}: {e}")

            # Get trend analysis from MCP
            try:
                trend = self.mcp_client.analyze_trend(symbol, period="1mo")
                if "error" not in trend:
                    context["trend_analysis"] = trend
            except Exception as e:
                logger.warning(f"Could not fetch trend for {symbol}: {e}")

            # Get multi-source sentiment analysis (News + Reddit + SEC)
            try:
                sentiment = self.sentiment_aggregator.get_aggregated_sentiment(
                    symbol,
                    news_lookback_hours=24,
                    reddit_lookback_hours=24,
                    sec_lookback_days=30
                )
                if "error" not in sentiment:
                    context["sentiment"] = sentiment
                    sources_str = ", ".join(sentiment.get("sources_used", []))
                    logger.info(
                        f"Aggregated sentiment for {symbol}: {sentiment['overall_sentiment']} "
                        f"(score: {sentiment['sentiment_score']}, "
                        f"confidence: {sentiment['confidence']}, "
                        f"sources: {sources_str}, "
                        f"agreement: {sentiment.get('agreement_level', 0):.0%})"
                    )
            except Exception as e:
                logger.warning(f"Could not fetch aggregated sentiment for {symbol}: {e}")

            # Get historical bars for additional analysis
            bars = self._get_historical_bars(symbol, timeframe, lookback_periods)

            if bars and len(bars) > 0:
                # Store bars in context for technical analyzer
                context["bars"] = bars

                context["historical_data"] = {
                    "bars_count": len(bars),
                    "oldest_timestamp": bars[0]["timestamp"],
                    "newest_timestamp": bars[-1]["timestamp"],
                }

                # Calculate technical indicators
                context["technical_indicators"] = self._calculate_indicators(bars)

                # Analyze trend
                context["trend_analysis"] = self._analyze_trend(bars)

                # Find support/resistance
                context["levels"] = self._find_support_resistance(bars)

                # Volume analysis
                context["volume_analysis"] = self._analyze_volume(bars)

                # Price action
                context["price_action"] = self._analyze_price_action(bars)
            else:
                logger.warning(f"No historical data available for {symbol}")
                context["bars"] = []
                context["data_available"] = False

        except Exception as e:
            logger.error(f"Error getting market context for {symbol}: {e}")
            context["error"] = str(e)

        return context

    def _convert_timeframe(self, timeframe: str) -> str:
        """Convert agent timeframe to Yahoo Finance interval."""
        mapping = {
            "5m": "5m",
            "15m": "15m",
            "1h": "1h",
            "4h": "1h",  # Yahoo doesn't have 4h, use 1h
            "daily": "1d",
            "1d": "1d"
        }
        return mapping.get(timeframe, "1d")

    def _get_historical_bars(
        self, symbol: str, timeframe: str, lookback: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical price bars from database (primary) or MCP (fallback).

        Args:
            symbol: Asset symbol
            timeframe: Time interval
            lookback: Number of periods

        Returns:
            List of bar dictionaries with OHLCV data
        """
        logger.info(f"Fetching {lookback} {timeframe} bars for {symbol}")

        try:
            # Try database first
            db_bars = market_data_store.get_latest_bars(symbol, timeframe, lookback)

            if db_bars and len(db_bars) >= min(lookback // 2, 20):
                logger.info(f"Fetched {len(db_bars)} bars from database for {symbol}")
                # Convert database format to expected format and reverse order (oldest first)
                bars = []
                for bar in reversed(db_bars):  # Database returns newest first
                    bars.append({
                        "timestamp": bar["timestamp"].isoformat() if hasattr(bar["timestamp"], "isoformat") else str(bar["timestamp"]),
                        "open": float(bar["open"]),
                        "high": float(bar["high"]),
                        "low": float(bar["low"]),
                        "close": float(bar["close"]),
                        "volume": int(bar["volume"]) if bar["volume"] else 0,
                    })
                return bars

            # Fallback to MCP if insufficient database data
            logger.info(f"Database has {len(db_bars) if db_bars else 0} bars, falling back to MCP")

            # Determine period based on lookback and timeframe
            interval = self._convert_timeframe(timeframe)

            # Calculate appropriate period
            if "m" in interval:  # minutes
                period = "5d"  # 5 days of minute data
            elif "h" in interval:  # hours
                period = "1mo"  # 1 month of hourly data
            else:  # daily
                period = "1y"  # 1 year of daily data

            # Get data from MCP
            hist_data = self.mcp_client.get_historical_data(
                symbol, period=period, interval=interval
            )

            if "error" in hist_data:
                logger.warning(f"Error fetching historical data: {hist_data['error']}")
                return []

            # Convert to bar format
            bars = []
            for price_point in hist_data.get("prices", []):
                bars.append({
                    "timestamp": price_point["date"],
                    "close": price_point["close"],
                    "volume": price_point["volume"],
                    "open": price_point.get("open", price_point["close"]),
                    "high": price_point.get("high", price_point["close"]),
                    "low": price_point.get("low", price_point["close"]),
                })

            logger.info(f"Fetched {len(bars)} bars for {symbol}")
            return bars

        except Exception as e:
            logger.error(f"Error fetching historical bars for {symbol}: {e}")
            return []

    def _calculate_indicators(self, bars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate technical indicators from price bars."""
        if not bars or len(bars) < 20:
            return {"insufficient_data": True}

        closes = [bar["close"] for bar in bars]

        indicators = {}

        # Simple Moving Averages
        if len(closes) >= 20:
            indicators["sma_20"] = sum(closes[-20:]) / 20

        if len(closes) >= 50:
            indicators["sma_50"] = sum(closes[-50:]) / 50

        # RSI (simplified)
        if len(closes) >= 14:
            indicators["rsi_14"] = self._calculate_rsi(closes, 14)

        # Current vs SMA (momentum)
        if "sma_20" in indicators:
            current = closes[-1]
            indicators["price_vs_sma20"] = (
                (current - indicators["sma_20"]) / indicators["sma_20"]
            ) * 100

        return indicators

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return 50.0  # Neutral

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    def _analyze_trend(self, bars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze price trend."""
        if len(bars) < 10:
            return {"trend": "unknown", "strength": 0}

        closes = [bar["close"] for bar in bars]

        # Simple trend detection
        recent_closes = closes[-10:]
        first_half_avg = sum(recent_closes[:5]) / 5
        second_half_avg = sum(recent_closes[5:]) / 5

        change_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100

        if change_pct > 2:
            trend = "bullish"
            strength = min(abs(change_pct) / 5, 1.0)  # 0-1 scale
        elif change_pct < -2:
            trend = "bearish"
            strength = min(abs(change_pct) / 5, 1.0)
        else:
            trend = "sideways"
            strength = 0.5

        return {
            "trend": trend,
            "strength": round(strength, 2),
            "change_pct": round(change_pct, 2),
        }

    def _find_support_resistance(self, bars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find support and resistance levels."""
        if len(bars) < 20:
            return {}

        highs = [bar["high"] for bar in bars[-20:]]
        lows = [bar["low"] for bar in bars[-20:]]

        resistance = max(highs)
        support = min(lows)

        current = bars[-1]["close"]

        return {
            "support": round(support, 2),
            "resistance": round(resistance, 2),
            "distance_to_support_pct": round(
                ((current - support) / support) * 100, 2
            ),
            "distance_to_resistance_pct": round(
                ((resistance - current) / current) * 100, 2
            ),
        }

    def _analyze_volume(self, bars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze volume patterns."""
        if len(bars) < 20:
            return {"volume_trend": "unknown"}

        volumes = [bar.get("volume", 0) for bar in bars]

        avg_volume = sum(volumes[-20:]) / 20
        recent_volume = volumes[-1]

        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1

        if volume_ratio > 1.5:
            volume_trend = "high"
        elif volume_ratio < 0.5:
            volume_trend = "low"
        else:
            volume_trend = "normal"

        return {
            "volume_trend": volume_trend,
            "volume_ratio": round(volume_ratio, 2),
            "avg_volume": round(avg_volume, 2),
            "current_volume": round(recent_volume, 2),
        }

    def _analyze_price_action(self, bars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze recent price action."""
        if len(bars) < 5:
            return {}

        recent_bars = bars[-5:]

        # Check for higher highs / lower lows
        highs = [bar["high"] for bar in recent_bars]
        lows = [bar["low"] for bar in recent_bars]

        higher_highs = all(highs[i] >= highs[i - 1] for i in range(1, len(highs)))
        higher_lows = all(lows[i] >= lows[i - 1] for i in range(1, len(lows)))
        lower_highs = all(highs[i] <= highs[i - 1] for i in range(1, len(highs)))
        lower_lows = all(lows[i] <= lows[i - 1] for i in range(1, len(lows)))

        if higher_highs and higher_lows:
            pattern = "strong_uptrend"
        elif lower_highs and lower_lows:
            pattern = "strong_downtrend"
        elif higher_lows and not lower_highs:
            pattern = "bullish_consolidation"
        elif lower_highs and not higher_lows:
            pattern = "bearish_consolidation"
        else:
            pattern = "choppy"

        return {"pattern": pattern, "bars_analyzed": len(recent_bars)}


def get_market_data_provider() -> MarketDataProvider:
    """Factory function to get market data provider."""
    return MarketDataProvider()
