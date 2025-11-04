# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ztrade is an AI-powered trading company system where multiple autonomous AI agents trade different assets independently. Each agent specializes in a specific asset (BTC, SPY, EUR, TSLA) with its own strategy, risk profile, and personality. The system is managed through a CLI interface built with Python Click.

**Key Technologies:**
- **AI**: Claude 4 (Anthropic API) for agent decision-making
- **Broker**: Alpaca API (paper trading via alpaca-py)
- **Market Data**: TradingView via Model Context Protocol (MCP)
- **CLI**: Python Click framework
- **Language**: Python 3.10+

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify environment setup
python cli/main.py hello
```

### Running the CLI
```bash
# Main CLI entry point
python cli/main.py [COMMAND]

# Agent commands
python cli/main.py agent list
python cli/main.py agent status AGENT_ID
python cli/main.py agent create AGENT_ID
python cli/main.py agent run AGENT_ID
python cli/main.py agent ask AGENT_ID "question"
```

### Testing
```bash
# Run backtests
python -m pytest tests/backtests/

# Paper trading tests
python -m pytest tests/paper_trading/

# Run specific test
python -m pytest tests/backtests/test_strategy.py
```

## Architecture

### Multi-Agent System Design

The system uses a hierarchical architecture:

```
You (Company Manager) → CLI Commands
         ↓
Trading Company System (Risk Manager & Oversight)
         ↓
    Trading Agents (agent_btc, agent_spy, agent_forex_eur, agent_tsla)
         ↓
External Services (TradingView MCP + Alpaca API)
```

**Key Principle**: Each agent operates autonomously but submits to company-wide risk management and oversight. Agents have distinct personalities, strategies, and risk profiles defined in their configuration files.

### Directory Structure

- **`agents/`**: Each subdirectory contains an autonomous trading agent with:
  - `context.yaml`: Agent configuration (strategy, timeframe, risk parameters)
  - `personality.md`: Trading philosophy and decision-making style
  - `performance.json`: Historical trading results and metrics
  - `state.json`: Current positions and daily state
  - `learning.json`: Pattern recognition and adaptive learning data

- **`cli/`**: Command-line interface implementation
  - `main.py`: Entry point for the CLI
  - `commands/`: Command groups (agent.py, company.py, monitor.py, risk.py)
  - `utils/`: Shared utilities (broker.py, llm.py, mcp_client.py, logger.py)

- **`config/`**: System-wide configuration
  - `company_config.yaml`: Capital allocation and trading parameters
  - `risk_limits.yaml`: Company-wide risk management rules
  - `broker_config.yaml`: Alpaca API credentials and settings

- **`shared/`**: Cross-agent resources
  - `market_data/`: Shared market intelligence (market_intel.yaml)
  - `research/`: Collective research notes
  - `correlations.json`: Cross-asset correlation tracking

- **`oversight/`**: Risk management and monitoring
  - `daily_reports/`: Generated performance reports
  - `risk_dashboard.json`: Real-time risk metrics
  - `audit_log.json`: Compliance and audit trail
  - `alerts/`: Critical notifications

- **`mcp/`**: Model Context Protocol integration
  - `tradingview_server.py`: MCP server wrapper for TradingView data
  - `mcp_config.json`: MCP configuration

- **`logs/`**: Structured logging
  - `trades/`: Trade execution logs (organized by date)
  - `agent_decisions/`: Agent reasoning and decision logs
  - `system/`: System events and errors

- **`tests/`**: Testing framework
  - `backtests/`: Historical strategy testing
  - `paper_trading/`: Paper trading validation

### Agent Autonomy Model

Each agent is designed with:

1. **Specialization**: Single asset focus with specific strategy (momentum, mean reversion, breakout)
2. **Autonomy**: Independent market analysis and trade decisions without human input
3. **Accountability**: All decisions logged with rationale; performance tracked; risk limits enforced
4. **Personality**: Distinct decision-making style defined in personality.md (e.g., aggressive momentum trader vs. conservative mean reversion)

**Agent State Management**: Each agent maintains its own state (positions, daily P&L, trade count) in `state.json`, which is updated after each trading cycle. This enables agents to track their own performance and respect daily trade limits.

### Risk Management Layers

The system implements multi-layer risk controls:

1. **Agent Level**: Position sizing (2-5% of agent capital), mandatory stop losses, daily trade limits, max concurrent positions
2. **Company Level**: Total exposure limits (80% of capital), daily loss limits, per-agent capital caps, correlation monitoring
3. **Circuit Breakers**: Emergency halt on daily loss threshold, market volatility pause (VIX > 30), system error halt
4. **Manual Override**: Company manager (you) has final authority via CLI commands

**Critical**: Risk limits should NEVER be bypassed. They are hard-coded protections against catastrophic losses.

## Configuration Management

### Environment Variables (.env)
- `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`: Alpaca broker credentials
- `ALPACA_BASE_URL`: Default is paper trading endpoint (`https://paper-api.alpaca.markets`)
- `ANTHROPIC_API_KEY`: Claude API key for agent AI
- `TRADINGVIEW_API_KEY`: TradingView API access (optional)

