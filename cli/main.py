import click
from cli.commands.agent import agent

@click.group()
def cli():
    """Ztrade is a command-line tool for managing your AI trading company."""
    pass

cli.add_command(agent)

@cli.command()
def hello():
    """Prints a welcome message."""
    click.echo("Welcome to Ztrade!")

if __name__ == '__main__':
    cli()
