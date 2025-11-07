# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ztrade is an AI-powered trading company system where multiple autonomous AI agents trade different assets independently. Each agent specializes in a specific asset (BTC, SPY, EUR, TSLA) with its own strategy, risk profile, and personality. The system is managed through a CLI interface built with Python Click.

**Key Technologies:**
- **AI**: Claude Code subagents (no API key required) for agent decision-making
- **Broker**: Alpaca API (paper trading via alpaca-py)
- **Market Data**: Alpaca API (real-time) + Yahoo Finance (fallback via yfinance)
- **CLI**: Python Click framework
- **Language**: Python 3.10+

## Current System Status (Updated 2025-11-07 - Multi-Source Sentiment)

### Active Trading Agents (3)

1. **agent_spy** - SPY Momentum Trader
   - Asset: SPY (S&P 500 ETF)
   - Strategy: Momentum (15-minute timeframe)
   - Risk: Moderate (2% stop loss, 60% min confidence)
   - Capital: $10,000 allocated
   - Status: ✅ Tested with real market data

2. **agent_tsla** - Tesla Momentum Trader
   - Asset: TSLA (Tesla)
   - Strategy: Momentum (15-minute timeframe)
   - Risk: Aggressive (3% stop loss, 65% min confidence)
   - Capital: $10,000 allocated
   - Status: ✅ Tested with real market data

3. **agent_aapl** - Apple Mean Reversion Trader
   - Asset: AAPL (Apple)
   - Strategy: Mean Reversion (1-hour timeframe)
   - Risk: Conservative (1.5% stop loss, 70% min confidence)
   - Capital: $10,000 allocated
   - Status: Configured, ready to test

### Subagent Mode Implementation

The system uses **Claude Code subagents** for trading decisions via file-based communication:

- **No API keys required**: Operates entirely through terminal without external costs
- **File-based communication**: Request/response files in `oversight/subagent_requests/` and `oversight/subagent_responses/`
- **60-second timeout**: Agents wait 60 seconds for trading decisions
- **Complete workflow**: Market data → Analysis → Subagent decision → Risk validation → Execution → Logging

**Running with subagent mode:**
```bash
# Dry-run (no trades executed)
uv run ztrade agent run agent_spy --subagent --dry-run

# Paper trading (simulated trades)
uv run ztrade agent run agent_spy --subagent
```

### Market Data Integration

**Primary Source**: Alpaca API
- Real-time quotes during market hours
- Historical bars for technical analysis (15min, 1hour, 1day timeframes)
- Successfully fetching: SPY ($677+), TSLA ($449-452), AAPL ($271)
- Live data confirmed working ✅

**Multi-Source Sentiment Analysis**: Weighted aggregation from 3 sources
- **News** (40% weight): Alpaca News API (Benzinga) with VADER sentiment on full article content
- **Reddit** (25% weight): r/wallstreetbets, r/stocks, r/investing via PRAW API (optional, requires credentials)
- **SEC Filings** (25% weight): EDGAR API for 10-K, 10-Q, 8-K filings (currently limited by SEC API access)
- Returns: aggregated score (-1 to +1), confidence (0-100%), source breakdown, agreement level
- Gracefully handles missing sources (falls back to available sources)
- Integrated into trading decision context via `cli/utils/sentiment_aggregator.py`

**Fallback Source**: Yahoo Finance (yfinance 0.2.40)
- Currently experiencing API issues for historical data
- Used as fallback when Alpaca fails

**Technical Indicators**:
- RSI, SMA, moving averages
- Volume analysis
- Trend detection
- Support/resistance levels

### System Capabilities

