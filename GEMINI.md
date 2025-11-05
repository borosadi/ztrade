# Project Overview

This project aims to build an AI-powered trading company. The system will consist of multiple autonomous AI agents, each specializing in different assets and trading strategies. The company will be managed through a command-line interface (CLI), with a focus on centralized risk management and oversight.

## Key Technologies

*   **AI:** Claude 4 (Sonnet 4.5) via Anthropic API
*   **Broker:** Alpaca (starting with paper trading)
*   **Market Data:** TradingView via Model Context Protocol (MCP)
*   **Programming Language:** Python 3.10+
*   **Interface:** Click CLI

## System Architecture

The system is designed with a multi-layer architecture:

1.  **Company Manager (You):** Manages risk and capital allocation via the CLI.
2.  **Trading Company System:** A central layer for risk management and oversight.
3.  **AI Agents:** Autonomous agents for different assets (e.g., BTC, SPY, EUR).
4.  **External Services:** TradingView for market data and Alpaca for trade execution.

## File Structure

The project will follow a structured directory layout, including separate folders for configuration, agents, shared data, oversight, CLI, logs, and tests, as detailed in `trading_company_plan.md`.

## Development Plan

The project will be developed in phases, as outlined in the `trading_company_plan.md`:

1.  **Phase 1: Foundation:** Set up the environment, build the basic CLI, and integrate the Alpaca API for paper trading.
2.  **Phase 2: Core Features:** Integrate TradingView MCP and Claude, build the agent context system, and add monitoring and logging.
3.  **Phase 3: Risk & Safety:** Implement circuit breakers, correlation monitoring, and pre-trade validation.
4.  **Phase 4: Advanced Features:** Add an agent learning system, performance-based capital allocation, and a risk manager agent.
5.  **Phase 5: Testing:** Extensive paper trading for 3-6 months.
6.  **Phase 6: Live Trading:** Start with minimal capital and gradually scale up.

## Progress Log

**2025-11-03:**

*   Set up the project structure for "Ztrade" based on `trading_company_plan.md`.
*   Created a Python virtual environment and installed dependencies.
*   Created the initial CLI structure using `click` in `cli/main.py`.
*   Added the `agent` command group in `cli/commands/agent.py`.
*   Added placeholder commands to the `agent` group: `list`, `create`, `status`, `ask`, `run`, `pause`, `resume`, `config`, `performance`, and `delete`.

**2025-11-05:**

*   **CI/CD Foundation:** Set up GitHub Actions workflow with testing, linting, and security checks.
*   **Package Management:** Migrated from venv to uv with pyproject.toml configuration.
*   **Core Implementation (Phase 1):**
    *   Implemented Claude AI integration (`cli/utils/llm.py`) with agent decision-making capabilities.
    *   Completed Alpaca broker integration (`cli/utils/broker.py`) with full trading API.
    *   Created configuration loader utility (`cli/utils/config.py`) for managing YAML/JSON files.
    *   Implemented all agent management commands with real functionality:
        *   `agent list` - Lists all agents with status
        *   `agent create` - Creates new agent with interactive prompts
        *   `agent status` - Shows detailed agent information
        *   `agent ask` - Ask agent questions using Claude AI
        *   `agent pause/resume` - Control agent status
        *   `agent config` - Update agent configuration
        *   `agent performance` - View trading performance
        *   `agent delete` - Remove agents
    *   Implemented company-level commands (`cli/commands/company.py`):
        *   `company dashboard` - Overview of all agents and positions
        *   `company positions` - View all open positions
        *   `company status` - System health check
        *   `company risk-check` - Risk assessment across agents
*   **Testing:** Added comprehensive unit tests for CLI and configuration utilities.
*   **Documentation:** Created CLAUDE.md for future AI instances working on this codebase.
*   **GitHub Repository:** Created and pushed to https://github.com/borosadi/ztrade

## Current Status

### ✅ Phase 1: Foundation - COMPLETE

