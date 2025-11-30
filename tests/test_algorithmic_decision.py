"""
Tests for algorithmic decision-making module.

This tests the critical path of trading decisions based on sentiment
and technical analysis.
"""
import pytest
from ztrade.decision.algorithmic import (
    AlgorithmicDecisionMaker,
    BUY_THRESHOLD,
    SELL_THRESHOLD,
    NEUTRAL_ZONE,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW
)


@pytest.fixture
def decision_maker():
    """Create a decision maker with default weights."""
    return AlgorithmicDecisionMaker(sentiment_weight=0.6, technical_weight=0.4)


@pytest.fixture
def agent_config():
    """Mock agent configuration."""
    return {
        'risk': {
            'max_position_size': 5000,
            'stop_loss': 0.03,
            'min_confidence': 0.65
        }
    }


class TestBuySignals:
    """Test buy signal generation."""

    def test_strong_bullish_signal_triggers_buy(self, decision_maker, agent_config):
        """Strong positive sentiment + bullish technical should trigger buy."""
        decision = decision_maker.make_decision(
            sentiment_score=0.7,  # Strong positive
            sentiment_confidence=0.8,
            technical_signal='bullish',
            technical_confidence=0.7,
            current_price=100.0,
            agent_config=agent_config
        )

        assert decision['decision'] == 'buy'
        assert decision['quantity'] > 0
        assert 'stop_loss' in decision
        assert decision['stop_loss'] < 100.0  # Stop loss below entry
        assert decision['confidence'] >= agent_config['risk']['min_confidence']

    def test_buy_signal_includes_stop_loss(self, decision_maker, agent_config):
        """Buy signals must include stop loss."""
        decision = decision_maker.make_decision(
            sentiment_score=0.6,
            sentiment_confidence=0.75,
            technical_signal='bullish',
            technical_confidence=0.7,
            current_price=100.0,
            agent_config=agent_config
        )

        assert decision['decision'] == 'buy'
        expected_stop_loss = 100.0 * (1 - 0.03)  # 3% stop loss
        assert abs(decision['stop_loss'] - expected_stop_loss) < 0.01

    def test_high_confidence_uses_full_position_size(self, decision_maker, agent_config):
        """Confidence >= 0.85 should use 100% of max position."""
        decision = decision_maker.make_decision(
            sentiment_score=0.8,
            sentiment_confidence=0.9,  # High confidence
            technical_signal='bullish',
            technical_confidence=0.85,
            current_price=100.0,
            agent_config=agent_config
        )

        assert decision['decision'] == 'buy'
        # 100% of 5000 = 50 shares at $100
        assert decision['quantity'] == 50

    def test_medium_confidence_uses_75_percent_position(self, decision_maker, agent_config):
        """Confidence between 0.75-0.85 should use 75% of max position."""
        decision = decision_maker.make_decision(
            sentiment_score=0.6,
            sentiment_confidence=0.8,  # Medium confidence
            technical_signal='bullish',
            technical_confidence=0.7,
            current_price=100.0,
            agent_config=agent_config
        )

        assert decision['decision'] == 'buy'
        # 75% of 5000 = 37 shares at $100
        assert decision['quantity'] == 37

    def test_low_confidence_uses_50_percent_position(self, decision_maker, agent_config):
        """Confidence between 0.65-0.75 should use 50% of max position."""
        decision = decision_maker.make_decision(
            sentiment_score=0.5,
            sentiment_confidence=0.7,  # Low confidence (but above min)
            technical_signal='bullish',
            technical_confidence=0.6,
            current_price=100.0,
            agent_config=agent_config
        )

        assert decision['decision'] == 'buy'
        # 50% of 5000 = 25 shares at $100
        assert decision['quantity'] == 25


class TestSellSignals:
    """Test sell signal handling."""

    def test_strong_bearish_signal_returns_hold(self, decision_maker, agent_config):
        """Strong bearish signals should return HOLD (no short selling)."""
        decision = decision_maker.make_decision(
            sentiment_score=-0.7,  # Strong negative
            sentiment_confidence=0.8,
            technical_signal='bearish',
            technical_confidence=0.7,
            current_price=100.0,
            agent_config=agent_config
        )

        # Currently only trading long positions
        assert decision['decision'] == 'hold'
        assert decision['quantity'] == 0
        assert 'bearish' in decision['rationale'].lower()