✅ **Working:**
- Real-time market data from Alpaca (quotes + historical bars)
- **Multi-source sentiment analysis** (News + Reddit + SEC with weighted aggregation)
- News sentiment from Alpaca News API (Benzinga) with full article content analysis
- Reddit sentiment from r/wallstreetbets, r/stocks (requires credentials, graceful fallback)
- SEC filings analysis from EDGAR API (10-K, 10-Q, 8-K material events)
- Technical analysis with traditional indicators (RSI, SMA, trend, volume)
- Hybrid decision-making: Traditional TA + Multi-source sentiment + AI synthesis
- Subagent decision-making via Claude Code
- Risk validation (confidence thresholds)
- Paper trading execution
- Trade logging and audit trail
- Agent personality and strategy loading

⏳ **Pending:**
- Continuous trading loops (manual cycles only)
- Multi-agent simultaneous trading
- Performance tracking and learning system
- Advanced sentiment models (FinBERT upgrade)
- Full SEC EDGAR API access (currently limited)

## Architectural Decisions

### ADR-001: Asset-Based vs Task-Based Agent Architecture (2025-11-07)

**Status**: Decided - Keeping asset-based architecture with hybrid optimization

**Context**:
After reviewing a comprehensive ChatGPT analysis of the system (comparing AI-powered vs traditional trading approaches), a proposal was made to reorganize agents by task (sentiment analysis, technical analysis, execution) instead of by asset (SPY, TSLA, AAPL).

**Proposal Evaluated**:
```
Task-Based Architecture:
- Agent #1: Sentiment analysis from financial news
- Agent #2: Technical analysis using traditional methods
- Agent #3: Execution/synthesis agent
```

**Analysis & Decision**:

The task-based architecture was **rejected** for the following reasons:

1. **Increases Coordination Complexity**:
   - Current: Zero inter-agent coordination, fully autonomous agents
   - Proposed: Sequential pipeline (Sentiment → Technical → Execution)
   - Creates single points of failure and complex state management
   - **ChatGPT specifically warned**: "The complexity of orchestration and communication is a major challenge in agentic trading systems"

2. **Worse Latency, Not Better**:
   - Current: ~10 seconds (Data fetch + LLM decision)
   - Proposed: ~15-20 seconds (Sentiment LLM + Technical + Execution LLM)
   - Serial chains are slower than parallel operations
   - Doesn't address the core concern about AI system speed

3. **Loses Agent Specialization**:
   - agent_aapl: Conservative, mean reversion, 1-hour timeframe
   - agent_tsla: Aggressive, momentum, 15-minute timeframe
   - Task-based dilutes personality and strategy specialization (a core strength)

4. **State Management Nightmare**:
   - Current: Clean per-agent ownership of positions and state
   - Proposed: Shared state across multiple agents, unclear ownership
   - Risk limits become ambiguous (who owns which positions?)

5. **Doesn't Address Real Concerns from ChatGPT Analysis**:
   - Latency: Task-based makes it worse (more sequential steps)
   - Complexity: Task-based makes it worse (coordination overhead)
   - Explainability: Only partially helps (TA transparent, but fusion still opaque)
   - Cost: Marginal savings (fewer LLM calls but not significant)

**Adopted Solution: Hybrid Optimization Within Asset-Based Architecture**

Instead of reorganizing, we implemented **internal optimizations** to each agent:

1. **Created `cli/utils/technical_analyzer.py`**:
   - Fast, deterministic TA calculations (RSI, SMA, trend, volume, support/resistance)
   - Returns structured signals with confidence scores and reasoning
   - Computation time: <10ms (vs seconds for LLM)
   - Fully transparent and auditable

2. **Updated agent execution flow** (cli/commands/agent.py):
   - Market data fetch → **Traditional TA signals** → LLM synthesis
   - LLM receives pre-digested signals instead of raw numbers
   - Smaller context, faster decisions, clearer reasoning

3. **Added performance metrics**:
   - Timing for: data fetch, TA computation, LLM decision
   - Logged and displayed for every trade cycle
   - Enables data-driven optimization

