#!/usr/bin/env python3
"""Improved Technical Analysis with market regime detection and multi-timeframe confirmation.

Key improvements over base analyzer:
1. Market regime detection (trending vs ranging) - skip neutral/choppy markets
2. Multi-timeframe confirmation (5m signal + 1h trend alignment)
3. Fixed inverted signal logic for strong_sell
4. Volatility-based filters and position sizing
5. Stricter entry criteria to reduce overtrading
"""
import statistics
from typing import Dict, Tuple, List, Optional
from datetime import datetime, timedelta


# === EMBEDDED TECHNICAL INDICATORS ===

def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """Calculate RSI indicator."""
    if len(prices) < period + 1:
        return [None] * len(prices)

    rsi_values = [None] * period

    # Calculate first average gain and loss
    first_gains = []
    first_losses = []

    for i in range(1, period + 1):
        change = prices[i] - prices[i-1]
        first_gains.append(max(0, change))
        first_losses.append(max(0, -change))

    avg_gain = sum(first_gains) / period
    avg_loss = sum(first_losses) / period

    # Calculate RSI for rest of periods
    for i in range(period, len(prices)):
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)

        # Update averages for next iteration
        if i < len(prices) - 1:
            change = prices[i+1] - prices[i]
            current_gain = max(0, change)
            current_loss = max(0, -change)
            avg_gain = (avg_gain * (period - 1) + current_gain) / period
            avg_loss = (avg_loss * (period - 1) + current_loss) / period

    return rsi_values


def calculate_sma(prices: List[float], period: int = 20) -> List[Optional[float]]:
    """Calculate Simple Moving Average."""
    sma = [None] * (period - 1)

    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        sma.append(sum(window) / period)

    return sma


