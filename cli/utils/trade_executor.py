"""Trade execution and state management."""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from cli.utils.config import get_config
from cli.utils.broker import get_broker
from cli.utils.logger import get_logger

logger = get_logger(__name__)


class TradeExecutor:
    """Handles trade execution, logging, and state updates."""

    def __init__(self):
        self.config = get_config()
        self.broker = get_broker()

    def execute_trade(self, agent_id: str, decision: Dict[str, Any], current_price: float, dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute a validated trade decision.

        Args:
            agent_id: ID of the agent making the trade
            decision: Validated trading decision
            current_price: Current market price
            dry_run: If True, simulate without actually executing

        Returns:
            Trade result dictionary
        """
        action = decision.get('action', '').lower()
        agent_config = self.config.load_agent_config(agent_id)
        asset = agent_config.get('agent', {}).get('asset', 'UNKNOWN')

        result = {
            'agent_id': agent_id,
            'asset': asset,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'success': False,
        }

        # Handle different actions
        if action == 'hold':
            result['success'] = True
            result['message'] = 'Holding position'
            self._log_decision(agent_id, decision, result)
            return result

        elif action in ['buy', 'sell']:
            quantity = decision.get('quantity', 0)
            stop_loss = decision.get('stop_loss')

            if dry_run:
                result['success'] = True
                result['message'] = f'DRY RUN: Would {action} {quantity} shares of {asset} at ${current_price:.2f}'
                if stop_loss:
                    result['message'] += f' with stop loss at ${stop_loss:.2f}'
                self._log_decision(agent_id, decision, result)
                return result

            # Execute actual trade
            try:
                order_result = self.broker.submit_order(
                    symbol=asset,
                    qty=quantity,
                    side=action,
                    order_type='market',
                    time_in_force='day',
                    stop_loss=stop_loss
                )

                result['success'] = True
                result['order_id'] = order_result.get('id')
                result['filled_price'] = order_result.get('filled_avg_price', current_price)
                result['message'] = f'{action.upper()} order submitted: {quantity} shares of {asset}'

                # Update agent state
                self._update_agent_state(agent_id, decision, order_result)

                # Log trade
                self._log_trade(agent_id, decision, order_result)

            except Exception as e:
                result['success'] = False
                result['error'] = str(e)
                result['message'] = f'Trade execution failed: {e}'
                logger.error(f"Trade execution failed for {agent_id}: {e}")

            self._log_decision(agent_id, decision, result)
            return result

        else:
            result['message'] = f'Unknown action: {action}'
            self._log_decision(agent_id, decision, result)
            return result

    def _update_agent_state(self, agent_id: str, decision: Dict[str, Any], order_result: Dict[str, Any]):
        """Update agent state after trade execution."""
        agent_state = self.config.load_agent_state(agent_id)

        # Increment trade count
        agent_state['trades_today'] = agent_state.get('trades_today', 0) + 1

        # Update positions
        action = decision.get('action', '').lower()
        quantity = decision.get('quantity', 0)
        filled_price = order_result.get('filled_avg_price', 0)

        positions = agent_state.get('positions', [])

        if action == 'buy':
            positions.append({
                'quantity': quantity,
                'entry_price': filled_price,
                'stop_loss': decision.get('stop_loss'),
                'timestamp': datetime.now().isoformat(),
                'order_id': order_result.get('id')
            })
        elif action == 'sell':
            # For now, just remove the oldest position
            # In a real system, you'd match specific positions
            if positions:
                positions.pop(0)

        agent_state['positions'] = positions
        agent_state['last_trade_time'] = datetime.now().isoformat()

        # Save updated state
        self.config.save_agent_state(agent_id, agent_state)

    def _log_trade(self, agent_id: str, decision: Dict[str, Any], order_result: Dict[str, Any]):
        """Log trade execution to trades log."""
        log_dir = Path('logs/trades')
        log_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime('%Y-%m-%d')
        log_file = log_dir / f'{today}.jsonl'

        trade_log = {
            'timestamp': datetime.now().isoformat(),
            'agent_id': agent_id,
            'decision': decision,
            'order_result': order_result,
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(trade_log) + '\n')

        logger.info(f"Trade logged for {agent_id}: {decision.get('action')} {decision.get('quantity', 0)} shares")

    def _log_decision(self, agent_id: str, decision: Dict[str, Any], result: Dict[str, Any]):
        """Log agent decision to decisions log."""
        log_dir = Path('logs/agent_decisions')
        log_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime('%Y-%m-%d')
        log_file = log_dir / f'{agent_id}_{today}.jsonl'

        decision_log = {
            'timestamp': datetime.now().isoformat(),
            'agent_id': agent_id,
            'decision': decision,
            'result': result,
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(decision_log) + '\n')

        logger.info(f"Decision logged for {agent_id}: {decision.get('action')}")
