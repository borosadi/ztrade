"""Company-level management commands."""
import click
from cli.utils.config import get_config
from cli.utils.broker import get_broker
from cli.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def company():
    """Company-level operations and monitoring."""
    pass


@company.command()
def dashboard():
    """View company dashboard with overall status."""
    config = get_config()

    click.echo(f"\n{'='*70}")
    click.echo(" "*25 + "ZTRADE DASHBOARD")
    click.echo(f"{'='*70}\n")

    # Get company config
    company_config = config.load_company_config()
    max_capital = company_config.get('max_capital_allocation', 100000)

    # Get all agents
    agents = config.list_agents()

    click.echo(f"📊 Company Overview")
    click.echo(f"  Total Capital: ${max_capital:,.2f}")
    click.echo(f"  Active Agents: {len(agents)}\n")

    # Try to get broker account info
    try:
        broker = get_broker()
        account = broker.get_account_info()

        click.echo(f"💰 Broker Account (Alpaca)")
        click.echo(f"  Equity: ${account['equity']:,.2f}")
        click.echo(f"  Cash: ${account['cash']:,.2f}")
        click.echo(f"  Buying Power: ${account['buying_power']:,.2f}")

        if account['trading_blocked']:
            click.echo(f"  ⚠️  Trading is BLOCKED", err=True)
        click.echo()

        # Get positions
        positions = broker.get_positions()
        if positions:
            click.echo(f"📈 Open Positions ({len(positions)})")
            total_pl = sum(p['unrealized_pl'] for p in positions)

            for pos in positions:
                pl_color = "green" if pos['unrealized_pl'] >= 0 else "red"
                click.echo(f"  {pos['symbol']}: {pos['qty']} shares @ ${pos['avg_entry_price']:.2f}")
                click.secho(f"    P&L: ${pos['unrealized_pl']:,.2f} ({pos['unrealized_plpc']*100:.2f}%)",
                           fg=pl_color)

            click.echo(f"\n  Total Unrealized P&L: ", nl=False)
            click.secho(f"${total_pl:,.2f}", fg="green" if total_pl >= 0 else "red")
            click.echo()
        else:
            click.echo(f"📈 No open positions\n")

    except Exception as e:
        click.echo(f"⚠️  Could not connect to broker: {e}\n", err=True)

    # Agent summary
    if agents:
        click.echo(f"🤖 Agent Summary")

        total_capital_allocated = 0
        total_pnl_today = 0
        total_trades_today = 0
        active_count = 0

        for agent_id in agents:
            agent_config = config.load_agent_config(agent_id)
            agent_state = config.load_agent_state(agent_id)

            capital = agent_config.get('performance', {}).get('allocated_capital', 0)
            pnl = agent_state.get('pnl_today', 0)
            trades = agent_state.get('trades_today', 0)
            status = agent_config.get('agent', {}).get('status', 'unknown')

            total_capital_allocated += capital
            total_pnl_today += pnl
            total_trades_today += trades

            if status == 'active':
                active_count += 1

            status_icon = "✓" if status == 'active' else "⏸"
            asset = agent_config.get('agent', {}).get('asset', 'N/A')

            click.echo(f"  {status_icon} {agent_id} ({asset}): ${pnl:+.2f} today, {trades} trades")

        click.echo(f"\n  Active: {active_count}/{len(agents)}")
        click.echo(f"  Capital Allocated: ${total_capital_allocated:,.2f}")
        click.echo(f"  Total P&L Today: ", nl=False)
        click.secho(f"${total_pnl_today:+,.2f}",
                   fg="green" if total_pnl_today >= 0 else "red")
        click.echo(f"  Total Trades Today: {total_trades_today}")
        click.echo()
    else:
        click.echo(f"🤖 No agents configured yet.\n")
        click.echo(f"  Create your first agent with: ztrade agent create <agent_id>\n")

    click.echo(f"{'='*70}\n")


