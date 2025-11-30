"""Backtesting commands for strategy validation."""
import click
from datetime import datetime, timedelta
from tabulate import tabulate

from cli.utils.logger import get_logger
from cli.utils.backtesting_engine import run_backtest
from cli.utils.database import get_db_connection
from cli.utils.config import get_config

logger = get_logger(__name__)


@click.group()
def backtest():
    """Run and manage backtests for trading strategies."""
    pass


@backtest.command()
@click.argument('agent_id')
@click.option('--start', '-s', help='Start date (YYYY-MM-DD)', required=True)
@click.option('--end', '-e', help='End date (YYYY-MM-DD)', required=True)
@click.option('--no-save', is_flag=True, help='Don\'t save results to database')
def run(agent_id, start, end, no_save):
    """
    Run a backtest for an agent.

    Example:
        uv run ztrade backtest run agent_spy --start 2024-01-01 --end 2024-12-31
    """
    try:
        # Parse dates
        start_date = datetime.strptime(start, '%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d')

        if start_date >= end_date:
            click.echo(click.style("❌ Start date must be before end date", fg='red'))
            return

        click.echo(f"\n🔄 Running backtest for {agent_id}")
        click.echo(f"   Period: {start_date.date()} to {end_date.date()}")
        click.echo()

        # Run backtest
        results = run_backtest(
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
            save=not no_save
        )

        # Display results
        display_backtest_results(results)

        if not no_save and 'run_id' in results:
            click.echo(f"\n💾 Saved as run #{results['run_id']}")
            click.echo(f"   View details: uv run ztrade backtest show {results['run_id']}")

    except ValueError as e:
        click.echo(click.style(f"❌ Error: {e}", fg='red'))
    except Exception as e:
        click.echo(click.style(f"❌ Backtest failed: {e}", fg='red'))
        logger.error(f"Backtest error: {e}", exc_info=True)


