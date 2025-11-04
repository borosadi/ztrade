"""Configuration loading and management utilities."""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from cli.utils.logger import get_logger

logger = get_logger(__name__)


class Config:
    """Configuration loader and manager."""

    def __init__(self, base_path: Optional[str] = None):
        """Initialize config loader.

        Args:
            base_path: Base directory path (defaults to project root)
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.agents_dir = self.base_path / "agents"
        self.config_dir = self.base_path / "config"

    def load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load a YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML as dict
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"YAML file not found: {file_path}")
            return {}

        with open(path, 'r') as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML {file_path}: {e}")
                return {}

    def load_json(self, file_path: str) -> Dict[str, Any]:
        """Load a JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON as dict
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"JSON file not found: {file_path}")
            return {}

        with open(path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON {file_path}: {e}")
                return {}

    def save_yaml(self, data: Dict[str, Any], file_path: str) -> bool:
        """Save data to YAML file.

        Args:
            data: Data to save
            file_path: Path to save to

        Returns:
            True if successful
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Saved YAML to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving YAML to {file_path}: {e}")
            return False

    def save_json(self, data: Dict[str, Any], file_path: str, indent: int = 2) -> bool:
        """Save data to JSON file.

        Args:
            data: Data to save
            file_path: Path to save to
            indent: JSON indentation

        Returns:
            True if successful
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=indent)
            logger.info(f"Saved JSON to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {e}")
            return False

    def get_agent_dir(self, agent_id: str) -> Path:
        """Get path to agent directory.

        Args:
            agent_id: Agent identifier

        Returns:
            Path to agent directory
        """
        return self.agents_dir / agent_id

    def load_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """Load agent configuration.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent config dict
        """
        agent_dir = self.get_agent_dir(agent_id)
        config_path = agent_dir / "context.yaml"
        return self.load_yaml(str(config_path))

    def load_agent_state(self, agent_id: str) -> Dict[str, Any]:
        """Load agent state.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent state dict
        """
        agent_dir = self.get_agent_dir(agent_id)
        state_path = agent_dir / "state.json"
        return self.load_json(str(state_path))

    def save_agent_state(self, agent_id: str, state: Dict[str, Any]) -> bool:
        """Save agent state.

        Args:
            agent_id: Agent identifier
            state: State data to save

        Returns:
            True if successful
        """
        agent_dir = self.get_agent_dir(agent_id)
        state_path = agent_dir / "state.json"
        return self.save_json(state, str(state_path))

    def load_agent_personality(self, agent_id: str) -> str:
        """Load agent personality markdown.

        Args:
            agent_id: Agent identifier

        Returns:
            Personality text
        """
        agent_dir = self.get_agent_dir(agent_id)
        personality_path = agent_dir / "personality.md"

        if not personality_path.exists():
            return ""

        with open(personality_path, 'r') as f:
            return f.read()

    def list_agents(self) -> List[str]:
        """List all agent directories.

        Returns:
            List of agent IDs
        """
        if not self.agents_dir.exists():
            return []

        return [
            d.name for d in self.agents_dir.iterdir()
            if d.is_dir() and (d / "context.yaml").exists()
        ]

    def agent_exists(self, agent_id: str) -> bool:
        """Check if an agent exists.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent exists
        """
        agent_dir = self.get_agent_dir(agent_id)
        return agent_dir.exists() and (agent_dir / "context.yaml").exists()

    def load_company_config(self) -> Dict[str, Any]:
        """Load company configuration.

        Returns:
            Company config dict
        """
        config_path = self.config_dir / "company_config.yaml"
        return self.load_yaml(str(config_path))

    def load_risk_limits(self) -> Dict[str, Any]:
        """Load risk limits configuration.

        Returns:
            Risk limits dict
        """
        config_path = self.config_dir / "risk_limits.yaml"
        return self.load_yaml(str(config_path))


def get_config(base_path: Optional[str] = None) -> Config:
    """Factory function to get a config instance.

    Args:
        base_path: Optional base path override

    Returns:
        Config instance
    """
    return Config(base_path)
