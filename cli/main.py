"""Main CLI entry point for Ztrade."""
import click
from cli.commands.agent import agent
from cli.commands.company import company


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Ztrade - AI-powered trading company management CLI.

    Manage autonomous trading agents, monitor positions, and oversee
    risk across your AI trading company.
    """
    pass


# Register command groups
cli.add_command(agent)
cli.add_command(company)


@cli.command()
def hello():
    """Prints a welcome message."""
    click.echo("\n" + "="*60)
    click.echo(" "*15 + "Welcome to Ztrade!")
    click.echo("="*60)
    click.echo("\nAI-Powered Trading Company Management\n")
    click.echo("Quick commands:")
    click.echo("  ztrade company dashboard  - View company overview")
    click.echo("  ztrade agent list         - List all agents")
    click.echo("  ztrade agent create <id>  - Create a new agent")
    click.echo("  ztrade --help             - Show all commands")
    click.echo()


if __name__ == '__main__':
    cli()