**Hybrid Pattern (Recommended Approach)**:
```python
# Traditional analysis (fast, deterministic)
technical_signals = {
    "rsi_oversold": rsi < 30,
    "macd_bullish": macd > signal,
    "above_sma": price > sma_20
}

# LLM only for synthesis and final decision
decision = llm_call({
    "technical_signals": technical_signals,  # Pre-computed
    "agent_personality": personality,
    "current_positions": positions
})
```

**Benefits of This Approach**:
- ✅ Speed: TA is instant (<10ms)
- ✅ Transparency: TA is deterministic and logged
- ✅ Lower cost: Smaller LLM prompts
- ✅ Still uses LLM for complex synthesis
- ✅ **No architectural changes needed**
- ✅ Preserves agent autonomy and specialization

**Focus Strategy: Single-Agent Mastery**

Additionally, decided to **focus exclusively on agent_spy** before scaling:

1. **Rationale**: Running 3 agents simultaneously is premature
2. **Approach**: Perfect one agent (SPY) with proven performance before cloning
3. **Benefits**:
   - Better debugging and iteration
   - Clear performance attribution
   - Simpler mental model
   - SPY is liquid, well-understood, diversified (ETF)

**References**:
- ChatGPT analysis emphasized: "Day trading thrives on speed, simplicity, and predictability"
- This is an **AI research platform** exploring autonomous trading, not an HFT execution system
- Lean into research/learning aspects, don't try to compete on speed with traditional HFT

**Implementation Status**: ✅ Complete (2025-11-07)
- technical_analyzer.py created
- agent.py updated with hybrid approach
- Performance metrics added
- Ready to test with agent_spy

### ADR-002: Multi-Source Sentiment Analysis Integration (2025-11-07)

**Status**: Implemented

**Decision**: Integrate multi-source sentiment analysis using weighted aggregation from News, Reddit, and SEC filings to provide comprehensive market sentiment for trading decisions.

**Rationale**:
- Single-source sentiment (news only) provides limited perspective
- Retail sentiment (Reddit) offers early signals and contrarian indicators
- Official filings (SEC) provide fundamental event detection
- Weighted aggregation reduces bias from any single source
- Graceful degradation when sources are unavailable

**Implementation Details**:

**Architecture**:
```
┌─────────────────────────────────────────────────┐
│         Multi-Source Sentiment Engine           │
└─────────────────────────────────────────────────┘
                      │
          ┌───────────┼───────────┬───────────┐
          │           │           │           │
     ┌────▼───┐  ┌───▼────┐  ┌──▼─────┐  ┌──▼─────┐
     │ News   │  │Reddit  │  │ SEC    │  │StockTwits│
     │(Alpaca)│  │(PRAW)  │  │(EDGAR) │  │(Future) │
     └────┬───┘  └───┬────┘  └──┬─────┘  └──┬─────┘
          │          │          │           │
     Weight: 40%  Weight: 25% Weight: 25% Weight: 10%
          │          │          │           │
          └──────────┴──────────┴───────────┘
                      │
            ┌─────────▼──────────┐
            │  Aggregate Score   │
            │  Confidence Level  │
            │  Source Breakdown  │
            └────────────────────┘
```

**Components Created**:

1. **`cli/utils/news_analyzer.py`** (289 lines)
   - Fetches news via Alpaca News API (Benzinga)
   - VADER sentiment on full article content (up to 5000 chars)
   - Parameters: `include_content=True`, `exclude_contentless=True`, 25 articles max
   - Returns: sentiment score, confidence, article count, top headlines
   - API call: line 218 (`news_client.get_news(request)`)

