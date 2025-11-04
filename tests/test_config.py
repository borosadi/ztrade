"""Tests for configuration utilities."""
import pytest
import tempfile
import json
import yaml
from pathlib import Path
from cli.utils.config import Config


def test_config_load_yaml(tmp_path):
    """Test loading YAML files."""
    # Create a test YAML file
    test_file = tmp_path / "test.yaml"
    data = {"key": "value", "number": 42}

    with open(test_file, 'w') as f:
        yaml.dump(data, f)

    config = Config(base_path=str(tmp_path))
    loaded = config.load_yaml(str(test_file))

    assert loaded == data


def test_config_load_json(tmp_path):
    """Test loading JSON files."""
    # Create a test JSON file
    test_file = tmp_path / "test.json"
    data = {"key": "value", "number": 42}

    with open(test_file, 'w') as f:
        json.dump(data, f)

    config = Config(base_path=str(tmp_path))
    loaded = config.load_json(str(test_file))

    assert loaded == data


def test_config_save_yaml(tmp_path):
    """Test saving YAML files."""
    config = Config(base_path=str(tmp_path))
    test_file = tmp_path / "output.yaml"
    data = {"test": "data"}

    success = config.save_yaml(data, str(test_file))

    assert success
    assert test_file.exists()

    # Verify content
    with open(test_file) as f:
        loaded = yaml.safe_load(f)
    assert loaded == data


def test_config_save_json(tmp_path):
    """Test saving JSON files."""
    config = Config(base_path=str(tmp_path))
    test_file = tmp_path / "output.json"
    data = {"test": "data"}

    success = config.save_json(data, str(test_file))

    assert success
    assert test_file.exists()

    # Verify content
    with open(test_file) as f:
        loaded = json.load(f)
    assert loaded == data


def test_config_list_agents(tmp_path):
    """Test listing agents."""
    # Create some test agents
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # Agent 1
    agent1_dir = agents_dir / "agent1"
    agent1_dir.mkdir()
    (agent1_dir / "context.yaml").write_text("test: data")

    # Agent 2
    agent2_dir = agents_dir / "agent2"
    agent2_dir.mkdir()
    (agent2_dir / "context.yaml").write_text("test: data")

    # Directory without context.yaml (should be ignored)
    invalid_dir = agents_dir / "invalid"
    invalid_dir.mkdir()

    config = Config(base_path=str(tmp_path))
    agents = config.list_agents()

    assert len(agents) == 2
    assert "agent1" in agents
    assert "agent2" in agents
    assert "invalid" not in agents


def test_config_agent_exists(tmp_path):
    """Test checking if agent exists."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    agent_dir = agents_dir / "test_agent"
    agent_dir.mkdir()
    (agent_dir / "context.yaml").write_text("test: data")

    config = Config(base_path=str(tmp_path))

    assert config.agent_exists("test_agent")
    assert not config.agent_exists("nonexistent")
