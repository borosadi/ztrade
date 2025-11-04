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
