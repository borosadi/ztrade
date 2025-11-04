"""Claude AI integration for agent decision-making."""
import os
from typing import Optional, Dict, Any, List
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class ClaudeAgent:
    """Interface for Claude AI agent interactions."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        """Initialize Claude client.

        Args:
            model: Claude model to use (default: claude-sonnet-4)
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=api_key)
        self.model = model

    def ask(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Send a prompt to Claude and get a response.

        Args:
            prompt: The user prompt/question
            system_prompt: System instructions for the agent
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            context: Previous conversation context

        Returns:
            Claude's response text
        """
        messages = context or []
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def analyze_trade(
        self,
        agent_personality: str,
        market_data: Dict[str, Any],
        agent_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ask agent to analyze market and make trading decision.

        Args:
            agent_personality: Agent's personality/strategy from personality.md
            market_data: Current market data and indicators
            agent_context: Agent configuration and current state

        Returns:
            Dict with decision, rationale, and confidence
        """
        system_prompt = f"""You are an autonomous trading agent with the following personality:

{agent_personality}

Your role is to analyze market data and make informed trading decisions based on your strategy.
You must provide:
1. Decision (BUY, SELL, HOLD, or CLOSE)
2. Detailed rationale
3. Confidence level (0-100)
4. Risk assessment
5. Proposed position size (if applicable)

Always respect your risk parameters and trading philosophy."""

        prompt = f"""Current Market Data:
{self._format_market_data(market_data)}

Your Current State:
{self._format_agent_state(agent_context)}

Based on your strategy and the current market conditions, what is your trading decision?

Respond in JSON format:
{{
    "decision": "BUY|SELL|HOLD|CLOSE",
    "rationale": "detailed explanation",
    "confidence": 0-100,
    "risk_level": "low|medium|high",
    "position_size": amount in USD or null,
    "stop_loss": price level or null,
    "take_profit": price level or null
}}"""

        response = self.ask(prompt, system_prompt=system_prompt, temperature=0.7)

        # Parse JSON response
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # If not valid JSON, return structured error
            return {
                "decision": "HOLD",
                "rationale": f"Error parsing response: {response}",
                "confidence": 0,
                "risk_level": "high",
                "position_size": None,
                "stop_loss": None,
                "take_profit": None
            }

    def _format_market_data(self, data: Dict[str, Any]) -> str:
        """Format market data for prompt."""
        return "\n".join([f"- {k}: {v}" for k, v in data.items()])

    def _format_agent_state(self, context: Dict[str, Any]) -> str:
        """Format agent state for prompt."""
        state = context.get('state', {})
        return f"""
- Current Positions: {len(state.get('positions', []))}
- Daily P&L: ${state.get('pnl_today', 0):.2f}
- Trades Today: {state.get('trades_today', 0)}
- Allocated Capital: ${context.get('allocated_capital', 0):.2f}
- Max Daily Trades: {context.get('risk', {}).get('max_daily_trades', 'N/A')}
"""


def get_agent_llm(model: Optional[str] = None) -> ClaudeAgent:
    """Factory function to get a Claude agent instance.

    Args:
        model: Optional model override

    Returns:
        ClaudeAgent instance
    """
    return ClaudeAgent(model=model) if model else ClaudeAgent()