All Phase 1 objectives have been met:
- Git repository initialized with proper .gitignore
- CI/CD pipeline with GitHub Actions (test, lint, security)
- uv package manager configured with pyproject.toml
- Claude AI integration for agent decision-making
- Alpaca broker API fully integrated
- Agent management system (create, list, status, ask, pause/resume, delete)
- Company dashboard and monitoring
- Configuration management utilities
- Unit tests for CLI and configuration
- Documentation (CLAUDE.md for AI context, README.md for users)

### 🎯 Ready for Phase 2: Core Features

**Next Steps:**
1. **TradingView MCP Integration** (`cli/utils/mcp_client.py`)
   - Implement MCP client to fetch market data from TradingView
   - Add market data to agent context for decision-making
   - Create helper functions for chart analysis

2. **Agent Trading Cycle** (implement `agent run` command)
   - Load agent personality and current state
   - Fetch market data via TradingView MCP
   - Call Claude to analyze and make trading decision
   - Validate decision against risk parameters
   - Execute trade via Alpaca if approved
   - Update agent state and performance metrics
   - Log all decisions and trades

3. **Risk Management Layer**
   - Implement pre-trade validation checks
   - Add circuit breaker logic
   - Create correlation monitoring
   - Implement position sizing rules

4. **Monitoring Commands** (`cli/commands/monitor.py`)
   - `monitor trades` - Recent trade history
   - `monitor logs --follow` - Real-time log streaming
   - `monitor alerts` - Active alerts and warnings
   - `monitor decisions <agent_id>` - Agent decision logs

5. **Risk Commands** (`cli/commands/risk.py`)
   - `risk set-limit` - Update risk parameters
   - `risk correlations` - Check asset correlations
   - `risk simulate` - Run risk scenarios
   - `risk history` - Historical risk metrics

### 🔧 Environment Setup Notes

**Required Environment Variables:**
- `ALPACA_API_KEY` - Alpaca API key (currently set)
- `ALPACA_SECRET_KEY` - Alpaca secret key (currently set)
- `ANTHROPIC_API_KEY` - Currently set to placeholder "YOUR_API_KEY" - needs real key
- `ALPACA_BASE_URL` - Defaults to paper trading endpoint

**To Test Core Functionality:**
```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Run the CLI
uv run ztrade hello
uv run ztrade company dashboard
uv run ztrade agent list -v

# Create a test agent
uv run ztrade agent create test_agent

# Ask an agent a question (requires API key)
uv run ztrade agent ask agent_btc "What's your strategy?"
```

### 📂 Key Files for Phase 2

**To Implement:**
- `cli/utils/mcp_client.py` - TradingView MCP integration
- `cli/commands/monitor.py` - Monitoring commands
- `cli/commands/risk.py` - Risk management commands
- Trading cycle logic in `agent run` command

**Existing Agents:**
- `agents/agent_btc/` - Bitcoin momentum trader
- `agents/agent_spy/` - SPY mean reversion
- `agents/agent_forex_eur/` - EUR/USD scalper
- `agents/agent_tsla/` - TSLA breakout trader

These are placeholder agents with empty/minimal config files - they were created as part of the initial structure but need to be properly configured or recreated using the `agent create` command.

### 🐛 Known Issues / To-Do

- [ ] Update `.env` with real ANTHROPIC_API_KEY before testing agent ask command
- [ ] Existing placeholder agents need proper configuration
- [ ] TradingView MCP server integration not started yet
- [ ] Agent trading cycle (`agent run`) returns placeholder message
- [ ] Monitoring and risk commands are empty files
- [ ] Need to configure git user name/email globally
- [ ] Consider adding more comprehensive error handling for API failures

### 📊 Testing Status

- ✅ CLI tests passing
- ✅ Configuration tests passing
- ⏸️ Integration tests with broker (requires valid API keys)
- ⏸️ Integration tests with Claude (requires valid API key)
- ⏸️ End-to-end trading cycle tests (Phase 2)

### 📝 Technical Debt