2. **`cli/utils/reddit_analyzer.py`** (285 lines) - NEW
   - Scrapes r/wallstreetbets, r/stocks, r/investing via PRAW
   - Analyzes posts + top 10 comments per post
   - VADER sentiment on combined text
   - Returns: mention count, trending score (mentions/hour), top posts
   - Requires credentials: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`
   - Gracefully falls back if credentials missing

3. **`cli/utils/sec_analyzer.py`** (316 lines) - NEW
   - Fetches SEC EDGAR filings (10-K, 10-Q, 8-K)
   - CIK lookup via `company_tickers.json`
   - Material event detection (8-K filings)
   - Keyword-based sentiment (positive: "beat", "growth"; negative: "miss", "decline")
   - Returns: filing count, material events, sentiment by filing type
   - Currently limited by SEC API access policies (403 errors)

4. **`cli/utils/sentiment_aggregator.py`** (272 lines) - NEW
   - Orchestrates all sentiment sources
   - Weighted aggregation (configurable weights)
   - Agreement level calculation (how much sources agree)
   - Source breakdown in output
   - Graceful handling of missing sources

**Weighting Strategy**:
- **News (40%)**: Most reliable, professional journalism, verified sources
- **Reddit (25%)**: Retail sentiment, early signals, high volume discussions
- **SEC (25%)**: Official filings, fundamental events, regulatory data
- **StockTwits (10%)**: Reserved for future implementation

**Integration Points**:
- `cli/utils/market_data.py:90-108`: Calls sentiment aggregator instead of news analyzer
- `cli/commands/agent.py:367-409`: Displays source breakdown in trading context
- Changed key from `news_sentiment` to `sentiment` in market context

**Example Output**:
```
Multi-Source Sentiment Analysis:
- Overall Sentiment: POSITIVE
- Sentiment Score: 0.95 (range: -1 to +1)
- Confidence: 100%
- Sources Used: news, reddit
- Agreement Level: 100%

News (Alpaca/Benzinga):
  Sentiment: POSITIVE (0.95)
  Articles: 19
  Top Headlines:
    1. Tesla Stock Surges on Strong Earnings Beat...
    2. Analysts Upgrade TSLA Price Target to $500...

Reddit (r/wallstreetbets, r/stocks):
  Sentiment: POSITIVE (0.82)
  Mentions: 147 (23 posts, 124 comments)
  Trending: 6.1 mentions/hour
  Top Post: "TSLA earnings call was fire 🚀🚀🚀" (1247 upvotes)

SEC Filings (EDGAR):
  Sentiment: POSITIVE (0.30)
  Recent Filings: 3 in last 30 days
  Material Events (8-K): 1
    - 2025-10-25: Material Event (sentiment: 0.40)
```

**Test Results** (2025-11-07):
```bash
TSLA Multi-Source Sentiment:
- Overall: POSITIVE
- Score: 0.947
- Confidence: 100%
- Sources: news (19 articles)
- Agreement: 100%
```

**Configuration**:

To enable Reddit sentiment, add to `.env`:
```bash
# Get credentials at: https://www.reddit.com/prefs/apps
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT="Ztrade:v1.0 (by /u/your_username)"
```

**Dependencies Added**:
- `alpaca-py>=0.9.0`: Alpaca News API client
- `vaderSentiment>=3.3.2`: Sentiment analysis
- `praw>=7.7.1`: Reddit API wrapper (Python Reddit API Wrapper)

**Known Limitations**:
- SEC EDGAR API has strict access policies (currently returning 403 errors)
- Reddit requires free API credentials (system gracefully falls back)
- VADER is general-purpose (FinBERT would be more finance-specific)

**Future Enhancements**:
- FinBERT model for financial-specific sentiment (more accurate than VADER)
- StockTwits integration (finance-focused social media)
- Sentiment trend analysis (tracking changes over time)
- Entity extraction (identifying mentioned companies, Fed officials)
- Source credibility weighting (weight by historical accuracy)
- Cross-asset correlation detection (SPY sentiment affects TSLA, etc.)

## Development Commands

### Environment Setup
```bash
# Using uv (recommended)
uv sync

# Or traditional setup
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Verify environment setup
uv run ztrade hello
```

### Running the CLI
```bash
# Main CLI entry point
uv run ztrade [COMMAND]

