"""Basic tests for CLI functionality."""
import pytest
from click.testing import CliRunner
from cli.main import cli


def test_cli_hello():
    """Test the hello command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["hello"])
    assert result.exit_code == 0
    assert "Welcome to Ztrade!" in result.output


def test_cli_help():
    """Test the help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Ztrade" in result.output


def test_agent_list():
    """Test the agent list command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["agent", "list"])
    assert result.exit_code == 0
    assert "Listing all agents" in result.output
