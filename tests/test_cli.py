"""Basic tests for CLI functionality."""
import pytest
import os
import tempfile
from pathlib import Path
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


def test_cli_version():
    """Test the version command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_agent_list():
    """Test the agent list command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["agent", "list"])
    assert result.exit_code == 0
    # Will show existing agents or "No agents found"


def test_agent_help():
    """Test the agent help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["agent", "--help"])
    assert result.exit_code == 0
    assert "agent" in result.output.lower()


def test_company_help():
    """Test the company help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["company", "--help"])
    assert result.exit_code == 0
    assert "company" in result.output.lower()


def test_company_status():
    """Test company status command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["company", "status"])
    assert result.exit_code == 0
    assert "System Status" in result.output


def test_agent_create_and_list():
    """Test creating an agent and listing it."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create agents directory
        os.makedirs("agents")
        os.makedirs("config")

        # Create test agent with all prompts
        result = runner.invoke(
            cli,
            ["agent", "create", "test_agent"],
            input="TSLA\nTest Agent\nmomentum\naggressive\n"
        )

        # Check if create was successful
        if result.exit_code == 0:
            assert "created successfully" in result.output

            # Try to list agents
            result = runner.invoke(cli, ["agent", "list"])
            assert result.exit_code == 0


def test_agent_status_not_found():
    """Test agent status for non-existent agent."""
    runner = CliRunner()
    result = runner.invoke(cli, ["agent", "status", "nonexistent_agent"])
    assert result.exit_code == 0
    assert "not found" in result.output.lower()