# Agent commands
uv run ztrade agent list
uv run ztrade agent status AGENT_ID
uv run ztrade agent create AGENT_ID

# Trading modes
uv run ztrade agent run AGENT_ID --subagent --dry-run   # Subagent mode (dry-run, recommended)
uv run ztrade agent run AGENT_ID --subagent             # Subagent mode (paper trading)
uv run ztrade agent run AGENT_ID --manual --dry-run     # Manual mode (no API key needed)
uv run ztrade agent run AGENT_ID --manual               # Manual mode (paper trading)
uv run ztrade agent run AGENT_ID                        # Automated (requires ANTHROPIC_API_KEY)

# Company commands
uv run ztrade company dashboard
uv run ztrade company positions
uv run ztrade company risk-check

# Risk management commands
uv run ztrade risk status
uv run ztrade risk correlations
uv run ztrade risk simulate market_crash

# Monitoring commands
uv run ztrade monitor decisions AGENT_ID
uv run ztrade monitor trades AGENT_ID
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
  - `commands/`: Command groups (agent.py, company.py, monitor.py, risk.py, subagent.py)
  - `utils/`: Shared utilities
    - `broker.py`: Alpaca API integration for trading and market data
    - `market_data.py`: Market data provider with technical analysis
    - `sentiment_aggregator.py`: Multi-source sentiment aggregation engine (NEW)
    - `news_analyzer.py`: News fetching and sentiment analysis via Alpaca
    - `reddit_analyzer.py`: Reddit sentiment via PRAW (NEW)
    - `sec_analyzer.py`: SEC EDGAR filings analysis (NEW)
    - `technical_analyzer.py`: Traditional technical indicators (RSI, SMA, etc.)
    - `subagent.py`: Claude Code subagent communication
    - `mcp_client.py`: MCP client for data providers
    - `logger.py`: Logging utilities

- **`config/`**: System-wide configuration
  - `company_config.yaml`: Capital allocation and trading parameters
  - `risk_limits.yaml`: Company-wide risk management rules
  - `broker_config.yaml`: Alpaca API credentials and settings

- **`shared/`**: Cross-agent resources
  - `market_data/`: Shared market intelligence (market_intel.yaml)
  - `research/`: Collective research notes
  - `correlations.json`: Cross-asset correlation tracking

- **`oversight/`**: Risk management and monitoring
  - `subagent_requests/`: Decision requests from agents (60s timeout)
  - `subagent_responses/`: Trading decisions from Claude Code subagents
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

### Agent Decision Flow (Subagent Mode)
1. Agent reads its context.yaml and personality.md
2. Fetches market data via Alpaca API (real-time quotes + historical bars)
3. Fetches news sentiment via Alpaca News API (last 24 hours, full content)
4. Runs technical analysis (RSI, SMA, trend, volume, support/resistance)
5. Creates decision request file in `oversight/subagent_requests/` with:
   - Market data (current price, technical indicators)
   - News sentiment (score, confidence, headlines)
   - Agent state (positions, daily P&L, trade count)
6. Waits for Claude Code subagent response (60-second timeout)
7. Claude Code analyzes context and provides trading decision
8. Subagent writes response to `oversight/subagent_responses/`
9. Agent validates decision against risk rules (confidence threshold, position size)
10. If approved, executes trade via Alpaca broker (or simulates in dry-run mode)
11. Logs decision and outcome to `logs/agent_decisions/` and `logs/trades/`

**Subagent Communication Format:**
- Request: `{request_id, agent_id, timestamp, context, status}`
- Response: `{request_id, timestamp, decision: {action, quantity, rationale, confidence, stop_loss}}`

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

### Using Multi-Source Sentiment Analysis
The system automatically fetches and analyzes sentiment from multiple sources for each trading decision.

