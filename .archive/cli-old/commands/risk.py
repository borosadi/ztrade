"""Risk management commands."""
import click
from cli.utils.config import get_config
from cli.utils.risk import RiskValidator
from cli.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def risk():
    """Risk management and control commands."""
    pass


@risk.command()
def status():
    """Check overall risk status across all agents."""
    config = get_config()
    validator = RiskValidator()

    click.echo(f"\n{'='*70}")
    click.echo("Risk Status")
    click.echo(f"{'='*70}\n")

    # Check company-wide limits
    company_ok, company_msg = validator.check_company_limits()

    if company_ok:
        click.secho(f"Company Limits: {company_msg}", fg='green')
    else:
        click.secho(f"Company Limits: {company_msg}", fg='red')

    click.echo()

    # Check each agent
    agents = config.list_agents()

    if not agents:
        click.echo("No agents configured.\n")
        return

    click.echo("Agent Risk Summary:\n")

    for agent_id in agents:
        agent_config = config.load_agent_config(agent_id)
        agent_state = config.load_agent_state(agent_id)

        asset = agent_config.get('agent', {}).get('asset', 'N/A')
        status = agent_config.get('agent', {}).get('status', 'unknown')

        # Risk metrics
        pnl = agent_state.get('pnl_today', 0)
        trades = agent_state.get('trades_today', 0)
        max_trades = agent_config.get('risk', {}).get('max_daily_trades', 10)
        max_loss = agent_config.get('risk', {}).get('max_daily_loss', 1000)

        # Status icon
        if status == 'active':
            status_icon = "Active"
            status_color = "green"
        else:
            status_icon = "Paused"
            status_color = "yellow"

        click.secho(f"{agent_id} ({asset}) - {status_icon}", fg=status_color)

        # Trade limit status
        trade_pct = (trades / max_trades * 100) if max_trades > 0 else 0
        if trade_pct >= 80:
            click.secho(f"  WARNING: Trades: {trades}/{max_trades} ({trade_pct:.0f}%)", fg='yellow')
        else:
            click.echo(f"  Trades: {trades}/{max_trades} ({trade_pct:.0f}%)")

        # P&L status
        loss_pct = (abs(pnl) / max_loss * 100) if max_loss > 0 and pnl < 0 else 0
        if pnl < 0 and loss_pct >= 70:
            click.secho(f"  WARNING: P&L Today: ${pnl:.2f} ({loss_pct:.0f}% of limit)", fg='red')
        else:
            pnl_color = 'green' if pnl >= 0 else 'red'
            click.secho(f"  P&L Today: ${pnl:+.2f}", fg=pnl_color)

        click.echo()


@risk.command()
@click.argument('agent_id')
@click.argument('parameter')
@click.argument('value', type=float)
def set_limit(agent_id, parameter, value):
    """Update risk parameter for an agent."""
    config = get_config()

    agent_config = config.load_agent_config(agent_id)
    if not agent_config:
        click.echo(f"Agent {agent_id} not found.", err=True)
        return

    # Valid risk parameters
    valid_params = [
        'max_position_size',
        'stop_loss',
        'max_daily_trades',
        'max_daily_loss',
        'min_confidence',
        'max_concurrent_positions'
    ]

    if parameter not in valid_params:
        click.echo(f"Invalid parameter: {parameter}", err=True)
        click.echo(f"Valid parameters: {', '.join(valid_params)}")
        return

    # Update configuration
    if 'risk' not in agent_config:
        agent_config['risk'] = {}

    old_value = agent_config['risk'].get(parameter, 'not set')
    agent_config['risk'][parameter] = value

    # Save updated config
    config.save_agent_config(agent_id, agent_config)

    click.echo(f"\nUpdated {agent_id} risk parameter:")
    click.echo(f"  {parameter}: {old_value} -> {value}\n")

    logger.info(f"Risk limit updated for {agent_id}: {parameter}={value}")


