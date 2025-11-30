"""Subagent management commands for Claude Code integration."""
import click
import json
from pathlib import Path
from cli.utils.subagent import get_subagent_communicator


@click.group()
def subagent():
    """Commands for managing Claude Code subagents."""
    pass


@subagent.command()
def list():
    """Lists all pending subagent requests."""
    communicator = get_subagent_communicator()
    requests = communicator.list_pending_requests()

    if not requests:
        click.echo("No pending subagent requests.")
        return

    click.echo(f"\n{'='*60}")
    click.echo(f"Pending Subagent Requests ({len(requests)})")
    click.echo(f"{'='*60}\n")

    for request_file in requests:
        with open(request_file, 'r') as f:
            request_data = json.load(f)

        click.echo(f"Request ID: {request_data['request_id']}")
        click.echo(f"Agent: {request_data['agent_id']}")
        click.echo(f"Time: {request_data['timestamp']}")
        click.echo(f"File: {request_file}")
        click.echo()

    click.echo(f"{'='*60}\n")


@subagent.command()
@click.argument('request_id')
def show(request_id):
    """Shows the full context for a subagent request."""
    communicator = get_subagent_communicator()
    request_file = communicator.requests_dir / f"{request_id}.json"

    if not request_file.exists():
        click.echo(f"Error: Request '{request_id}' not found!", err=True)
        return

    with open(request_file, 'r') as f:
        request_data = json.load(f)

    click.echo(f"\n{'='*70}")
    click.echo(f"Subagent Request: {request_id}")
    click.echo(f"{'='*70}\n")
    click.echo(request_data['context'])
    click.echo(f"\n{'='*70}\n")


@subagent.command()
@click.argument('request_id')
@click.argument('decision_json')
def respond(request_id, decision_json):
    """Responds to a subagent request with a trading decision.

    Example:
        ztrade subagent respond abc123 '{"action":"hold","quantity":0,"rationale":"Waiting","confidence":0.6}'
    """
    communicator = get_subagent_communicator()
    request_file = communicator.requests_dir / f"{request_id}.json"

    if not request_file.exists():
        click.echo(f"Error: Request '{request_id}' not found!", err=True)
        return

    try:
        # Parse the decision JSON
        decision = json.loads(decision_json)

        # Validate required fields
        required_fields = ['action', 'rationale', 'confidence']
        for field in required_fields:
            if field not in decision:
                click.echo(f"Error: Missing required field '{field}' in decision!", err=True)
                return

        # Send response
        communicator.respond_to_request(request_id, decision)
        click.echo(f"✓ Response sent for request '{request_id}'")

    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON: {e}", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@subagent.command()
def process():
    """Process the first pending subagent request (for Claude Code to use)."""
    communicator = get_subagent_communicator()
    requests = communicator.list_pending_requests()

    if not requests:
        click.echo("No pending subagent requests to process.")
        return

    # Get first request
    request_file = requests[0]
    with open(request_file, 'r') as f:
        request_data = json.load(f)

    request_id = request_data['request_id']

    click.echo(f"\n{'='*70}")
    click.echo(f"PROCESSING SUBAGENT REQUEST")
    click.echo(f"{'='*70}")
    click.echo(f"Request ID: {request_id}")
    click.echo(f"Agent: {request_data['agent_id']}")
    click.echo(f"{'='*70}\n")
    click.echo(request_data['context'])
    click.echo(f"\n{'='*70}")
    click.echo("\nClaude Code: Please analyze this context and provide your decision.")
    click.echo("After analysis, use this command to respond:")
    click.echo(f"\n  ztrade subagent respond {request_id} '<decision_json>'\n")


@subagent.command()
def clear():
    """Clears all pending subagent requests (cleanup)."""
    communicator = get_subagent_communicator()
    requests = communicator.list_pending_requests()

    if not requests:
        click.echo("No pending requests to clear.")
        return

    for request_file in requests:
        request_file.unlink()

    click.echo(f"✓ Cleared {len(requests)} pending request(s)")
