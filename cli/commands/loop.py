"""Loop management commands for continuous trading."""

import click
from cli.utils.loop_manager import get_loop_manager, LoopSchedule
from cli.utils.logger import get_logger
from cli.utils.config import get_config

logger = get_logger(__name__)


@click.group()
def loop():
    """Commands for managing continuous trading loops."""
    pass


@loop.command()
@click.argument('agent_id')
@click.option('--interval', type=int, default=300, help='Seconds between cycles (default 300 = 5 min)')
@click.option('--max-cycles', type=int, default=None, help='Maximum cycles before stopping')
@click.option('--dry-run', is_flag=True, help='Run without executing trades')
@click.option('--manual', is_flag=True, help='Use manual mode')
@click.option('--subagent', is_flag=True, help='Use subagent mode')
@click.option('--market-hours/--no-market-hours', default=True, help='Only trade during market hours (default: on)')
def start(agent_id, interval, max_cycles, dry_run, manual, subagent, market_hours):
    """Start a continuous trading loop for an agent."""
    config = get_config()

    # Verify agent exists
    if not config.agent_exists(agent_id):
        click.echo(f"Error: Agent '{agent_id}' not found!", err=True)
        return

    agent_config = config.load_agent_config(agent_id)
    asset = agent_config.get('agent', {}).get('asset', 'UNKNOWN')

    # Create cycle function that runs the trading cycle
    def run_cycle(agent_id_param, loop_config):
        """Run a single trading cycle."""
        try:
            logger.info(f"Cycle started for {agent_id_param} ({asset})")

            # Simple test: just log that we ran
            # TODO: Add market data fetch, analysis, and trading decision
            logger.info(f"Cycle executed for {agent_id_param}")

        except Exception as e:
            logger.error(f"Error in trading cycle for {agent_id_param}: {e}", exc_info=True)

    # Start the loop
    loop_manager = get_loop_manager()
    success = loop_manager.start_loop(
        agent_id=agent_id,
        interval_seconds=interval,
        max_cycles=max_cycles,
        dry_run=dry_run,
        manual=manual,
        subagent=subagent,
        market_hours_only=market_hours,
        cycle_func=run_cycle
    )

    if success:
        click.echo(f"\n✅ Started continuous loop for {agent_id} ({asset})")
        click.echo(f"   Interval: {interval} seconds")
        click.echo(f"   Max cycles: {max_cycles if max_cycles else 'unlimited'}")
        click.echo(f"   Market hours only: {market_hours}")
        click.echo(f"   Dry run: {dry_run}")
        click.echo(f"\n   Use 'ztrade loop stop {agent_id}' to stop the loop")
        click.echo(f"   Press Ctrl+C to stop or run 'ztrade loop status {agent_id}' to check status\n")

        # Keep main process alive by monitoring the loop
        import time
        try:
            while True:
                time.sleep(0.5)
                # Check if loop has completed
                status = loop_manager.get_loop_status(agent_id)
                if not status or status['status'] in ['stopped', 'error']:
                    logger.info(f"Loop completed for {agent_id}")
                    break
        except KeyboardInterrupt:
            click.echo("\n\nKeyboard interrupt - stopping loop...")
            loop_manager.stop_loop(agent_id)
            time.sleep(1)
            click.echo(f"✅ Loop stopped for {agent_id}")
    else:
        click.echo(f"❌ Failed to start loop for {agent_id}", err=True)


@loop.command()
@click.argument('agent_id')
def stop(agent_id):
    """Stop a running loop."""
    loop_manager = get_loop_manager()

    success = loop_manager.stop_loop(agent_id)

    if success:
        status = loop_manager.get_loop_status(agent_id)
        click.echo(f"\n✅ Stopped loop for {agent_id}")
        click.echo(f"   Cycles completed: {status['cycles_completed']}")
        click.echo()
    else:
        click.echo(f"❌ No running loop found for {agent_id}", err=True)


@loop.command()
@click.argument('agent_id')
def pause(agent_id):
    """Pause a running loop."""
    loop_manager = get_loop_manager()

    success = loop_manager.pause_loop(agent_id)

    if success:
        click.echo(f"⏸️  Paused loop for {agent_id}")
    else:
        click.echo(f"❌ No running loop found for {agent_id}", err=True)


