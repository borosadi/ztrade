"""Monitoring and observability commands."""
import click
import json
from datetime import datetime
from pathlib import Path
from cli.utils.config import get_config
from cli.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def monitor():
    """Monitoring and observability commands."""
    pass


@monitor.command()
@click.option('--limit', default=10, help='Number of recent trades to show')
@click.option('--agent', help='Filter by agent ID')
def trades(limit, agent):
    """View recent trade history."""
    log_dir = Path('logs/trades')

    if not log_dir.exists():
        click.echo("\nNo trade logs found.\n")
        return

    # Get all trade log files
    log_files = sorted(log_dir.glob('*.jsonl'), reverse=True)

    if not log_files:
        click.echo("\nNo trades logged yet.\n")
        return

    click.echo(f"\n{'='*70}")
    click.echo("Recent Trades")
    click.echo(f"{'='*70}\n")

    trades_shown = 0

    # Read most recent log files
    for log_file in log_files:
        if trades_shown >= limit:
            break

        with open(log_file, 'r') as f:
            lines = f.readlines()

        # Read from bottom (most recent first)
        for line in reversed(lines):
            if trades_shown >= limit:
                break

            try:
                trade = json.loads(line)
                agent_id = trade.get('agent_id', 'unknown')

                # Filter by agent if specified
                if agent and agent_id != agent:
                    continue

                decision = trade.get('decision', {})
                order_result = trade.get('order_result', {})

                timestamp = trade.get('timestamp', 'unknown')
                action = decision.get('action', 'unknown').upper()
                quantity = decision.get('quantity', 0)
                price = order_result.get('filled_avg_price', 'N/A')

                click.echo(f"{timestamp} | {agent_id}")
                click.echo(f"  {action} {quantity} shares @ ${price}")
                click.echo(f"  Rationale: {decision.get('rationale', 'N/A')}")
                click.echo(f"  Confidence: {decision.get('confidence', 0)*100:.0f}%")
                click.echo()

                trades_shown += 1

            except json.JSONDecodeError:
                continue

    if trades_shown == 0:
        if agent:
            click.echo(f"No trades found for agent {agent}.\n")
        else:
            click.echo("No trades found.\n")


@monitor.command()
@click.argument('agent_id')
@click.option('--limit', default=10, help='Number of recent decisions to show')
def decisions(agent_id, limit):
    """View agent decision history."""
    log_dir = Path('logs/agent_decisions')

    if not log_dir.exists():
        click.echo("\nNo decision logs found.\n")
        return

    # Find decision logs for this agent
    log_files = sorted(log_dir.glob(f'{agent_id}_*.jsonl'), reverse=True)

    if not log_files:
        click.echo(f"\nNo decisions logged for {agent_id}.\n")
        return

    click.echo(f"\n{'='*70}")
    click.echo(f"Decision History: {agent_id}")
    click.echo(f"{'='*70}\n")

    decisions_shown = 0

    for log_file in log_files:
        if decisions_shown >= limit:
            break

        with open(log_file, 'r') as f:
            lines = f.readlines()

        for line in reversed(lines):
            if decisions_shown >= limit:
                break

            try:
                entry = json.loads(line)
                decision = entry.get('decision', {})
                result = entry.get('result', {})

                timestamp = entry.get('timestamp', 'unknown')
                action = decision.get('action', 'unknown').upper()

                click.echo(f"{timestamp}")
                click.echo(f"  Action: {action}")
                click.echo(f"  Rationale: {decision.get('rationale', 'N/A')}")
                click.echo(f"  Confidence: {decision.get('confidence', 0)*100:.0f}%")

                if result.get('success'):
                    click.secho(f"  Success: {result.get('message', 'Success')}", fg='green')
                else:
                    click.secho(f"  Failed: {result.get('message', 'Failed')}", fg='red')

                click.echo()
                decisions_shown += 1

            except json.JSONDecodeError:
                continue

    if decisions_shown == 0:
        click.echo(f"No decisions found for {agent_id}.\n")


