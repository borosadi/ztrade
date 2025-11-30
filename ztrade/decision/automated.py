"""Automated trading decision maker using Anthropic API.

This module provides automated decision-making for agents running outside
Claude Code terminal (e.g., in Celery, cron, or background loops).
"""
import os
import json
import re
from typing import Dict, Any, Optional
from ztrade.core.logger import get_logger

logger = get_logger(__name__)


class AutomatedDecisionMaker:
    """Makes trading decisions using Anthropic API."""

    def __init__(self):
        """Initialize with API key from environment."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None

        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Anthropic API client initialized")
            except ImportError:
                logger.warning("anthropic package not installed. Run: pip install anthropic")
                self.client = None
        else:
            logger.warning("ANTHROPIC_API_KEY not set in environment")

    def is_available(self) -> bool:
        """Check if automated decisions are available."""
        return self.client is not None

    def make_decision(self, context: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Make a trading decision using Anthropic API.

        Args:
            context: Trading context with market data, sentiment, agent personality
            timeout: API timeout in seconds

        Returns:
            Dict with decision in format:
            {
                "action": "buy" | "sell" | "hold",
                "quantity": int,
                "rationale": str,
                "confidence": float,
                "stop_loss": float (optional, for buy orders)
            }

        Raises:
            RuntimeError: If API key not configured or API call fails
            ValueError: If response is not valid JSON
        """
        if not self.is_available():
            raise RuntimeError(
                "Automated decisions not available. Set ANTHROPIC_API_KEY in .env "
                "and install: pip install anthropic"
            )

        try:
            logger.info("Requesting trading decision from Anthropic API...")

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                temperature=0.7,
                system="""You are an expert trading decision agent. Analyze the trading context
and provide a JSON decision. Be concise and data-driven. Consider both technical
indicators and sentiment signals. Always include your confidence level.""",
                messages=[
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                timeout=timeout
            )

            # Extract text from response
            response_text = response.content[0].text.strip()

            logger.debug(f"API response: {response_text[:200]}...")

            # Try to extract JSON from response (in case model added explanation)
            json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', response_text, re.DOTALL)

            if json_match:
                decision = json.loads(json_match.group())
            else:
                # Try parsing entire response as JSON
                decision = json.loads(response_text)

            # Validate decision format
            required_fields = ["action", "rationale", "confidence"]
            for field in required_fields:
                if field not in decision:
                    raise ValueError(f"Missing required field: {field}")

            # Validate action
            if decision["action"] not in ["buy", "sell", "hold"]:
                raise ValueError(f"Invalid action: {decision['action']}")

            # Validate confidence
            if not (0.0 <= decision.get("confidence", 0) <= 1.0):
                raise ValueError(f"Confidence must be between 0.0 and 1.0")

            # Ensure quantity exists
            if "quantity" not in decision:
                decision["quantity"] = 0 if decision["action"] == "hold" else 100

            logger.info(
                f"Decision: {decision['action'].upper()} "
                f"(confidence: {decision['confidence']:.0%})"
            )

            return decision

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON decision: {e}")
            logger.error(f"Response was: {response_text}")
            raise ValueError(f"Invalid JSON in API response: {e}")

        except Exception as e:
            logger.error(f"Error making automated decision: {e}")
            raise RuntimeError(f"Automated decision failed: {e}")


# Singleton instance
_decision_maker = None


def get_automated_decision_maker() -> AutomatedDecisionMaker:
    """Get or create the automated decision maker singleton."""
    global _decision_maker
    if _decision_maker is None:
        _decision_maker = AutomatedDecisionMaker()
    return _decision_maker
