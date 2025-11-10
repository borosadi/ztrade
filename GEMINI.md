# Project Overview

This project aims to build an AI-powered trading company called **Ztrade**. The system consists of multiple autonomous AI agents that trade different assets, each with its own unique strategy and personality. The entire operation is managed through a command-line interface (CLI) and is designed for robust, centralized risk management.

## Key Technologies

*   **AI**: Claude Code subagents (file-based, no API key required) for trading decisions.
*   **Broker**: Alpaca API (paper trading via `alpaca-py`).
*   **Market Data**: Alpaca API (real-time) with Yahoo Finance as a fallback.
*   **Orchestration**: Celery for distributed task queuing, Redis as the message broker, and Flower for web-based monitoring.
*   **Database**: PostgreSQL for storing historical market data and backtesting results.
*   **Interface**: Python Click for the CLI, and Streamlit for a real-time web dashboard.
*   **Containerization**: Docker and Docker Compose for full environment containerization.
*   **Language**: Python 3.10+.

## System Architecture

The system is built on a multi-layer, containerized architecture:

1.  **Company Manager (You):** Manages risk, allocates capital, and oversees agents via the CLI.
2.  **Orchestration Layer:** Celery and Redis manage autonomous trading loops, data collection, and other background tasks.
3.  **AI Agents:** Autonomous agents (e.g., `agent_spy`, `agent_tsla`) execute trades based on a hybrid model of technical analysis, sentiment analysis, and AI-driven synthesis.
4.  **Data & Services:** Includes a PostgreSQL database for historical data, a Streamlit dashboard for real-time monitoring, and external APIs like Alpaca for trading and market data.

## Current Status (2025-11-10)

The project has advanced significantly, with a robust set of features already implemented and tested.

### ✅ Completed Features:

*   **AI & Decision Making:**
    *   Hybrid decision-making combining technical analysis, multi-source sentiment (News, Reddit, SEC), and AI synthesis.
    *   File-based Claude Code subagent integration for final trade decisions (60s timeout).
*   **Trading & Brokerage:**
    *   Full integration with Alpaca for paper trading.
    *   Continuous, autonomous trading loops managed by Celery.
*   **Data & Backtesting:**
    *   **Historical Data Collection:** A service using Celery Beat to automatically collect and store market data in a PostgreSQL database.
    *   **Event-Driven Backtester:** A complete backtesting framework to simulate strategies against historical data and compare results.
*   **Monitoring & Orchestration:**
    *   **Celery Orchestration:** The entire system is orchestrated with Celery, with a Flower UI for monitoring workers and tasks.
    *   **Real-time Dashboard:** A Streamlit web dashboard (`dashboard.py`) provides live insights into agent performance and market conditions.
    *   **Containerization:** The entire application is containerized into 7 services using Docker Compose, allowing for consistent development and production environments.
*   **Risk Management:**
    *   Multi-layer risk validation and system-wide circuit breakers.

### ⏳ Pending Features:

*   Simultaneous trading of multiple agents.
*   Integration of advanced sentiment models (e.g., FinBERT).
*   Collection of real market data during live market hours to populate the database.

## Quick Start

### 1. Running with Docker (Recommended)

The entire Ztrade environment is containerized.

```bash
# Build and start all 7 services in detached mode
./docker-control.sh start

# Monitor logs for a specific service (e.g., the trading app)
./docker-control.sh logs trading

# Stop all services
./docker-control.sh stop
```
*   **Dashboard:** [http://localhost:8501](http://localhost:8501)
*   **Celery Monitor (Flower):** [http://localhost:5555](http://localhost:5555)

### 2. Running Locally (Manual)

```bash
# Start the real-time web dashboard
./run_dashboard.sh

# Run an agent in subagent mode (dry-run)
uv run ztrade agent run agent_spy --subagent --dry-run

# Start a continuous trading loop for an agent
uv run ztrade loop start agent_spy

# Run a backtest for an agent
uv run ztrade backtest run agent_spy --start 2025-01-01 --end 2025-10-31
```
**Full command reference:** `docs/guides/development-commands.md`

## Development Plan & Progress

The project has moved rapidly through its initial phases and is now focused on data collection, testing, and validation.

*   **✅ Phase 1: Foundation** - Complete.
*   **✅ Phase 2: Core Features** - Complete.
*   **✅ Phase 3: Advanced Risk & Safety** - Complete.
*   **✅ Phase 4: Data Collection & Backtesting** - Complete.
*   **🎯 Current Phase: Phase 5 (Testing & Validation)**
    *   **Goal:** Run agents in paper trading mode to collect real-world performance data. Backtest strategies against the newly collected historical data.
    *   **Next Steps:**
        1.  Enable data collection services during market hours.
        2.  Run `agent_spy`, `agent_tsla`, and `agent_aapl` in continuous paper trading mode.
        3.  Analyze performance and refine strategies based on results.
        4.  Conduct extensive backtesting using the new historical data.
*   **Future Phase: Phase 6 (Live Trading)**
    *   Begin with minimal capital and scale up gradually based on proven performance.

## Documentation

*   **Architectural Decisions (ADRs):** `docs/adr/`
*   **Development Guides:** `docs/guides/`
*   **Session Logs:** `docs/sessions/`
*   **Claude-Specific Guidance:** `CLAUDE.md`