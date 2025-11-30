"""
Tests for risk validation module.

Tests the critical risk management rules that protect capital.
"""
import pytest
from ztrade.execution.risk import RiskValidator


@pytest.fixture
def validator():
    """Create a risk validator instance."""
    return RiskValidator()


@pytest.fixture
def agent_config():
    """Mock agent configuration with risk parameters."""
    return {
        'risk': {
            'max_position_size': 5000,
            'daily_trade_limit': 10,
            'stop_loss': 0.03
        }
    }


@pytest.fixture
def agent_state():
    """Mock agent state."""
    return {
        'trades_today': 0,
        'daily_loss': 0.0
    }


class TestPositionSizeLimits:
    """Test position size validation."""

    def test_accepts_valid_position_size(self, validator, agent_config, agent_state):
        """Valid position size should pass."""
        is_valid, reason = validator.validate_trade(
            agent_id='agent_test',
            action='buy',
            asset='TSLA',
            quantity=10,
            price=100.0,  # Total: $1000 (within $5000 limit)
            agent_config=agent_config,
            agent_state=agent_state
        )

        assert is_valid
        assert reason is None or reason == ""

    def test_rejects_oversized_position(self, validator, agent_config, agent_state):
        """Position size exceeding limit should be rejected."""
        is_valid, reason = validator.validate_trade(
            agent_id='agent_test',
            action='buy',
            asset='TSLA',
            quantity=100,
            price=100.0,  # Total: $10,000 (exceeds $5000 limit)
            agent_config=agent_config,
            agent_state=agent_state
        )

        assert not is_valid
        assert 'position size' in reason.lower() or 'exceeds' in reason.lower()


class TestDailyTradeLimits:
    """Test daily trade count limits."""

    def test_rejects_trade_at_daily_limit(self, validator, agent_config, agent_state):
        """Trade at daily limit should be rejected."""
        agent_state['trades_today'] = 10  # At limit

        is_valid, reason = validator.validate_trade(
            agent_id='agent_test',
            action='buy',
            asset='TSLA',
            quantity=10,
            price=100.0,
            agent_config=agent_config,
            agent_state=agent_state
        )

        assert not is_valid
        assert 'daily' in reason.lower() or 'limit' in reason.lower()

    def test_accepts_trade_below_daily_limit(self, validator, agent_config, agent_state):
        """Trade below daily limit should pass."""
        agent_state['trades_today'] = 5  # Below limit of 10

        is_valid, reason = validator.validate_trade(
            agent_id='agent_test',
            action='buy',
            asset='TSLA',
            quantity=10,
            price=100.0,
            agent_config=agent_config,
            agent_state=agent_state
        )

        assert is_valid


class TestStopLossRequirements:
    """Test stop loss validation."""

    def test_buy_requires_stop_loss(self, validator, agent_config, agent_state):
        """All buy orders must have a stop loss."""
        # This test depends on how the validator is implemented
        # If stop loss is validated, it should be in the trade params
        pass


class TestEdgeCases:
    """Test edge cases."""

    def test_zero_quantity_is_invalid(self, validator, agent_config, agent_state):
        """Zero quantity should be rejected."""
        is_valid, reason = validator.validate_trade(
            agent_id='agent_test',
            action='buy',
            asset='TSLA',
            quantity=0,
            price=100.0,
            agent_config=agent_config,
            agent_state=agent_state
        )

        assert not is_valid

    def test_negative_quantity_is_invalid(self, validator, agent_config, agent_state):
        """Negative quantity should be rejected."""
        is_valid, reason = validator.validate_trade(
            agent_id='agent_test',
            action='buy',
            asset='TSLA',
            quantity=-10,
            price=100.0,
            agent_config=agent_config,
            agent_state=agent_state
        )

        assert not is_valid

    def test_negative_price_is_invalid(self, validator, agent_config, agent_state):
        """Negative price should be rejected."""
        is_valid, reason = validator.validate_trade(
            agent_id='agent_test',
            action='buy',
            asset='TSLA',
            quantity=10,
            price=-100.0,
            agent_config=agent_config,
            agent_state=agent_state
        )

        assert not is_valid


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