**How it works:**
1. `market_data.py` calls `sentiment_aggregator.get_aggregated_sentiment(symbol)`
2. News: Alpaca News API fetches recent articles (last 24 hours) with VADER sentiment
3. Reddit: PRAW scrapes r/wallstreetbets, r/stocks, r/investing (if credentials available)
4. SEC: EDGAR API fetches recent filings (10-K, 10-Q, 8-K) with keyword-based sentiment
5. All sources aggregated with weighted scoring (news=40%, reddit=25%, sec=25%)
6. Sentiment included in trading decision context with source breakdown

**Accessing aggregated sentiment in code:**
```python
from cli.utils.sentiment_aggregator import get_sentiment_aggregator

aggregator = get_sentiment_aggregator()
sentiment = aggregator.get_aggregated_sentiment(
    "TSLA",
    news_lookback_hours=24,
    reddit_lookback_hours=24,
    sec_lookback_days=30
)

# Returns:
# {
#   "overall_sentiment": "positive" | "negative" | "neutral",
#   "sentiment_score": -1.0 to 1.0,  # Weighted aggregate
#   "confidence": 0.0 to 1.0,
#   "sources_used": ["news", "reddit", "sec"],
#   "agreement_level": 0.0 to 1.0,  # How much sources agree
#   "source_breakdown": {
#       "news": {...},     # Individual news sentiment
#       "reddit": {...},   # Individual Reddit sentiment
#       "sec": {...}       # Individual SEC sentiment
#   },
#   "weights_applied": {"news": 0.4, "reddit": 0.25, "sec": 0.25}
# }
```

**Accessing individual sources:**
```python
# News only
from cli.utils.news_analyzer import get_news_analyzer
news = get_news_analyzer()
news_sentiment = news.get_news_sentiment("SPY", lookback_hours=24, max_articles=25)

# Reddit only (requires credentials)
from cli.utils.reddit_analyzer import get_reddit_analyzer
reddit = get_reddit_analyzer()
reddit_sentiment = reddit.get_reddit_sentiment("TSLA", lookback_hours=24, max_posts=50)

# SEC only
from cli.utils.sec_analyzer import get_sec_analyzer
sec = get_sec_analyzer()
sec_sentiment = sec.get_sec_sentiment("AAPL", lookback_days=30, max_filings=10)
```

**Configuration:**
- Aggregated sentiment works automatically with available sources
- News: Works out-of-the-box (Alpaca API credentials already configured)
- Reddit: Requires free credentials in `.env` (see ADR-002 for setup)
- SEC: Implemented but currently limited by SEC API access policies
- System gracefully falls back if sources unavailable

## Dependencies

Key packages from requirements.txt:
- `anthropic>=0.40.0`: Claude AI SDK (optional, only for automated mode)
- `alpaca-trade-api>=3.0.0`: Alpaca trading API for paper trading
- `alpaca-py>=0.9.0`: Alpaca News API client (for news sentiment analysis)
- `vaderSentiment>=3.3.2`: VADER sentiment analysis for financial text
- `praw>=7.7.1`: Python Reddit API Wrapper (for Reddit sentiment analysis)
- `click>=8.1.0`: CLI framework
- `pyyaml>=6.0`: YAML config parsing
- `python-dotenv>=1.0.0`: Environment variable management
- `pandas>=2.0.0`, `numpy>=1.24.0`: Data analysis for backtesting
- `yfinance==0.2.40`: Yahoo Finance data (fallback for historical data)
- `requests>=2.31.0`: HTTP requests (used by SEC analyzer)

**Note**: The `mcp` package was removed due to websockets version conflicts. Market data now fetched directly via Alpaca API (primary) and yfinance (fallback).

**Multi-Source Sentiment**: News sentiment works out-of-the-box. Reddit sentiment requires free API credentials (see ADR-002). SEC sentiment is implemented but currently limited by SEC API access policies.

## References

- Full system design: `trading_company_plan.md`
- Gemini integration notes: `GEMINI.md`
- Project README: `README.md`
- to memorize
- lets save todays work to the context
- to memorize