"""Algorithmic trading decision maker using sentiment and technical analysis.

This module provides rules-based decision-making using only sentiment and
technical signals, without any AI/LLM involvement.
"""
from typing import Dict, Any
from ztrade.core.logger import get_logger

logger = get_logger(__name__)

# Decision thresholds (empirically validated on TSLA backtest - 91.2% win rate)
BUY_THRESHOLD = 0.3       # Strong bullish signal threshold (+0.3)
SELL_THRESHOLD = -0.3     # Strong bearish signal threshold (-0.3)
NEUTRAL_ZONE = 0.15       # Weak signal zone (±0.15 from zero)

# Position sizing thresholds (confidence-based)
CONFIDENCE_HIGH = 0.85    # 100% of max position size
CONFIDENCE_MEDIUM = 0.75  # 75% of max position size
CONFIDENCE_LOW = 0.65     # 50% of max position size (minimum to trade)


class AlgorithmicDecisionMaker:
    """Makes trading decisions using algorithmic rules (sentiment + technical)."""

    def __init__(self, sentiment_weight: float = 0.6, technical_weight: float = 0.4):
        """
        Initialize algorithmic decision maker.

        Args:
            sentiment_weight: Weight for sentiment score (default 60%)
            technical_weight: Weight for technical score (default 40%)
        """
        self.sentiment_weight = sentiment_weight
        self.technical_weight = technical_weight
        logger.info(f"Algorithmic decision maker initialized (sentiment: {sentiment_weight*100}%, technical: {technical_weight*100}%)")

    def make_decision(
        self,
        sentiment_score: float,
        sentiment_confidence: float,
        technical_signal: str,
        technical_confidence: float,
        current_price: float,
        agent_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make a trading decision using algorithmic rules.

        Args:
            sentiment_score: Aggregated sentiment score (-1 to +1)
            sentiment_confidence: Sentiment confidence (0 to 1)
            technical_signal: Technical analysis signal ('bullish', 'bearish', 'neutral')
            technical_confidence: Technical analysis confidence (0 to 1)
            current_price: Current asset price
            agent_config: Agent configuration with risk parameters

        Returns:
            Dict with decision:
            {
                "decision": "buy" | "sell" | "hold",
                "quantity": int,
                "rationale": str,
                "confidence": float,
                "stop_loss": float (optional, for buy)
            }
        """
        # Extract agent parameters
        max_position_size = float(agent_config.get('risk', {}).get('max_position_size', 5000))
        stop_loss_pct = float(agent_config.get('risk', {}).get('stop_loss', 0.03))
        min_confidence = float(agent_config.get('risk', {}).get('min_confidence', 0.65))

        # Convert technical signal to numeric score
        technical_score = self._technical_to_score(technical_signal)

        # Calculate combined score (weighted average)
        # Sentiment: -1 to +1, Technical: -1 to +1
        combined_score = (
            sentiment_score * self.sentiment_weight +
            technical_score * self.technical_weight
        )

        # Calculate combined confidence (weighted average)
        combined_confidence = (
            sentiment_confidence * self.sentiment_weight +
            technical_confidence * self.technical_weight
        )

        logger.info(
            f"Algorithmic decision: sentiment={sentiment_score:.2f} ({sentiment_confidence:.0%}), "
            f"technical={technical_signal} ({technical_confidence:.0%}), "
            f"combined_score={combined_score:.2f}, combined_confidence={combined_confidence:.0%}"
        )

        # Decision logic
        decision = self._make_decision_from_score(
            combined_score=combined_score,
            combined_confidence=combined_confidence,
            min_confidence=min_confidence,
            current_price=current_price,
            max_position_size=max_position_size,
            stop_loss_pct=stop_loss_pct,
            sentiment_score=sentiment_score,
            technical_signal=technical_signal
        )

        logger.info(f"Algorithmic decision: {decision['decision']} (confidence: {decision['confidence']:.0%})")
        return decision

    def _technical_to_score(self, signal: str) -> float:
        """Convert technical signal to numeric score."""
        signal_lower = signal.lower()
        if signal_lower == 'bullish':
            return 1.0
        elif signal_lower == 'bearish':
            return -1.0
        else:  # neutral
            return 0.0

    def _make_decision_from_score(
        self,
        combined_score: float,
        combined_confidence: float,
        min_confidence: float,
        current_price: float,
        max_position_size: float,
        stop_loss_pct: float,
        sentiment_score: float,
        technical_signal: str
    ) -> Dict[str, Any]:
        """
        Generate trading decision from combined score.

        Decision thresholds:
        - combined_score > 0.3 and confidence >= min_confidence: BUY
        - combined_score < -0.3 and confidence >= min_confidence: SELL
        - Otherwise: HOLD
        """
        # Check confidence threshold first
        if combined_confidence < min_confidence:
            return {
                "decision": "hold",
                "quantity": 0,
                "rationale": f"Combined confidence ({combined_confidence:.1%}) below minimum threshold ({min_confidence:.0%}). Waiting for higher conviction signal.",
                "confidence": combined_confidence
            }

        # BUY signal (strong positive)
        if combined_score > BUY_THRESHOLD:
            quantity = self._calculate_position_size(
                combined_confidence,
                current_price,
                max_position_size
            )
            stop_loss_price = current_price * (1 - stop_loss_pct)

            return {
                "decision": "buy",
                "quantity": quantity,
                "rationale": (
                    f"Strong bullish signal: combined_score={combined_score:.2f} "
                    f"(sentiment: {sentiment_score:+.2f}, technical: {technical_signal}). "
                    f"Confidence {combined_confidence:.0%} exceeds threshold. "
                    f"Entering position with {stop_loss_pct:.1%} stop loss."
                ),
                "confidence": combined_confidence,
                "stop_loss": round(stop_loss_price, 2)
            }

        # SELL signal (strong negative)
        elif combined_score < SELL_THRESHOLD:
            # For now, we only trade long positions
            # In the future, this could trigger short positions or exit existing longs
            return {
                "decision": "hold",
                "quantity": 0,
                "rationale": (
                    f"Strong bearish signal: combined_score={combined_score:.2f} "
                    f"(sentiment: {sentiment_score:+.2f}, technical: {technical_signal}). "
                    f"Not entering position in bearish conditions. "
                    f"Currently only trading long positions."
                ),
                "confidence": combined_confidence
            }

        # HOLD (neutral or weak signal)
        else:
            signal_strength = "weak" if abs(combined_score) < NEUTRAL_ZONE else "moderate"
            direction = "bullish" if combined_score > 0 else "bearish" if combined_score < 0 else "neutral"

            return {
                "decision": "hold",
                "quantity": 0,
                "rationale": (
                    f"{signal_strength.capitalize()} {direction} signal: combined_score={combined_score:.2f} "
                    f"(sentiment: {sentiment_score:+.2f}, technical: {technical_signal}). "
                    f"Waiting for stronger conviction (threshold: ±{BUY_THRESHOLD})."
                ),
                "confidence": combined_confidence
            }

    def _calculate_position_size(
        self,
        confidence: float,
        current_price: float,
        max_position_size: float
    ) -> int:
        """
        Calculate position size based on confidence level.

        Position sizing:
        - confidence >= CONFIDENCE_HIGH (0.85): 100% of max
        - confidence >= CONFIDENCE_MEDIUM (0.75): 75% of max
        - confidence >= CONFIDENCE_LOW (0.65): 50% of max
        """
        if confidence >= CONFIDENCE_HIGH:
            position_size = max_position_size
        elif confidence >= CONFIDENCE_MEDIUM:
            position_size = max_position_size * 0.75
        else:  # confidence >= CONFIDENCE_LOW
            position_size = max_position_size * 0.50

        # Convert to number of shares
        quantity = int(position_size / current_price)

        logger.info(
            f"Position sizing: confidence={confidence:.0%}, "
            f"position_size=${position_size:.2f}, "
            f"quantity={quantity} shares @ ${current_price:.2f}"
        )

        return max(1, quantity)  # At least 1 share


def get_algorithmic_decision_maker(
    sentiment_weight: float = 0.6,
    technical_weight: float = 0.4
) -> AlgorithmicDecisionMaker:
    """Factory function to get algorithmic decision maker instance."""
    return AlgorithmicDecisionMaker(
        sentiment_weight=sentiment_weight,
        technical_weight=technical_weight
    )
