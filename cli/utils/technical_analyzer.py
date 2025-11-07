"""
Technical Analysis Signal Generator.

This module provides traditional (non-AI) technical analysis calculations
and converts them into structured trading signals with confidence scores.

Purpose: Optimize decision-making by pre-computing TA signals so the LLM
only needs to synthesize pre-digested information instead of raw numbers.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import time
from cli.utils.logger import get_logger

logger = get_logger(__name__)


class SignalType(Enum):
    """Types of technical signals."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class TechnicalSignal:
    """A single technical analysis signal with confidence score."""
    indicator: str  # e.g., "rsi", "macd", "sma_crossover"
    signal: SignalType  # bullish, bearish, neutral
    confidence: float  # 0.0 to 1.0
    value: Optional[float] = None  # The actual indicator value
    reasoning: str = ""  # Human-readable explanation


@dataclass
class TechnicalAnalysis:
    """Complete technical analysis with multiple signals."""
    symbol: str
    timestamp: str
    signals: List[TechnicalSignal]
    overall_signal: SignalType
    overall_confidence: float
    computation_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/LLM consumption."""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "overall_signal": self.overall_signal.value,
            "overall_confidence": round(self.overall_confidence, 2),
            "computation_time_ms": round(self.computation_time_ms, 2),
            "signals": [
                {
                    "indicator": s.indicator,
                    "signal": s.signal.value,
                    "confidence": round(s.confidence, 2),
                    "value": s.value,
                    "reasoning": s.reasoning
                }
                for s in self.signals
            ]
        }


class TechnicalAnalyzer:
    """
    Fast, deterministic technical analysis using traditional methods.

    Converts raw market data into structured signals for LLM consumption.
    All calculations are transparent and auditable.
    """

    def analyze(self, market_context: Dict[str, Any]) -> TechnicalAnalysis:
        """
        Analyze market context and generate technical signals.

        Args:
            market_context: Output from MarketDataProvider.get_market_context()

        Returns:
            TechnicalAnalysis with structured signals and overall assessment
        """
        start_time = time.time()

        symbol = market_context.get("symbol", "UNKNOWN")
        timestamp = market_context.get("timestamp", "")

        signals: List[TechnicalSignal] = []

        # Extract indicators from market context
        indicators = market_context.get("technical_indicators", {})
        trend = market_context.get("trend_analysis", {})
        levels = market_context.get("levels", {})
        volume = market_context.get("volume_analysis", {})
        price_action = market_context.get("price_action", {})
        current_price = market_context.get("current_price", 0)

        # RSI Signal
        if "rsi_14" in indicators:
            signals.append(self._analyze_rsi(indicators["rsi_14"]))

        # SMA Signal (price vs moving average)
        if "price_vs_sma20" in indicators:
            signals.append(
                self._analyze_sma_position(indicators["price_vs_sma20"], indicators.get("sma_20"))
            )

        # Trend Signal
        if trend and trend.get("trend") != "unknown":
            signals.append(self._analyze_trend(trend))

        # Support/Resistance Signal
        if levels and current_price > 0:
            signals.append(self._analyze_levels(levels, current_price))

        # Volume Signal
        if volume and volume.get("volume_trend") != "unknown":
            signals.append(self._analyze_volume(volume))

        # Price Action Signal
        if price_action and "pattern" in price_action:
            signals.append(self._analyze_price_action(price_action))

        # Calculate overall signal and confidence
        overall_signal, overall_confidence = self._synthesize_signals(signals)

        computation_time_ms = (time.time() - start_time) * 1000

        analysis = TechnicalAnalysis(
            symbol=symbol,
            timestamp=timestamp,
            signals=signals,
            overall_signal=overall_signal,
            overall_confidence=overall_confidence,
            computation_time_ms=computation_time_ms
        )

        logger.info(
            f"Technical analysis for {symbol}: {overall_signal.value} "
            f"(confidence: {overall_confidence:.2f}) in {computation_time_ms:.1f}ms"
        )

        return analysis

    def _analyze_rsi(self, rsi: float) -> TechnicalSignal:
        """Analyze RSI and return signal."""
        if rsi < 30:
            return TechnicalSignal(
                indicator="rsi",
                signal=SignalType.BULLISH,
                confidence=min((30 - rsi) / 10, 1.0),  # Stronger as it gets lower
                value=rsi,
                reasoning=f"RSI at {rsi:.1f} suggests oversold conditions"
            )
        elif rsi > 70:
            return TechnicalSignal(
                indicator="rsi",
                signal=SignalType.BEARISH,
                confidence=min((rsi - 70) / 10, 1.0),
                value=rsi,
                reasoning=f"RSI at {rsi:.1f} suggests overbought conditions"
            )
        else:
            return TechnicalSignal(
                indicator="rsi",
                signal=SignalType.NEUTRAL,
                confidence=1.0 - abs(rsi - 50) / 20,  # Most neutral at 50
                value=rsi,
                reasoning=f"RSI at {rsi:.1f} is in neutral zone"
            )

    def _analyze_sma_position(
        self, price_vs_sma: float, sma_value: Optional[float]
    ) -> TechnicalSignal:
        """Analyze price position relative to SMA."""
        if price_vs_sma > 2:  # Price > 2% above SMA
            return TechnicalSignal(
                indicator="sma_20",
                signal=SignalType.BULLISH,
                confidence=min(abs(price_vs_sma) / 5, 1.0),
                value=sma_value,
                reasoning=f"Price {price_vs_sma:.1f}% above 20-period SMA (bullish momentum)"
            )
        elif price_vs_sma < -2:  # Price > 2% below SMA
            return TechnicalSignal(
                indicator="sma_20",
                signal=SignalType.BEARISH,
                confidence=min(abs(price_vs_sma) / 5, 1.0),
                value=sma_value,
                reasoning=f"Price {price_vs_sma:.1f}% below 20-period SMA (bearish momentum)"
            )
        else:
            return TechnicalSignal(
                indicator="sma_20",
                signal=SignalType.NEUTRAL,
                confidence=0.5,
                value=sma_value,
                reasoning=f"Price near 20-period SMA ({price_vs_sma:+.1f}%)"
            )

    def _analyze_trend(self, trend: Dict[str, Any]) -> TechnicalSignal:
        """Analyze trend direction and strength."""
        trend_direction = trend.get("trend", "sideways")
        strength = trend.get("strength", 0)
        change_pct = trend.get("change_pct", 0)

        if trend_direction == "bullish":
            return TechnicalSignal(
                indicator="trend",
                signal=SignalType.BULLISH,
                confidence=strength,
                value=change_pct,
                reasoning=f"Bullish trend with {change_pct:+.1f}% change (strength: {strength:.2f})"
            )
        elif trend_direction == "bearish":
            return TechnicalSignal(
                indicator="trend",
                signal=SignalType.BEARISH,
                confidence=strength,
                value=change_pct,
                reasoning=f"Bearish trend with {change_pct:+.1f}% change (strength: {strength:.2f})"
            )
        else:
            return TechnicalSignal(
                indicator="trend",
                signal=SignalType.NEUTRAL,
                confidence=0.5,
                value=change_pct,
                reasoning="Sideways/choppy trend with no clear direction"
            )

    def _analyze_levels(
        self, levels: Dict[str, Any], current_price: float
    ) -> TechnicalSignal:
        """Analyze support/resistance levels."""
        dist_to_support = levels.get("distance_to_support_pct", 0)
        dist_to_resistance = levels.get("distance_to_resistance_pct", 0)

        # Near support = potential bounce (bullish)
        if dist_to_support < 2:
            return TechnicalSignal(
                indicator="support_resistance",
                signal=SignalType.BULLISH,
                confidence=max(0.6, 1.0 - dist_to_support / 2),
                value=current_price,
                reasoning=f"Price near support level ({dist_to_support:.1f}% above) - potential bounce"
            )
        # Near resistance = potential rejection (bearish)
        elif dist_to_resistance < 2:
            return TechnicalSignal(
                indicator="support_resistance",
                signal=SignalType.BEARISH,
                confidence=max(0.6, 1.0 - dist_to_resistance / 2),
                value=current_price,
                reasoning=f"Price near resistance level ({dist_to_resistance:.1f}% below) - potential rejection"
            )
        else:
            return TechnicalSignal(
                indicator="support_resistance",
                signal=SignalType.NEUTRAL,
                confidence=0.4,
                value=current_price,
                reasoning="Price in mid-range between support and resistance"
            )

    def _analyze_volume(self, volume: Dict[str, Any]) -> TechnicalSignal:
        """Analyze volume trends."""
        volume_trend = volume.get("volume_trend", "normal")
        volume_ratio = volume.get("volume_ratio", 1.0)

        if volume_trend == "high":
            # High volume can confirm trend, assign moderate confidence
            return TechnicalSignal(
                indicator="volume",
                signal=SignalType.NEUTRAL,  # Volume alone doesn't indicate direction
                confidence=0.7,
                value=volume_ratio,
                reasoning=f"High volume ({volume_ratio:.1f}x average) - strong participation"
            )
        elif volume_trend == "low":
            return TechnicalSignal(
                indicator="volume",
                signal=SignalType.NEUTRAL,
                confidence=0.3,
                value=volume_ratio,
                reasoning=f"Low volume ({volume_ratio:.1f}x average) - weak conviction"
            )
        else:
            return TechnicalSignal(
                indicator="volume",
                signal=SignalType.NEUTRAL,
                confidence=0.5,
                value=volume_ratio,
                reasoning="Normal volume levels"
            )

    def _analyze_price_action(self, price_action: Dict[str, Any]) -> TechnicalSignal:
        """Analyze price action patterns."""
        pattern = price_action.get("pattern", "choppy")

        pattern_signals = {
            "strong_uptrend": (SignalType.BULLISH, 0.85, "Strong uptrend (higher highs and lows)"),
            "strong_downtrend": (SignalType.BEARISH, 0.85, "Strong downtrend (lower highs and lows)"),
            "bullish_consolidation": (SignalType.BULLISH, 0.65, "Bullish consolidation (higher lows)"),
            "bearish_consolidation": (SignalType.BEARISH, 0.65, "Bearish consolidation (lower highs)"),
            "choppy": (SignalType.NEUTRAL, 0.3, "Choppy price action - no clear pattern"),
        }

        signal_type, confidence, reasoning = pattern_signals.get(
            pattern, (SignalType.NEUTRAL, 0.5, f"Price action: {pattern}")
        )

        return TechnicalSignal(
            indicator="price_action",
            signal=signal_type,
            confidence=confidence,
            value=None,
            reasoning=reasoning
        )

    def _synthesize_signals(
        self, signals: List[TechnicalSignal]
    ) -> tuple[SignalType, float]:
        """
        Synthesize multiple signals into overall assessment.

        Returns:
            Tuple of (overall_signal, overall_confidence)
        """
        if not signals:
            return SignalType.NEUTRAL, 0.0

        # Weighted voting system
        bullish_score = 0.0
        bearish_score = 0.0
        neutral_score = 0.0

        for signal in signals:
            weight = signal.confidence
            if signal.signal == SignalType.BULLISH:
                bullish_score += weight
            elif signal.signal == SignalType.BEARISH:
                bearish_score += weight
            else:
                neutral_score += weight

        total_score = bullish_score + bearish_score + neutral_score

        if total_score == 0:
            return SignalType.NEUTRAL, 0.0

        # Determine overall signal based on highest score
        if bullish_score > bearish_score and bullish_score > neutral_score:
            return SignalType.BULLISH, bullish_score / total_score
        elif bearish_score > bullish_score and bearish_score > neutral_score:
            return SignalType.BEARISH, bearish_score / total_score
        else:
            return SignalType.NEUTRAL, neutral_score / total_score


def get_technical_analyzer() -> TechnicalAnalyzer:
    """Factory function to get technical analyzer."""
    return TechnicalAnalyzer()