- Consider adding retry logic for API calls
- Add rate limiting for Alpaca API calls
- Implement proper logging to files (currently just console)
- Add input validation for agent creation parameters
- Consider adding agent validation on startup
- May need to handle timezone conversions for trading hours

---

**2025-11-05 (Evening Session):**

*   **✅ Phase 2: Core Trading Features - COMPLETE**
    *   Implemented risk validation layer (`cli/utils/risk.py`) with 9 comprehensive safety rules
    *   Created trade executor (`cli/utils/trade_executor.py`) with logging and state management
    *   Completed full agent trading cycle in `agent run` command with dry-run mode
    *   Implemented monitoring commands (`cli/commands/monitor.py`):
        *   `monitor trades` - View recent trade history
        *   `monitor decisions` - View agent decision logs
        *   `monitor alerts` - Active warnings and alerts
        *   `monitor logs` - System log viewer
        *   `monitor performance` - Detailed agent metrics
    *   Implemented risk management commands (`cli/commands/risk.py`):
        *   `risk status` - Overall risk status across agents
        *   `risk set-limit` - Update agent risk parameters
        *   `risk correlations` - Asset correlation monitoring
        *   `risk simulate` - Run risk scenarios (market_crash, volatility_spike, max_drawdown)
        *   `risk history` - Historical risk metrics (placeholder)
    *   Updated CLI (`cli/main.py`) to register monitor and risk command groups
*   **Dependency Fixes:**
    *   Changed from `alpaca-py` to `alpaca-trade-api` (fixes import errors)
    *   Removed `websockets` dependency conflict
    *   Added hatchling build configuration to `pyproject.toml`
    *   Generated and committed `uv.lock` for reproducible builds
*   **Testing:**
    *   Verified all CLI commands work: `uv run ztrade --version`, `--help`
    *   All command groups (agent, company, monitor, risk) properly registered
*   **GitHub:**
    *   Force-pushed to replace corrupted commits from earlier session
    *   Repository now clean with proper file encoding
    *   Commits: 00edd76 (Phase 2 implementation), ad6ef37 (uv.lock)

### ✅ Phase 2: Core Trading Features - COMPLETE

All Phase 2 objectives have been met:
- ✅ Risk validation layer with 9 safety rules
- ✅ Trade executor with logging and state management
- ✅ Full agent trading cycle (fetch data, AI decision, risk validation, execution)
- ✅ Monitoring commands (trades, decisions, alerts, logs, performance)
- ✅ Risk management commands (status, set-limit, correlations, simulate)
- ✅ Dry-run mode for safe testing
- ✅ Decision and trade logging to JSONL files
- ✅ CLI properly structured with all command groups

### 🎯 Ready for Phase 3: Advanced Risk & Safety

**Next Steps:**
1. **TradingView MCP Integration** (`cli/utils/mcp_client.py`)
   - Implement MCP client to fetch real market data
   - Add technical indicators and chart analysis
   - Integrate into agent trading cycle

2. **Circuit Breakers**
   - Implement automatic trading halt on severe losses
   - Add market volatility detection (VIX monitoring)
   - Create emergency stop mechanisms

3. **Enhanced Risk Monitoring**
   - Real-time correlation tracking
   - Position concentration monitoring
   - Daily loss circuit breakers

4. **Agent Learning System** (Phase 4 preview)
   - Track decision outcomes
   - Pattern recognition
   - Performance-based adjustments

### 📝 Updated Technical Debt / To-Do

- [x] Agent trading cycle implementation
- [x] Monitoring commands
- [x] Risk management commands
- [x] Dependency conflicts resolved
- [ ] Update `.env` with real ANTHROPIC_API_KEY before testing
- [ ] TradingView MCP server integration
- [ ] End-to-end testing with real market data
- [ ] Configure git user name/email globally
- [ ] Add retry logic for API calls
- [ ] Implement file-based logging (currently logs directory structure exists)
- [ ] Create integration tests for trading cycle

---

**Phase 2 Complete! Ready to start Phase 3 (Advanced Risk & Safety) or Phase 4 (Agent Learning).**