### Agent Configuration Pattern

When creating new agents, follow this structure in `agents/[agent_name]/context.yaml`:

```yaml
agent:
  id: agent_[asset]_[number]
  name: "[Descriptive Name]"
  asset: [SYMBOL]
  strategy:
    type: [momentum|mean_reversion|breakout]
    timeframe: [5m|15m|1h|4h|daily]
  risk:
    max_position_size: [USD amount]
    stop_loss: [percentage as decimal]
    max_daily_trades: [integer]
  personality:
    risk_tolerance: [conservative|moderate|aggressive]
```

## Code Patterns

### Broker Integration (cli/utils/broker.py)
The `Broker` class wraps the Alpaca API. Always use paper trading initially:
- Instantiate with environment variables
- Use `get_account_info()` for account status
- Use `submit_order()` for trade execution
- All orders should include stop loss parameters

### Agent Decision Flow
1. Agent reads its context.yaml and personality.md
2. Fetches market data via TradingView MCP
3. Analyzes data using Claude AI (via Anthropic API)
4. Generates trade decision with rationale
5. Submits decision to risk manager for validation
6. If approved, executes via Alpaca broker
7. Logs decision and outcome to agent_decisions/ and trades/

### Logging Standards
Use the logger utility (`cli/utils/logger.py`) for all output:
- INFO: Regular operations and trade decisions
- WARNING: Risk limit approaches, unusual conditions
- ERROR: Failed operations, validation failures
- CRITICAL: Circuit breaker triggers, emergency stops

## Development Phases

The system is being built in phases (see trading_company_plan.md for details):

1. **Phase 1 (Current)**: Foundation - Basic CLI, Alpaca integration, first agent
2. **Phase 2**: TradingView MCP integration, agent context system, monitoring
3. **Phase 3**: Circuit breakers, correlation monitoring, pre-trade validation
4. **Phase 4**: Agent learning system, performance-based capital allocation
5. **Phase 5**: 3-6 months paper trading validation
6. **Phase 6**: Live trading with minimal capital

**Important**: Never skip testing phases. Paper trading validation is mandatory before any live trading.

## Risk Management Rules

When working on this codebase, always enforce these non-negotiable rules:

- RULE_001: No agent can exceed 10% of total capital
- RULE_002: Daily loss limit triggers immediate halt
- RULE_003: All trades must have stop losses
- RULE_004: Maximum 3 correlated positions (correlation > 0.7)
- RULE_005: Position size never exceeds 5% of capital
- RULE_006: No more than 80% capital deployed
- RULE_007: All decisions logged and auditable
- RULE_008: Manual override always available

## Common Tasks

### Adding a New Agent
1. Create directory: `agents/agent_[name]/`
2. Create config files: `context.yaml`, `personality.md`, `state.json`, `performance.json`, `learning.json`
3. Define agent strategy, risk parameters, and personality
4. Test with paper trading before activation
5. Update `config/company_config.yaml` allowed_assets if needed

### Implementing a New CLI Command
1. Add command to appropriate file in `cli/commands/`
2. Follow Click decorator pattern with @click.command()
3. Use logger for output instead of print statements
4. Include error handling and validation
5. Update CLI help text with clear descriptions

### Adding Risk Validation
1. Implement check in risk validation layer (company level)
2. Add to pre-trade validation function
3. Log validation failures with reason
4. Return clear error messages to agent
5. Update audit trail in `oversight/audit_log.json`

## Dependencies

Key packages from requirements.txt:
- `anthropic>=0.40.0`: Claude AI SDK
- `alpaca-py>=0.30.0`: Alpaca trading API (note: uses `alpaca_trade_api` in current code)
- `click>=8.1.0`: CLI framework
- `pyyaml>=6.0`: YAML config parsing
- `python-dotenv>=1.0.0`: Environment variable management
- `pandas>=2.0.0`, `numpy>=1.24.0`: Data analysis for backtesting

## References

- Full system design: `trading_company_plan.md`
- Gemini integration notes: `GEMINI.md`
- Project README: `README.md`