@backtest.command()
@click.option('--limit', '-n', default=10, help='Number of runs to show')
@click.option('--agent', '-a', help='Filter by agent ID')
def list(limit, agent):
    """
    List recent backtest runs.

    Example:
        uv run ztrade backtest list --limit 20
        uv run ztrade backtest list --agent agent_spy
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if agent:
                    cur.execute("""
                        SELECT id, agent_id, start_date, end_date,
                               total_return_pct, total_trades, win_rate,
                               created_at
                        FROM backtest_runs
                        WHERE agent_id = %s AND status = 'completed'
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (agent, limit))
                else:
                    cur.execute("""
                        SELECT id, agent_id, start_date, end_date,
                               total_return_pct, total_trades, win_rate,
                               created_at
                        FROM backtest_runs
                        WHERE status = 'completed'
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (limit,))

                rows = cur.fetchall()

        if not rows:
            click.echo("No backtest runs found")
            return

        # Format table
        headers = ['Run ID', 'Agent', 'Start', 'End', 'Return %', 'Trades', 'Win Rate', 'Created']
        table_data = []

        for row in rows:
            table_data.append([
                row[0],  # ID
                row[1],  # Agent ID
                row[2].strftime('%Y-%m-%d'),  # Start
                row[3].strftime('%Y-%m-%d'),  # End
                f"{row[4]:.2f}%" if row[4] else 'N/A',  # Return
                row[5],  # Trades
                f"{row[6]*100:.1f}%" if row[6] else 'N/A',  # Win rate
                row[7].strftime('%Y-%m-%d %H:%M')  # Created
            ])

        click.echo("\n📊 Recent Backtest Runs:\n")
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

    except Exception as e:
        click.echo(click.style(f"❌ Error listing backtests: {e}", fg='red'))
        logger.error(f"List error: {e}", exc_info=True)


@backtest.command()
@click.argument('run_id', type=int)
@click.option('--trades', is_flag=True, help='Show individual trades')
def show(run_id, trades):
    """
    Show details of a backtest run.

    Example:
        uv run ztrade backtest show 42
        uv run ztrade backtest show 42 --trades
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get run details
                cur.execute("""
                    SELECT agent_id, start_date, end_date,
                           initial_capital, final_capital, total_return_pct,
                           total_trades, winning_trades, losing_trades,
                           win_rate, avg_trade_pnl, max_drawdown, sharpe_ratio,
                           created_at
                    FROM backtest_runs
                    WHERE id = %s
                """, (run_id,))

                run = cur.fetchone()

                if not run:
                    click.echo(click.style(f"❌ Run #{run_id} not found", fg='red'))
                    return

                # Display run details
                click.echo(f"\n📊 Backtest Run #{run_id}")
                click.echo("=" * 60)
                click.echo(f"Agent:          {run[0]}")
                click.echo(f"Period:         {run[1].strftime('%Y-%m-%d')} to {run[2].strftime('%Y-%m-%d')}")
                click.echo(f"Created:        {run[13].strftime('%Y-%m-%d %H:%M')}")
                click.echo()

                click.echo("💰 Performance:")
                click.echo(f"  Initial Capital:  ${run[3]:,.2f}")
                click.echo(f"  Final Capital:    ${run[4]:,.2f}")
                click.echo(f"  Total Return:     {run[5]:.2f}%")
                click.echo(f"  Max Drawdown:     {run[11]:.2f}%")
                click.echo(f"  Sharpe Ratio:     {run[12]:.2f}")
                click.echo()

                click.echo("📈 Trading Stats:")
                click.echo(f"  Total Trades:     {run[6]}")
                click.echo(f"  Winning Trades:   {run[7]}")
                click.echo(f"  Losing Trades:    {run[8]}")
                click.echo(f"  Win Rate:         {run[9]*100:.1f}%")
                click.echo(f"  Avg Trade P&L:    ${run[10]:,.2f}")
                click.echo()

                # Show trades if requested
                if trades:
                    cur.execute("""
                        SELECT timestamp, action, symbol, quantity, price, pnl,
                               portfolio_value
                        FROM backtest_trades
                        WHERE run_id = %s
                        ORDER BY timestamp
                    """, (run_id,))

                    trade_rows = cur.fetchall()

                    if trade_rows:
                        click.echo("📝 Trades:")
                        headers = ['Date', 'Action', 'Symbol', 'Qty', 'Price', 'P&L', 'Portfolio']
                        table_data = []

                        for trade in trade_rows:
                            table_data.append([
                                trade[0].strftime('%Y-%m-%d %H:%M'),
                                trade[1].upper(),
                                trade[2],
                                trade[3],
                                f"${trade[4]:.2f}",
                                f"${trade[5]:.2f}" if trade[5] else '-',
                                f"${trade[6]:,.2f}" if trade[6] else '-'
                            ])

                        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

    except Exception as e:
        click.echo(click.style(f"❌ Error showing backtest: {e}", fg='red'))
        logger.error(f"Show error: {e}", exc_info=True)


@backtest.command()
@click.argument('run_ids', nargs=-1, type=int, required=True)
def compare(run_ids):
    """
    Compare multiple backtest runs.

    Example:
        uv run ztrade backtest compare 42 43 44
    """
    if len(run_ids) < 2:
        click.echo(click.style("❌ Need at least 2 runs to compare", fg='red'))
        return

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get runs
                placeholders = ','.join(['%s'] * len(run_ids))
                cur.execute(f"""
                    SELECT id, agent_id, total_return_pct, total_trades,
                           win_rate, max_drawdown, sharpe_ratio
                    FROM backtest_runs
                    WHERE id IN ({placeholders})
                    ORDER BY total_return_pct DESC
                """, run_ids)

                rows = cur.fetchall()

        if not rows:
            click.echo(click.style("❌ No runs found", fg='red'))
            return

        # Format comparison table
        headers = ['Run ID', 'Agent', 'Return %', 'Trades', 'Win Rate', 'Max DD', 'Sharpe']
        table_data = []

        for row in rows:
            table_data.append([
                row[0],  # ID
                row[1],  # Agent
                f"{row[2]:.2f}%",  # Return
                row[3],  # Trades
                f"{row[4]*100:.1f}%",  # Win rate
                f"{row[5]:.2f}%",  # Max drawdown
                f"{row[6]:.2f}"  # Sharpe
            ])

        click.echo("\n📊 Backtest Comparison:\n")
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

        # Highlight best performers
        if len(rows) > 1:
            best_return = max(rows, key=lambda x: x[2] or 0)
            best_sharpe = max(rows, key=lambda x: x[6] or 0)

            click.echo()
            click.echo(f"🏆 Best Return:  Run #{best_return[0]} ({best_return[2]:.2f}%)")
            click.echo(f"📈 Best Sharpe:  Run #{best_sharpe[0]} ({best_sharpe[6]:.2f})")

    except Exception as e:
        click.echo(click.style(f"❌ Error comparing backtests: {e}", fg='red'))
        logger.error(f"Compare error: {e}", exc_info=True)


def display_backtest_results(results: dict):
    """Display backtest results in a formatted way."""
    metrics = results['metrics']

    click.echo("=" * 60)
    click.echo("📊 BACKTEST RESULTS")
    click.echo("=" * 60)
    click.echo()

    click.echo(f"Agent:          {results['agent_id']}")
    click.echo(f"Symbol:         {results['symbol']}")
    click.echo(f"Period:         {results['start_date'].date()} to {results['end_date'].date()}")
    click.echo()

    # Performance section
    click.echo(click.style("💰 PERFORMANCE", bold=True))
    click.echo("-" * 60)

    return_color = 'green' if metrics['total_return_pct'] > 0 else 'red'
    click.echo(f"Initial Capital:    ${metrics['initial_capital']:,.2f}")
    click.echo(f"Final Capital:      ${metrics['final_capital']:,.2f}")
    click.echo(f"Total Return:       " + click.style(f"{metrics['total_return_pct']:.2f}%", fg=return_color, bold=True))
    click.echo(f"Max Drawdown:       {metrics['max_drawdown']:.2f}%")
    click.echo(f"Sharpe Ratio:       {metrics['sharpe_ratio']:.2f}")
    click.echo()

    # Trading stats section
    click.echo(click.style("📈 TRADING STATISTICS", bold=True))
    click.echo("-" * 60)
    click.echo(f"Total Trades:       {metrics['total_trades']}")
    click.echo(f"Winning Trades:     {metrics['winning_trades']}")
    click.echo(f"Losing Trades:      {metrics['losing_trades']}")
    click.echo(f"Win Rate:           {metrics['win_rate']*100:.1f}%")
    click.echo(f"Avg Trade P&L:      ${metrics['avg_trade_pnl']:,.2f}")
    click.echo()

    # Sample trades
    if results.get('trades'):
        trades = results['trades']
        sells = [t for t in trades if t['action'] == 'sell']

        if sells:
            click.echo(click.style("💼 SAMPLE TRADES (First 5)", bold=True))
            click.echo("-" * 60)

            headers = ['Date', 'Action', 'Qty', 'Price', 'P&L']
            table_data = []

            for trade in sells[:5]:
                pnl_color = 'green' if trade.get('pnl', 0) > 0 else 'red'
                table_data.append([
                    trade['timestamp'].strftime('%Y-%m-%d'),
                    trade['action'].upper(),
                    trade['quantity'],
                    f"${trade['price']:.2f}",
                    click.style(f"${trade.get('pnl', 0):.2f}", fg=pnl_color)
                ])

            click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))
            click.echo()

    click.echo("=" * 60)