class TestHoldSignals:
    """Test hold signal generation."""

    def test_low_confidence_returns_hold(self, decision_maker, agent_config):
        """Confidence below minimum threshold should return HOLD."""
        decision = decision_maker.make_decision(
            sentiment_score=0.5,
            sentiment_confidence=0.5,  # Below min_confidence (0.65)
            technical_signal='bullish',
            technical_confidence=0.6,
            current_price=100.0,
            agent_config=agent_config
        )

        assert decision['decision'] == 'hold'
        assert decision['quantity'] == 0
        assert 'below minimum threshold' in decision['rationale'].lower()

    def test_weak_signal_returns_hold(self, decision_maker, agent_config):
        """Weak signals (abs(score) < 0.3) should return HOLD."""
        decision = decision_maker.make_decision(
            sentiment_score=0.2,  # Weak positive
            sentiment_confidence=0.7,
            technical_signal='neutral',
            technical_confidence=0.6,
            current_price=100.0,
            agent_config=agent_config
        )

        assert decision['decision'] == 'hold'
        assert decision['quantity'] == 0

    def test_neutral_signal_returns_hold(self, decision_maker, agent_config):
        """Neutral signals should return HOLD."""
        decision = decision_maker.make_decision(
            sentiment_score=0.0,
            sentiment_confidence=0.7,
            technical_signal='neutral',
            technical_confidence=0.6,
            current_price=100.0,
            agent_config=agent_config
        )

        assert decision['decision'] == 'hold'
        assert decision['quantity'] == 0


class TestScoreCombination:
    """Test sentiment + technical score combination."""

    def test_sentiment_weight_dominates(self, decision_maker, agent_config):
        """Sentiment (60%) should have more weight than technical (40%)."""
        # Strong positive sentiment + neutral technical = buy
        decision1 = decision_maker.make_decision(
            sentiment_score=0.8,  # Strong positive
            sentiment_confidence=0.8,
            technical_signal='neutral',  # Neutral (score=0)
            technical_confidence=0.6,
            current_price=100.0,
            agent_config=agent_config
        )

        # Neutral sentiment + strong bullish technical = weaker signal
        decision2 = decision_maker.make_decision(
            sentiment_score=0.0,  # Neutral
            sentiment_confidence=0.7,
            technical_signal='bullish',  # Strong positive (score=1)
            technical_confidence=0.8,
            current_price=100.0,
            agent_config=agent_config
        )

        # First should have higher confidence (sentiment dominates)
        assert decision1['confidence'] > decision2['confidence']

    def test_conflicting_signals_reduce_confidence(self, decision_maker, agent_config):
        """Conflicting signals (positive + negative) should reduce overall confidence."""
        # Aligned signals (both bullish)
        aligned = decision_maker.make_decision(
            sentiment_score=0.6,
            sentiment_confidence=0.8,
            technical_signal='bullish',
            technical_confidence=0.7,
            current_price=100.0,
            agent_config=agent_config
        )

        # Conflicting signals (bullish sentiment + bearish technical)
        conflicting = decision_maker.make_decision(
            sentiment_score=0.6,
            sentiment_confidence=0.8,
            technical_signal='bearish',
            technical_confidence=0.7,
            current_price=100.0,
            agent_config=agent_config
        )

        # Aligned should have higher confidence
        assert aligned['confidence'] > conflicting['confidence']


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_price_raises_error(self, decision_maker, agent_config):
        """Zero or negative price should cause issues."""
        # This should either raise an error or return a sensible default
        # Currently it would cause division by zero in position sizing
        with pytest.raises((ZeroDivisionError, ValueError)):
            decision_maker.make_decision(
                sentiment_score=0.5,
                sentiment_confidence=0.7,
                technical_signal='bullish',
                technical_confidence=0.6,
                current_price=0.0,  # Invalid price
                agent_config=agent_config
            )

    def test_minimum_quantity_is_one_share(self, decision_maker, agent_config):
        """Quantity should never be less than 1 share."""
        decision = decision_maker.make_decision(
            sentiment_score=0.5,
            sentiment_confidence=0.7,
            technical_signal='bullish',
            technical_confidence=0.6,
            current_price=10000.0,  # Very high price (would calculate <1 share)
            agent_config=agent_config
        )

        if decision['decision'] == 'buy':
            assert decision['quantity'] >= 1

    def test_handles_missing_risk_config(self, decision_maker):
        """Should use defaults when risk config is missing."""
        minimal_config = {}

        decision = decision_maker.make_decision(
            sentiment_score=0.6,
            sentiment_confidence=0.8,
            technical_signal='bullish',
            technical_confidence=0.7,
            current_price=100.0,
            agent_config=minimal_config
        )

        # Should not crash, should use defaults
        assert decision['decision'] in ['buy', 'sell', 'hold']


class TestThresholdConstants:
    """Test that threshold constants are sensible."""

    def test_buy_threshold_is_positive(self):
        """Buy threshold should be positive."""
        assert BUY_THRESHOLD > 0

    def test_sell_threshold_is_negative(self):
        """Sell threshold should be negative."""
        assert SELL_THRESHOLD < 0

    def test_thresholds_are_symmetric(self):
        """Buy and sell thresholds should be symmetric."""
        assert abs(BUY_THRESHOLD) == abs(SELL_THRESHOLD)

    def test_neutral_zone_is_smaller_than_threshold(self):
        """Neutral zone should be smaller than decision threshold."""
        assert NEUTRAL_ZONE < BUY_THRESHOLD

    def test_confidence_thresholds_are_ordered(self):
        """Confidence thresholds should be in ascending order."""
        assert CONFIDENCE_LOW < CONFIDENCE_MEDIUM < CONFIDENCE_HIGH


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