@company.command()
def positions():
    """View all positions across agents."""
    try:
        broker = get_broker()
        positions = broker.get_positions()

        if not positions:
            click.echo("\nNo open positions.\n")
            return

        click.echo(f"\n{'='*70}")
        click.echo("All Positions")
        click.echo(f"{'='*70}\n")

        total_value = 0
        total_pl = 0

        for pos in positions:
            total_value += pos['market_value']
            total_pl += pos['unrealized_pl']

            click.echo(f"{pos['symbol']}")
            click.echo(f"  Side: {pos['side'].upper()}")
            click.echo(f"  Quantity: {pos['qty']}")
            click.echo(f"  Entry: ${pos['avg_entry_price']:.2f}")
            click.echo(f"  Current: ${pos['current_price']:.2f}")
            click.echo(f"  Market Value: ${pos['market_value']:,.2f}")

            pl_color = "green" if pos['unrealized_pl'] >= 0 else "red"
            click.echo(f"  P&L: ", nl=False)
            click.secho(f"${pos['unrealized_pl']:+,.2f} ({pos['unrealized_plpc']*100:+.2f}%)",
                       fg=pl_color)
            click.echo()

        click.echo(f"{'='*70}")
        click.echo(f"Total Market Value: ${total_value:,.2f}")
        click.echo(f"Total Unrealized P&L: ", nl=False)
        click.secho(f"${total_pl:+,.2f}", fg="green" if total_pl >= 0 else "red")
        click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@company.command()
@click.option('--check-broker', is_flag=True, help='Check broker connection')
def status(check_broker):
    """Check company system status."""
    config = get_config()

    click.echo("\n" + "="*60)
    click.echo("System Status")
    click.echo("="*60 + "\n")

    # Check configuration files
    company_config = config.load_company_config()
    if company_config:
        click.echo("✓ Company configuration loaded")
    else:
        click.echo("✗ Company configuration not found", err=True)

    risk_limits = config.load_risk_limits()
    if risk_limits:
        click.echo("✓ Risk limits configuration loaded")
    else:
        click.echo("✗ Risk limits not found", err=True)

    # Check agents
    agents = config.list_agents()
    click.echo(f"✓ Found {len(agents)} agent(s)")

    # Check broker if requested
    if check_broker:
        try:
            broker = get_broker()
            account = broker.get_account_info()
            click.echo(f"✓ Broker connection successful")
            click.echo(f"  Account equity: ${account['equity']:,.2f}")
        except Exception as e:
            click.echo(f"✗ Broker connection failed: {e}", err=True)

    click.echo()


@company.command()
def risk_check():
    """Perform risk checks across all agents."""
    config = get_config()

    click.echo(f"\n{'='*60}")
    click.echo("Risk Check")
    click.echo(f"{'='*60}\n")

    # Load risk limits
    risk_limits = config.load_risk_limits()
    company_config = config.load_company_config()

    max_capital = company_config.get('max_capital_allocation', 100000)

    # Check each agent
    agents = config.list_agents()
    total_allocated = 0
    issues = []

    for agent_id in agents:
        agent_config = config.load_agent_config(agent_id)
        agent_state = config.load_agent_state(agent_id)

        capital = agent_config.get('performance', {}).get('allocated_capital', 0)
        pnl = agent_state.get('pnl_today', 0)
        max_daily_trades = agent_config.get('risk', {}).get('max_daily_trades', 10)
        trades_today = agent_state.get('trades_today', 0)

        total_allocated += capital

        # Check for issues
        if pnl < -1000:  # Example threshold
            issues.append(f"{agent_id}: Daily loss ${pnl:.2f}")

        if trades_today >= max_daily_trades:
            issues.append(f"{agent_id}: Hit daily trade limit ({trades_today}/{max_daily_trades})")

    # Display summary
    click.echo(f"Total Capital Allocated: ${total_allocated:,.2f} / ${max_capital:,.2f}")

    utilization = (total_allocated / max_capital * 100) if max_capital > 0 else 0
    click.echo(f"Capital Utilization: {utilization:.1f}%\n")

    if issues:
        click.echo("⚠️  Risk Issues Detected:")
        for issue in issues:
            click.echo(f"  - {issue}")
    else:
        click.echo("✓ No risk issues detected")

    click.echo()