def detect_trend(prices: List[float], lookback: int = 100) -> Tuple[str, float]:
    """Detect trend from price data."""
    if len(prices) < lookback:
        return 'neutral', 0.0

    recent = prices[-lookback:] if len(prices) > lookback else prices
    first_third = recent[:len(recent)//3]
    last_third = recent[-len(recent)//3:]

    avg_first = sum(first_third) / len(first_third)
    avg_last = sum(last_third) / len(last_third)

    pct_change = (avg_last - avg_first) / avg_first * 100

    # Lower thresholds for 5-minute timeframe (smaller moves than daily)
    # Changed from 2.0% to 1.0% to capture more trends
    if pct_change > 1.0:  # Was 2.0
        return 'bullish', abs(pct_change)
    elif pct_change < -1.0:  # Was -2.0
        return 'bearish', abs(pct_change)
    else:
        return 'neutral', abs(pct_change)


class MarketRegime:
    """Market regime classification."""
    STRONG_TREND = "strong_trend"  # Clear directional move - trade aggressively
    WEAK_TREND = "weak_trend"      # Developing trend - trade cautiously
    RANGING = "ranging"            # Choppy/sideways - avoid trading
    HIGH_VOLATILITY = "high_vol"   # Volatile - reduce position size


def detect_market_regime(
    closes: List[float],
    highs: List[float],
    lows: List[float],
    lookback: int = 100
) -> Tuple[str, float]:
    """Detect market regime using multiple metrics.

    Args:
        closes: Price closes
        highs: Price highs
        lows: Price lows
        lookback: Bars to analyze

    Returns:
        (regime, strength): Regime type and strength score 0-1
    """
    if len(closes) < lookback:
        return MarketRegime.RANGING, 0.0

    recent = closes[-lookback:]
    recent_highs = highs[-lookback:]
    recent_lows = lows[-lookback:]

    # 1. Trend strength (directional movement)
    first_third = recent[:lookback//3]
    last_third = recent[-lookback//3:]
    avg_first = statistics.mean(first_third)
    avg_last = statistics.mean(last_third)
    trend_pct = abs((avg_last - avg_first) / avg_first * 100)

    # 2. Trend consistency (how smooth is the trend)
    sma_20 = calculate_sma(recent, period=20)
    valid_sma = [s for s in sma_20 if s is not None]
    if valid_sma:
        price_vs_sma = [abs(p - s) / s * 100 for p, s in zip(recent[-len(valid_sma):], valid_sma)]
        consistency = 1.0 - min(statistics.mean(price_vs_sma) / 5.0, 1.0)  # Normalize to 0-1
    else:
        consistency = 0.0

    # 3. Volatility level
    avg_price = statistics.mean(recent)
    volatility_pct = (max(recent_highs) - min(recent_lows)) / avg_price * 100

    # 4. ADX-like directional movement
    up_moves = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i-1])
    directional_ratio = up_moves / (len(recent) - 1) if len(recent) > 1 else 0.5
    directional_strength = abs(directional_ratio - 0.5) * 2  # 0 = random, 1 = one direction

    # Classify regime
    if volatility_pct > 8.0:
        return MarketRegime.HIGH_VOLATILITY, min(volatility_pct / 15.0, 1.0)

    # Strong trend: high directional movement + good consistency
    if trend_pct > 3.0 and consistency > 0.6 and directional_strength > 0.6:
        strength = min((trend_pct / 5.0 + consistency + directional_strength) / 3.0, 1.0)
        return MarketRegime.STRONG_TREND, strength

    # Weak trend: moderate movement
    if trend_pct > 1.0 and directional_strength > 0.4:
        strength = min((trend_pct / 3.0 + directional_strength) / 2.0, 1.0)
        return MarketRegime.WEAK_TREND, strength

    # Ranging: low directional movement
    strength = 1.0 - min(trend_pct / 2.0, 1.0)
    return MarketRegime.RANGING, strength


def get_volatility_multiplier(volatility_pct: float) -> float:
    """Get position size multiplier based on volatility.

    Args:
        volatility_pct: 20-bar rolling volatility percentage

    Returns:
        Multiplier 0.5-1.0 for position sizing
    """
    if volatility_pct < 2.0:
        return 1.0  # Normal size
    elif volatility_pct < 4.0:
        return 0.8  # Reduce 20%
    elif volatility_pct < 7.0:
        return 0.6  # Reduce 40%
    else:
        return 0.5  # Reduce 50% in high volatility


def analyze_improved(
    symbol: str,
    closes: List[float],
    highs: List[float],
    lows: List[float],
    volumes: List[float],
    hourly_closes: Optional[List[float]] = None
) -> Dict:
    """Improved technical analysis with regime detection.

    Args:
        symbol: Asset symbol
        closes: 5-minute close prices (or primary timeframe)
        highs: High prices
        lows: Low prices
        volumes: Volume data
        hourly_closes: Optional 1-hour closes for multi-timeframe confirmation

    Returns:
        Analysis dict with signal, confidence, regime, etc.
    """
    if len(closes) < 100:
        return {
            'signal': 'neutral',
            'confidence': 0.0,
            'reason': 'Insufficient data',
            'regime': MarketRegime.RANGING,
            'regime_strength': 0.0
        }

    # Calculate indicators
    rsi_values = calculate_rsi(closes, period=14)
    sma_short = calculate_sma(closes, period=20)
    sma_long = calculate_sma(closes, period=50)

    current_price = closes[-1]
    current_rsi = rsi_values[-1] if rsi_values[-1] is not None else 50
    current_sma_short = sma_short[-1]
    current_sma_long = sma_long[-1]

    # Detect market regime (CRITICAL - skip ranging markets)
    regime, regime_strength = detect_market_regime(closes, highs, lows, lookback=100)

    # Calculate volatility for position sizing
    recent_highs = highs[-20:]
    recent_lows = lows[-20:]
    recent_closes = closes[-20:]
    avg_price = statistics.mean(recent_closes)
    volatility_pct = (max(recent_highs) - min(recent_lows)) / avg_price * 100
    vol_multiplier = get_volatility_multiplier(volatility_pct)

    # Detect primary trend
    trend, trend_strength = detect_trend(closes[-100:])

    # Multi-timeframe confirmation (if hourly data available)
    hourly_trend = 'neutral'
    if hourly_closes and len(hourly_closes) >= 24:
        hourly_trend, _ = detect_trend(hourly_closes[-24:])  # Last 24 hours

    # === FILTERING RULES ===

    # FILTER 1 (REMOVED): Previously blocked all RANGING markets hard-coded
    # Now relies on regime_strength threshold below for quality filtering

    # FILTER 2: Require minimum regime strength
    if regime_strength < 0.5:
        return {
            'signal': 'neutral',
            'confidence': 0.0,
            'reason': f'Weak regime strength: {regime_strength:.2f}',
            'regime': regime,
            'regime_strength': regime_strength,
            'volatility_pct': volatility_pct,
            'vol_multiplier': vol_multiplier
        }

    # FILTER 3: Multi-timeframe alignment (if available)
    if hourly_closes and len(hourly_closes) >= 24:
        if trend == 'bullish' and hourly_trend not in ['bullish', 'neutral']:
            return {
                'signal': 'neutral',
                'confidence': 0.0,
                'reason': f'Timeframe misalignment: 5m {trend} vs 1h {hourly_trend}',
                'regime': regime,
                'regime_strength': regime_strength,
                'volatility_pct': volatility_pct,
                'vol_multiplier': vol_multiplier
            }
        elif trend == 'bearish' and hourly_trend not in ['bearish', 'neutral']:
            return {
                'signal': 'neutral',
                'confidence': 0.0,
                'reason': f'Timeframe misalignment: 5m {trend} vs 1h {hourly_trend}',
                'regime': regime,
                'regime_strength': regime_strength,
                'volatility_pct': volatility_pct,
                'vol_multiplier': vol_multiplier
            }

    # === SIGNAL GENERATION (Fixed logic) ===

    signal = 'neutral'
    confidence = 0.0
    reason = ''

    # STRONG BUY: Bullish trend + oversold RSI + price below SMA (bounce setup)
    # Now allows RANGING markets (mean reversion) - quality controlled by regime_strength filter
    if (trend == 'bullish' and
        current_rsi < 35 and
        current_price < current_sma_short and
        regime in [MarketRegime.STRONG_TREND, MarketRegime.WEAK_TREND, MarketRegime.RANGING]):

        signal = 'buy'
        # Confidence based on regime strength and RSI oversold depth
        rsi_factor = (35 - current_rsi) / 35  # 0-1, higher when more oversold
        confidence = min((regime_strength + rsi_factor) / 2.0, 1.0)
        reason = f'Bullish trend + oversold RSI {current_rsi:.1f}'

    # STRONG SELL: Bearish trend + overbought RSI + price above SMA (rollover setup)
    # FIXED: This should profit when price FALLS, so we SELL when overbought in downtrend
    # Now allows RANGING markets (mean reversion) - quality controlled by regime_strength filter
    elif (trend == 'bearish' and
          current_rsi > 65 and
          current_price > current_sma_short and
          regime in [MarketRegime.STRONG_TREND, MarketRegime.WEAK_TREND, MarketRegime.RANGING]):

        signal = 'sell'
        # Confidence based on regime strength and RSI overbought level
        rsi_factor = (current_rsi - 65) / 35  # 0-1, higher when more overbought
        confidence = min((regime_strength + rsi_factor) / 2.0, 1.0)
        reason = f'Bearish trend + overbought RSI {current_rsi:.1f}'

    # MOMENTUM BUY: Strong bullish trend + price breaking above SMA
    elif (trend == 'bullish' and
          current_rsi > 50 and current_rsi < 70 and
          current_price > current_sma_short and
          current_price > current_sma_long and
          regime == MarketRegime.STRONG_TREND):

        signal = 'buy'
        confidence = min(regime_strength * 0.8, 0.80)  # Cap at 80% for momentum
        reason = f'Strong bullish momentum, RSI {current_rsi:.1f}'

    # MOMENTUM SELL: Strong bearish trend + price breaking below SMA
    elif (trend == 'bearish' and
          current_rsi < 50 and current_rsi > 30 and
          current_price < current_sma_short and
          current_price < current_sma_long and
          regime == MarketRegime.STRONG_TREND):

        signal = 'sell'
        confidence = min(regime_strength * 0.8, 0.80)  # Cap at 80% for momentum
        reason = f'Strong bearish momentum, RSI {current_rsi:.1f}'

    # VOLATILITY BREAKOUT BUY: High volatility + strong bullish trend
    # Trade high-vol markets ONLY when there's clear directional movement
    elif (regime == MarketRegime.HIGH_VOLATILITY and
          trend == 'bullish' and
          trend_strength > 1.5 and  # Strong trend (> 1.5% move)
          current_rsi < 70):  # Not overbought

        signal = 'buy'
        # Conservative confidence for volatile markets
        confidence = min(trend_strength / 5.0, 0.70)  # Cap at 70%
        reason = f'Volatility breakout: bullish with {trend_strength:.1f}% trend'

    # VOLATILITY BREAKOUT SELL: High volatility + strong bearish trend
    elif (regime == MarketRegime.HIGH_VOLATILITY and
          trend == 'bearish' and
          trend_strength > 1.5 and  # Strong trend (> 1.5% move)
          current_rsi > 30):  # Not oversold

        signal = 'sell'
        # Conservative confidence for volatile markets
        confidence = min(trend_strength / 5.0, 0.70)  # Cap at 70%
        reason = f'Volatility breakout: bearish with {trend_strength:.1f}% trend'

    # Adjust confidence for volatility
    final_confidence = confidence * vol_multiplier

    return {
        'signal': signal,
        'confidence': final_confidence,
        'reason': reason,
        'regime': regime,
        'regime_strength': regime_strength,
        'volatility_pct': volatility_pct,
        'vol_multiplier': vol_multiplier,
        'trend': trend,
        'trend_strength': trend_strength,
        'hourly_trend': hourly_trend,
        'rsi': current_rsi,
        'price_vs_sma': (current_price / current_sma_short - 1) * 100 if current_sma_short else 0
    }


if __name__ == '__main__':
    # Test the improved analyzer
    import random

    print("Testing improved technical analyzer...\n")

    # Simulate trending market
    print("=== TRENDING MARKET (Bullish) ===")
    trend_closes = [100 + i * 0.5 + random.uniform(-1, 1) for i in range(150)]
    trend_highs = [c + random.uniform(0.5, 1.5) for c in trend_closes]
    trend_lows = [c - random.uniform(0.5, 1.5) for c in trend_closes]
    trend_volumes = [1000000] * 150

    result = analyze_improved('TEST', trend_closes, trend_highs, trend_lows, trend_volumes)
    print(f"Signal: {result['signal']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Regime: {result['regime']} (strength: {result['regime_strength']:.2f})")
    print(f"Reason: {result['reason']}\n")

    # Simulate ranging market
    print("=== RANGING MARKET (Choppy) ===")
    range_closes = [100 + random.uniform(-3, 3) for _ in range(150)]
    range_highs = [c + random.uniform(0.5, 1.5) for c in range_closes]
    range_lows = [c - random.uniform(0.5, 1.5) for c in range_closes]
    range_volumes = [1000000] * 150

    result = analyze_improved('TEST', range_closes, range_highs, range_lows, range_volumes)
    print(f"Signal: {result['signal']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Regime: {result['regime']} (strength: {result['regime_strength']:.2f})")
    print(f"Reason: {result['reason']}\n")