@loop.command()
@click.argument('agent_id')
def resume(agent_id):
    """Resume a paused loop."""
    loop_manager = get_loop_manager()

    success = loop_manager.resume_loop(agent_id)

    if success:
        click.echo(f"▶️  Resumed loop for {agent_id}")
    else:
        click.echo(f"❌ No paused loop found for {agent_id}", err=True)


@loop.command()
@click.argument('agent_id', required=False)
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
def status(agent_id, verbose):
    """Show loop status."""
    loop_manager = get_loop_manager()

    if agent_id:
        # Show status for specific agent
        status_info = loop_manager.get_loop_status(agent_id)

        if not status_info:
            click.echo(f"No loop found for {agent_id}")
            return

        click.echo(f"\n{'='*60}")
        click.echo(f"Loop Status: {agent_id}")
        click.echo(f"{'='*60}")
        click.echo(f"Status: {status_info['status']}")
        click.echo(f"Cycles Completed: {status_info['cycles_completed']}")
        click.echo(f"Started At: {status_info['started_at']}")
        click.echo(f"Last Cycle: {status_info['last_cycle_at']}")
        click.echo(f"Interval: {status_info['interval_seconds']} seconds")

        if status_info['last_error']:
            click.echo(f"Last Error: {status_info['last_error']}")

        click.echo(f"{'='*60}\n")

    else:
        # Show status for all loops
        loops = loop_manager.list_loops()

        if not loops:
            click.echo("No active loops")
            return

        click.echo(f"\n{'='*60}")
        click.echo(f"Active Trading Loops ({len(loops)})")
        click.echo(f"{'='*60}\n")

        for agent_id, info in loops.items():
            status_symbol = {
                "running": "▶️",
                "paused": "⏸️",
                "error": "❌",
                "stopped": "⏹️"
            }.get(info['status'], "❓")

            click.echo(f"{status_symbol} {agent_id}")
            click.echo(f"   Status: {info['status']}")
            click.echo(f"   Cycles: {info['cycles_completed']}")
            click.echo(f"   Interval: {info['interval_seconds']}s")

            if verbose and info['last_cycle_at']:
                click.echo(f"   Last cycle: {info['last_cycle_at']}")

            if info['last_error']:
                click.echo(f"   Error: {info['last_error']}")

            click.echo()

        click.echo(f"{'='*60}\n")

        # Show market status
        if LoopSchedule.is_market_day():
            if LoopSchedule.is_market_hours():
                click.echo("📊 Market is OPEN (9:30 AM - 4:00 PM EST)")
            else:
                minutes_to_open = LoopSchedule.time_to_market_open()
                click.echo(f"⏰ Market opens in {minutes_to_open} minutes")
        else:
            click.echo("📊 Market is CLOSED (Weekend)")


@loop.command()
def market_hours():
    """Show current market hours status."""
    click.echo("\n" + "="*60)
    click.echo("Market Hours Status")
    click.echo("="*60)

    if LoopSchedule.is_market_day():
        click.echo("📅 Today is a market day (Monday-Friday)")

        if LoopSchedule.is_market_hours():
            click.echo("📊 Market is OPEN")
            click.echo(f"   Regular hours: 9:30 AM - 4:00 PM EST")
        else:
            now_time = __import__('datetime').datetime.now().time()
            if now_time < LoopSchedule.MARKET_OPEN:
                minutes = LoopSchedule.time_to_market_open()
                click.echo(f"⏰ Market opens in {minutes} minutes (9:30 AM EST)")
            else:
                click.echo("📊 Market is CLOSED for the day")
                minutes_to_open = LoopSchedule.time_to_market_open()
                click.echo(f"   Next open: {minutes_to_open // 1440 + 1} days")
    else:
        click.echo("📅 Today is a weekend/holiday")
        minutes_to_open = LoopSchedule.time_to_market_open()
        hours_to_open = minutes_to_open / 60
        click.echo(f"⏰ Market opens in {hours_to_open:.1f} hours (Monday 9:30 AM EST)")

    click.echo("="*60 + "\n")