@risk.command()
def correlations():
    """Check asset correlations across agents."""
    config = get_config()

    click.echo(f"\n{'='*70}")
    click.echo("Asset Correlation Monitoring")
    click.echo(f"{'='*70}\n")

    agents = config.list_agents()

    if len(agents) < 2:
        click.echo("Need at least 2 agents to check correlations.\n")
        return

    # Get active agents with positions
    active_agents = []
    for agent_id in agents:
        agent_config = config.load_agent_config(agent_id)
        agent_state = config.load_agent_state(agent_id)

        status = agent_config.get('agent', {}).get('status', 'unknown')
        positions = agent_state.get('positions', [])

        if status == 'active' and positions:
            asset = agent_config.get('agent', {}).get('asset', 'N/A')
            active_agents.append((agent_id, asset))

    if not active_agents:
        click.echo("No active agents with positions.\n")
        return

    click.echo("Active Positions:\n")
    for agent_id, asset in active_agents:
        click.echo(f"  {agent_id}: {asset}")

    click.echo(f"\nTotal exposed assets: {len(active_agents)}")

    # Simple correlation warning
    if len(active_agents) >= 4:
        click.secho("\nWARNING: Multiple concurrent positions may increase correlation risk", fg='yellow')

    click.echo()


@risk.command()
@click.argument('scenario')
def simulate(scenario):
    """Run risk scenario simulations."""
    config = get_config()

    click.echo(f"\n{'='*70}")
    click.echo(f"Risk Scenario: {scenario.upper()}")
    click.echo(f"{'='*70}\n")

    agents = config.list_agents()

    if scenario == 'market_crash':
        click.echo("Simulating 10% market crash across all positions...\n")

        total_loss = 0

        for agent_id in agents:
            agent_state = config.load_agent_state(agent_id)
            positions = agent_state.get('positions', [])

            agent_loss = 0
            for pos in positions:
                qty = pos.get('quantity', 0)
                entry = pos.get('entry_price', 0)
                position_value = qty * entry
                loss = position_value * 0.10
                agent_loss += loss

            if agent_loss > 0:
                click.secho(f"{agent_id}: -${agent_loss:,.2f}", fg='red')
                total_loss += agent_loss

        click.echo(f"\nTotal simulated loss: -${total_loss:,.2f}")

    elif scenario == 'volatility_spike':
        click.echo("Simulating VIX > 30 (high volatility)...\n")
        click.echo("Recommended actions:")
        click.echo("  - Reduce position sizes")
        click.echo("  - Tighten stop losses")
        click.echo("  - Consider pausing aggressive agents")

    elif scenario == 'max_drawdown':
        click.echo("Simulating maximum allowed drawdown...\n")

        company_config = config.load_company_config()
        max_capital = company_config.get('max_capital_allocation', 100000)
        max_loss_pct = company_config.get('max_daily_loss_pct', 0.05)
        max_loss = max_capital * max_loss_pct

        click.echo(f"Company capital: ${max_capital:,.2f}")
        click.echo(f"Max daily loss ({max_loss_pct*100:.0f}%): ${max_loss:,.2f}\n")

        click.echo("At this loss level, circuit breakers would trigger:")
        click.echo("  - All trading halted")
        click.echo("  - Positions reviewed")
        click.echo("  - Manual intervention required")

    else:
        click.echo(f"Unknown scenario: {scenario}", err=True)
        click.echo("Available scenarios: market_crash, volatility_spike, max_drawdown")

    click.echo()


@risk.command()
@click.option('--days', default=7, help='Number of days to show')
def history(days):
    """View historical risk metrics."""
    config = get_config()

    click.echo(f"\n{'='*70}")
    click.echo(f"Risk History (Last {days} days)")
    click.echo(f"{'='*70}\n")

    # This is a placeholder - in a real system, you'd read from historical logs
    click.echo("Historical risk tracking not yet implemented.")
    click.echo("Future metrics:")
    click.echo("  - Daily P&L trends")
    click.echo("  - Trade volume patterns")
    click.echo("  - Risk limit violations")
    click.echo("  - Correlation changes")
    click.echo()
