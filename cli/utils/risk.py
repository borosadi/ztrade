"""Risk validation and safety checks."""
from typing import Dict, Any, Tuple
from cli.utils.config import get_config
from cli.utils.logger import get_logger

logger = get_logger(__name__)


class RiskValidator:
    """Validates trades against risk management rules."""

    def __init__(self):
        self.config = get_config()

    def validate_trade(self, agent_id: str, decision: Dict[str, Any], current_price: float) -> Tuple[bool, str]:
        """
        Validate a trading decision against all risk rules.

        Args:
            agent_id: ID of the agent making the decision
            decision: Trading decision from AI agent
            current_price: Current market price

        Returns:
            Tuple of (is_valid, reason)
        """
        # Load agent configuration
        agent_config = self.config.load_agent_config(agent_id)
        if not agent_config:
            return False, f"Agent {agent_id} not found"

        agent_state = self.config.load_agent_state(agent_id)

        # RULE 1: Check if agent is active
        status = agent_config.get('agent', {}).get('status', 'paused')
        if status != 'active':
            return False, f"Agent status is {status}, not active"

        # RULE 2: Check daily trade limit
        max_daily_trades = agent_config.get('risk', {}).get('max_daily_trades', 10)
        trades_today = agent_state.get('trades_today', 0)
        if trades_today >= max_daily_trades:
            return False, f"Daily trade limit reached ({trades_today}/{max_daily_trades})"

        # RULE 3: Validate position size
        action = decision.get('action', '').lower()
        if action in ['buy', 'sell']:
            quantity = decision.get('quantity', 0)
            position_value = quantity * current_price
            max_position = agent_config.get('risk', {}).get('max_position_size', 5000)

            if position_value > max_position:
                return False, f"Position size ${position_value:.2f} exceeds max ${max_position:.2f}"

        # RULE 4: Check allocated capital
        allocated_capital = agent_config.get('performance', {}).get('allocated_capital', 0)
        if allocated_capital <= 0:
            return False, "No capital allocated to agent"

        # RULE 5: Validate stop loss
        if action == 'buy' and 'stop_loss' not in decision:
            return False, "Buy order must include stop_loss"

        if 'stop_loss' in decision:
            stop_loss = decision['stop_loss']
            min_stop_loss = agent_config.get('risk', {}).get('stop_loss', 0.02)

            if action == 'buy':
                stop_loss_pct = (current_price - stop_loss) / current_price
                if stop_loss_pct < min_stop_loss:
                    return False, f"Stop loss too tight: {stop_loss_pct*100:.1f}% < {min_stop_loss*100:.1f}%"

        # RULE 6: Check daily P&L limit
        pnl_today = agent_state.get('pnl_today', 0)
        max_daily_loss = agent_config.get('risk', {}).get('max_daily_loss', 1000)

        if pnl_today < -max_daily_loss:
            return False, f"Daily loss limit exceeded: ${pnl_today:.2f} < ${-max_daily_loss:.2f}"

        # RULE 7: Validate confidence threshold
        confidence = decision.get('confidence', 0)
        min_confidence = agent_config.get('risk', {}).get('min_confidence', 0.6)

        if confidence < min_confidence:
            return False, f"Confidence {confidence:.0%} below threshold {min_confidence:.0%}"

        # RULE 8: Validate decision structure
        required_fields = ['action', 'rationale']
        if action in ['buy', 'sell']:
            required_fields.extend(['quantity', 'confidence'])

        for field in required_fields:
            if field not in decision:
                return False, f"Missing required field: {field}"

        # RULE 9: Check concurrent positions
        positions = agent_state.get('positions', [])
        max_positions = agent_config.get('risk', {}).get('max_concurrent_positions', 3)

        if action == 'buy' and len(positions) >= max_positions:
            return False, f"Maximum concurrent positions reached ({len(positions)}/{max_positions})"

        # All checks passed
        return True, "All risk checks passed"

    def check_company_limits(self) -> Tuple[bool, str]:
        """
        Check company-wide risk limits.

        Returns:
            Tuple of (is_ok, message)
        """
        company_config = self.config.load_company_config()
        if not company_config:
            return False, "Company configuration not found"

        # Check total capital allocation
        max_capital = company_config.get('max_capital_allocation', 100000)
        agents = self.config.list_agents()

        total_allocated = 0
        for agent_id in agents:
            agent_config = self.config.load_agent_config(agent_id)
            capital = agent_config.get('performance', {}).get('allocated_capital', 0)
            total_allocated += capital

        max_deployment = company_config.get('max_capital_deployment_pct', 0.8)
        max_deployable = max_capital * max_deployment

        if total_allocated > max_deployable:
            return False, f"Capital deployment ${total_allocated:,.2f} exceeds limit ${max_deployable:,.2f}"

        return True, "Company limits OK"