@monitor.command()
def alerts():
    """View active alerts and warnings."""
    config = get_config()

    click.echo(f"\n{'='*70}")
    click.echo("Active Alerts")
    click.echo(f"{'='*70}\n")

    alerts_found = False

    # Check each agent for alert conditions
    agents = config.list_agents()

    for agent_id in agents:
        agent_config = config.load_agent_config(agent_id)
        agent_state = config.load_agent_state(agent_id)

        # Check for alert conditions
        pnl = agent_state.get('pnl_today', 0)
        trades = agent_state.get('trades_today', 0)
        max_trades = agent_config.get('risk', {}).get('max_daily_trades', 10)
        max_loss = agent_config.get('risk', {}).get('max_daily_loss', 1000)

        # Alert if approaching daily trade limit
        if trades >= max_trades * 0.8:
            click.secho(f"WARNING: {agent_id}: Approaching trade limit ({trades}/{max_trades})", fg='yellow')
            alerts_found = True

        # Alert if daily loss is significant
        if pnl < -max_loss * 0.7:
            click.secho(f"WARNING: {agent_id}: Significant daily loss ${pnl:.2f}", fg='red')
            alerts_found = True

        # Alert if agent is paused
        status = agent_config.get('agent', {}).get('status', 'unknown')
        if status == 'paused':
            click.echo(f"INFO: {agent_id}: Agent is paused")
            alerts_found = True

    if not alerts_found:
        click.echo("No active alerts.\n")
    else:
        click.echo()


@monitor.command()
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.option('--level', default='INFO', help='Log level filter')
def logs(follow, level):
    """View system logs."""
    log_dir = Path('logs/system')

    if not log_dir.exists():
        click.echo("\nNo system logs found.\n")
        return

    # Get most recent log file
    log_files = sorted(log_dir.glob('*.log'), reverse=True)

    if not log_files:
        click.echo("\nNo log files found.\n")
        return

    log_file = log_files[0]

    if follow:
        click.echo(f"Following {log_file}... (Ctrl+C to stop)\n")
        # Simple tail -f implementation
        import time
        with open(log_file, 'r') as f:
            # Go to end of file
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    if level.upper() in line:
                        click.echo(line.rstrip())
                else:
                    time.sleep(0.1)
    else:
        # Show last 50 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()

        click.echo(f"\nLast 50 log entries from {log_file}:\n")
        for line in lines[-50:]:
            if level.upper() in line:
                click.echo(line.rstrip())


@monitor.command()
@click.argument('agent_id')
def performance(agent_id):
    """View detailed performance metrics for an agent."""
    config = get_config()

    agent_config = config.load_agent_config(agent_id)
    if not agent_config:
        click.echo(f"Agent {agent_id} not found.", err=True)
        return

    agent_state = config.load_agent_state(agent_id)

    click.echo(f"\n{'='*70}")
    click.echo(f"Performance Metrics: {agent_id}")
    click.echo(f"{'='*70}\n")

    # Basic info
    asset = agent_config.get('agent', {}).get('asset', 'N/A')
    strategy = agent_config.get('agent', {}).get('strategy', {}).get('type', 'N/A')
    status = agent_config.get('agent', {}).get('status', 'unknown')

    click.echo(f"Asset: {asset}")
    click.echo(f"Strategy: {strategy}")
    click.echo(f"Status: {status}\n")

    # Performance data
    perf = agent_config.get('performance', {})
    allocated = perf.get('allocated_capital', 0)
    total_pnl = perf.get('total_pnl', 0)
    win_rate = perf.get('win_rate', 0)
    total_trades = perf.get('total_trades', 0)

    click.echo("Lifetime Performance:")
    click.echo(f"  Allocated Capital: ${allocated:,.2f}")
    click.echo(f"  Total P&L: ${total_pnl:+,.2f}")
    click.echo(f"  Total Trades: {total_trades}")
    click.echo(f"  Win Rate: {win_rate*100:.1f}%\n")

    # Today's performance
    pnl_today = agent_state.get('pnl_today', 0)
    trades_today = agent_state.get('trades_today', 0)

    click.echo("Today's Performance:")
    click.echo(f"  P&L: ${pnl_today:+,.2f}")
    click.echo(f"  Trades: {trades_today}\n")

    # Current positions
    positions = agent_state.get('positions', [])
    if positions:
        click.echo(f"Open Positions ({len(positions)}):")
        for i, pos in enumerate(positions, 1):
            qty = pos.get('quantity', 0)
            entry = pos.get('entry_price', 0)
            stop = pos.get('stop_loss', 'N/A')
            click.echo(f"  {i}. {qty} shares @ ${entry:.2f} (stop: ${stop})")
        click.echo()
    else:
        click.echo("No open positions.\n")
