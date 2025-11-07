"""Subagent utilities for Claude Code integration."""
import json
import time
from pathlib import Path
from datetime import datetime


class SubagentCommunicator:
    """Handles communication between CLI and Claude Code subagents via files."""

    def __init__(self):
        self.requests_dir = Path("oversight/subagent_requests")
        self.responses_dir = Path("oversight/subagent_responses")

        # Create directories if they don't exist
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)

    def request_decision(self, agent_id: str, context: str, timeout: int = 30) -> dict:
        """
        Request a trading decision from Claude Code subagent.

        Args:
            agent_id: The agent requesting the decision
            context: The full trading context for decision-making
            timeout: Maximum seconds to wait for response (default 60)

        Returns:
            dict: The trading decision from the subagent

        Raises:
            TimeoutError: If no response is received within timeout
            ValueError: If response is invalid JSON
        """
        # Create request file
        request_id = f"{agent_id}_{int(time.time())}"
        request_file = self.requests_dir / f"{request_id}.json"
        response_file = self.responses_dir / f"{request_id}.json"

        request_data = {
            "request_id": request_id,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "status": "pending"
        }

        # Write request
        with open(request_file, 'w') as f:
            json.dump(request_data, f, indent=2)

        print(f"\n{'='*70}")
        print("🤖 SUBAGENT REQUEST CREATED")
        print(f"{'='*70}")
        print(f"Request ID: {request_id}")
        print(f"Request File: {request_file}")
        print(f"Response File: {response_file}")
        print(f"\nWaiting for Claude Code subagent to process this request...")
        print(f"(Timeout: {timeout} seconds)")
        print(f"{'='*70}\n")

        # Wait for response with timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            if response_file.exists():
                # Read response
                with open(response_file, 'r') as f:
                    response_data = json.load(f)

                # Validate response
                if "decision" not in response_data:
                    raise ValueError("Invalid response format: missing 'decision' field")

                decision = response_data["decision"]

                # Clean up files
                request_file.unlink(missing_ok=True)
                response_file.unlink(missing_ok=True)

                print("✓ Subagent response received!")
                return decision

            # Wait a bit before checking again
            time.sleep(0.5)

        # Timeout - clean up request file
        request_file.unlink(missing_ok=True)
        raise TimeoutError(f"No response from subagent after {timeout} seconds")

    def list_pending_requests(self):
        """List all pending subagent requests."""
        requests = list(self.requests_dir.glob("*.json"))
        return requests

    def respond_to_request(self, request_id: str, decision: dict):
        """
        Respond to a subagent request (used by Claude Code).

        Args:
            request_id: The request ID to respond to
            decision: The trading decision dict
        """
        response_file = self.responses_dir / f"{request_id}.json"

        response_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "processed_by": "claude_code_subagent"
        }

        with open(response_file, 'w') as f:
            json.dump(response_data, f, indent=2)


def get_subagent_communicator():
    """Get the subagent communicator instance."""
    return SubagentCommunicator()
