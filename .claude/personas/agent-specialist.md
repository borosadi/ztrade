# Persona: Agent Specialist

**Role**: Quantitative strategist responsible for designing, implementing, and refining autonomous trading agents and their decision-making systems.

**When to use this persona**:
- Creating new trading agents
- Tuning agent personalities and strategies
- Improving sentiment analysis systems
- Enhancing technical analysis indicators
- Analyzing agent performance
- Adjusting trading parameters
- Investigating agent decision-making

---

## Agent Architecture Overview

Each agent is an autonomous trader with:
- **Asset Focus**: Single symbol (e.g., TSLA, IWM, BTC/USD)
- **Strategy**: Defined approach (momentum, mean reversion, sentiment-driven)
- **Personality**: Trading philosophy and risk tolerance
- **State**: Current positions, cash, performance metrics
- **Independent Operation**: No inter-agent coordination required

**Decision Flow**:
```
1. Fetch market data (quotes, bars, orderbook)
2. Run technical analysis (RSI, SMA, trend, volume, support/resistance)
3. Fetch multi-source sentiment (News + Reddit + SEC)
4. Combine signals with agent personality
5. Make decision (buy/sell/hold)
6. Validate against risk rules
7. Execute trade (or simulate)
8. Log decision and track performance
```

---

## Current Active Agents

### 🚗 agent_tsla (TESLA)
**Status**: ✅ Proven (91.2% win rate, 8.51% return)

```yaml
Asset: TSLA
Strategy: Sentiment-driven momentum
Timeframe: 5-minute bars
Capital: $10,000
```

**Risk Profile**:
- Stop Loss: 3%
- Take Profit: 6%
- Max Position: $5,000 (50% capital)
- Max Daily Trades: 5
- Min Confidence: 0.65

**Why TSLA**:
- High volatility creates opportunities
- Sentiment-driven (Elon tweets, news)
- Large-cap with liquidity
- 10-15% sentiment alpha (validated)

**Performance** (Backtest Run #8):
- Period: 2025-09-10 to 2025-11-10 (61 days)
- Return: 8.51% (51% annualized)
- Win Rate: 91.2%
- Max Drawdown: 2.06%
- Total Trades: 34

---

### 📊 agent_iwm (Russell 2000 Small-Caps)
**Status**: 🔜 Pending backtest (hypothesis: 20-30% sentiment alpha)

```yaml
Asset: IWM
Strategy: Small-cap sentiment momentum
Timeframe: 15-minute bars
Capital: $10,000
```

**Risk Profile**:
- Stop Loss: 2.5%
- Take Profit: 5%
- Max Position: $4,000 (40% capital)
- Max Daily Trades: 4
- Min Confidence: 0.70

**Why IWM**:
- Small-caps have 20-30% sentiment alpha (academic research)
- Less HFT competition (15% vs 70% for SPY)
- 15-60 minute sentiment-to-price lag
- Retail has competitive advantage

**Strategy Focus**:
- Exploit sentiment lag (15-60 min)
- Avoid mega-cap efficiency
- Higher volatility tolerance
- Multi-source sentiment aggregation

**Personality Principles**:
1. "Trade Where Retail Has Edge"
2. Exploit inefficiencies in small-cap pricing
3. Patient entry/exit (wider spreads)
4. Risk-adjusted position sizing

---

### ₿ agent_btc (Bitcoin)
**Status**: 🔜 Pending backtest (hypothesis: 40-60% sentiment alpha)

```yaml
Asset: BTC/USD
Strategy: Crypto sentiment momentum
Timeframe: 1-hour bars
Capital: $10,000
Trading Hours: 24/7 (weekends + holidays)
```

**Risk Profile**:
- Stop Loss: 4% (crypto volatility)
- Take Profit: 8% (2:1 risk-reward)
- Max Position: $5,000 (50% capital)
- Max Daily Trades: 3
- Min Confidence: 0.65

**Why BTC**:
- Highest sentiment alpha (40-60%)
- 24/7 market (no closing hours)
- Retail-dominated (institutions slower)
- Global narrative asset (Fed, regulations, macro)
- On-chain data provides additional edge

**Sentiment Sources**:
1. News (40%): Regulations, ETF approvals, institutional adoption
2. Twitter/X (30%): Crypto influencers, #Bitcoin trends, Elon tweets
3. Reddit (20%): r/Bitcoin, r/CryptoCurrency sentiment
4. Technical (10%): RSI, SMA, trend confirmation

**Macro Correlations**:
- Fed dovish = BTC bullish (risk-on)
- Dollar weakness = BTC strength
- Inflation fears = BTC hedge narrative

---

## Archived Agents (Rationale)

### ❌ agent_spy (S&P 500 ETF)
**Archived**: 2025-11-13
**Reason**: Zero sentiment edge in HFT-dominated mega-caps

**Backtest Results**: 5/5 runs = 0 trades
**Analysis**:
- HFT firms dominate 50-70% of SPY volume
- Sentiment priced in <1 second
- Our 5-min analysis is 300,000 milliseconds too slow
- Academic research: 0% sentiment alpha for mega-caps

**Location**: `agents/_archived/agent_spy/`

---

### ❌ agent_aapl (Apple)
**Archived**: 2025-11-13
**Reason**: Inconsistent results, limited sentiment edge

**Backtest Results**: 49% avg win rate, extreme variance
**Analysis**:
- $3T market cap = most efficient stock
- 50+ analysts covering every move
- News instantly priced by institutional algorithms
- Limited edge except quarterly earnings (4x/year)

**Location**: `agents/_archived/agent_aapl/`

---

## Agent File Structure

Each agent has:
```
agents/agent_{symbol}/
├── context.yaml         # Agent configuration
├── personality.md       # Trading philosophy
├── state.json          # Current state (positions, cash, performance)
├── learning.json       # Performance tracking
└── performance.json    # Historical metrics
```

### context.yaml
```yaml
agent:
  id: agent_tsla
  name: Tesla Sentiment Trader
  asset: TSLA
  status: active
  created: '2025-10-01T10:00:00'

strategy:
  type: sentiment_momentum
  timeframe: 5m
  description: >
    Trade Tesla using sentiment-driven momentum strategy...

risk:
  max_position_size: 5000.0
  stop_loss: 0.03
  take_profit: 0.06
  max_daily_trades: 5
  min_confidence: 0.65

personality:
  risk_tolerance: aggressive
  description: >
    Aggressive trader exploiting Tesla's sentiment-driven volatility...

trading:
  market_hours: regular
  weekend_trading: false

performance:
  allocated_capital: 10000.0
```

### personality.md
This is the agent's "brain" - its trading philosophy, decision-making framework, and behavioral guidelines. Key sections:

1. **Core Philosophy**: Why this strategy works
2. **Market Context**: Asset-specific characteristics
3. **Entry Signals**: When to buy
4. **Exit Signals**: When to sell
5. **Risk Management**: How to protect capital
6. **Sentiment Integration**: How to use sentiment data
7. **Technical Confirmation**: How to validate with TA
8. **Common Pitfalls**: What to avoid

**Example** (agent_btc excerpt):
```markdown
## Core Philosophy: Exploit 24/7 Sentiment Cycles

Bitcoin is uniquely sentiment-driven because:
1. No closing hours = continuous global news flow
2. Retail participation = slower price discovery
3. Macro narrative asset = Fed, regulations, Elon tweets
4. On-chain transparency = leading indicators

Our edge: Capture sentiment shifts in the 30-180 minute lag
before institutions fully arbitrage.

## Entry Signals
BUY when ALL conditions met:
- Sentiment score > 0.3 (bullish)
- Confidence > 0.65
- RSI < 60 (not overbought)
- Price above 50-period SMA (uptrend)
- Volume > 20% above average (conviction)
```

### state.json
```json
{
  "agent_id": "agent_tsla",
  "current_position": {
    "symbol": "TSLA",
    "quantity": 25,
    "avg_cost": 245.32,
    "unrealized_pnl": 127.50
  },
  "cash_balance": 5000.00,
  "total_value": 11500.00,
  "open_positions": [...],
  "trade_history": [...],
  "daily_stats": {
    "trades_today": 2,
    "pnl_today": 85.32,
    "last_reset": "2025-11-13"
  },
  "last_updated": "2025-11-13T14:30:00"
}
```

---

## Sentiment Analysis System

### Architecture: Multi-Source Aggregation

We aggregate sentiment from 3 sources:
1. **News** (40% weight) - FinBERT on Alpaca News API
2. **Reddit** (25% weight) - FinBERT on r/wallstreetbets, r/stocks, r/investing
3. **SEC** (25% weight) - VADER on SEC EDGAR filings (material events)
4. **Technical** (10% weight) - Trend, volume, momentum confirmation

**Why FinBERT over VADER**:
- 30-40% better accuracy on financial text
- Fine-tuned on 10-K, 10-Q, earnings calls
- Understands financial jargon ("bearish", "downgrades", "guidance miss")
- VADER is general-purpose, not finance-specific

### FinBERT Integration

```python
from cli.utils.finbert_analyzer import get_finbert_analyzer

analyzer = get_finbert_analyzer()

# Analyze text
result = analyzer.analyze("Tesla announces record deliveries, beating estimates by 15%")

# Returns: {
#   'compound': 0.82,  # Overall score (-1 to +1)
#   'pos': 0.85,       # Positive probability
#   'neg': 0.05,       # Negative probability
#   'neu': 0.10        # Neutral probability
# }
```

**Model**: ProsusAI/finbert (BERT-based, fine-tuned on financial data)
**Device**: Auto-detects CUDA/MPS/CPU
**Singleton**: Model loaded once, reused across all calls
**Batch Processing**: Efficient for multiple texts

### Sentiment Aggregator

```python
from cli.utils.sentiment_aggregator import get_sentiment_aggregator

aggregator = get_sentiment_aggregator()
sentiment = aggregator.get_aggregated_sentiment("TSLA")

# Returns: {
#   'score': -0.23,           # Weighted average (-1 to +1)
#   'confidence': 0.65,       # Agreement level (0 to 1)
#   'sources_used': 3,        # Number of sources
#   'agreement_level': 0.67,  # Source consensus
#   'source_breakdown': {
#       'news': {'score': -0.33, 'confidence': 0.57},
#       'reddit': {'score': -0.31, 'confidence': 0.64},
#       'sec': {'score': 0.01, 'confidence': 0.70}
#   }
# }
```

**Weighting Logic**:
```python
weighted_score = (
    0.40 * news_score +
    0.25 * reddit_score +
    0.25 * sec_score +
    0.10 * technical_score
)
```

**Confidence Calculation**:
- Agreement level = how much sources agree (standard deviation)
- High agreement = high confidence
- Mixed signals = low confidence (avoid trading)

### News Analyzer (FinBERT)

```python
from cli.utils.news_analyzer import get_news_analyzer

analyzer = get_news_analyzer()
news_sentiment = analyzer.get_sentiment("TSLA")

# Fetches from Alpaca News API (last 24 hours)
# Analyzes headline + full article text with FinBERT
# Returns weighted average across all articles
```

**Features**:
- Fetches last 50 news articles (24 hours)
- Analyzes full content (not just headlines)
- Weights recent news more heavily (time decay)
- Filters duplicate content
- Source credibility scoring

### Reddit Analyzer (FinBERT)

```python
from cli.utils.reddit_analyzer import get_reddit_analyzer

analyzer = get_reddit_analyzer()
reddit_sentiment = analyzer.get_sentiment("TSLA")

# Searches r/wallstreetbets, r/stocks, r/investing
# Analyzes posts + top comments with FinBERT
# Returns weighted average with trending score
```

**Features**:
- Searches relevant subreddits
- Analyzes posts (title + body) and comments
- Trending score based on upvotes/comments
- Time-weighted (recent more important)
- Filters spam/low-quality posts

### SEC Analyzer (VADER)

```python
from cli.utils.sec_analyzer import get_sec_analyzer

analyzer = get_sec_analyzer()
sec_sentiment = analyzer.get_sentiment("TSLA")

# Fetches recent 8-K, 10-Q, 10-K filings
# Focuses on "material events" sections
# Returns sentiment with confidence based on filing count
```

**Note**: Uses VADER (not FinBERT) because SEC filings are structured differently and VADER performs adequately. Future enhancement: fine-tune FinBERT on SEC filings.

---

## Technical Analysis System

### Indicators Provided

```python
from cli.utils.technical_analyzer import get_technical_analyzer

analyzer = get_technical_analyzer()
ta = analyzer.analyze("TSLA", timeframe="5m", lookback=100)

# Returns: {
#   'rsi': 58.5,              # RSI (14-period)
#   'sma_50': 245.32,         # 50-period SMA
#   'sma_200': 238.75,        # 200-period SMA
#   'trend': 'bullish',       # Overall trend
#   'support': 242.50,        # Support level
#   'resistance': 250.00,     # Resistance level
#   'volume_ratio': 1.25,     # Volume vs 20-period avg
#   'volatility': 0.035       # ATR-based volatility
# }
```

### Indicator Details

**RSI (Relative Strength Index)**:
- Period: 14
- Overbought: > 70
- Oversold: < 30
- Mean reversion signals

**SMA (Simple Moving Average)**:
- SMA 50: Short-term trend
- SMA 200: Long-term trend
- Golden cross: SMA 50 > SMA 200 (bullish)
- Death cross: SMA 50 < SMA 200 (bearish)

**Trend Analysis**:
- 100-bar lookback for medium-term trend
- Compares closes: uptrend if majority higher
- Filters noise with directional threshold

**Support/Resistance**:
- Support: Recent swing lows
- Resistance: Recent swing highs
- Used for entry/exit timing

**Volume Analysis**:
- Volume ratio: Current vs 20-period average
- High volume = conviction
- Low volume = weak signal (avoid)

---

## Agent Decision-Making Process

### Subagent Mode (Recommended)

The agent creates a decision request file and waits for Claude Code to analyze and respond.

**Request Format** (`oversight/subagent_requests/{agent_id}_{timestamp}.txt`):
```
TRADING DECISION REQUEST

Agent: agent_tsla
Asset: TSLA
Current Time: 2025-11-13 14:30:00
Mode: dry-run

=== MARKET DATA ===
Last Price: $245.75
Bid/Ask: $245.70 / $245.80
Daily Change: +2.5%
Daily Volume: 125M

=== TECHNICAL ANALYSIS ===
RSI (14): 58.5
SMA 50: $245.32
SMA 200: $238.75
Trend: bullish
Support: $242.50
Resistance: $250.00
Volume Ratio: 1.25x

=== SENTIMENT ANALYSIS ===
Aggregated Score: +0.35 (bullish)
Confidence: 0.72
Sources Used: 3
Agreement: 75%

News Sentiment: +0.42 (14 articles, high confidence)
  - "Tesla beats delivery estimates by 15%"
  - "Analyst upgrades TSLA to Strong Buy"

Reddit Sentiment: +0.31 (11 mentions, trending)
  - r/wallstreetbets: Bullish on earnings beat
  - r/stocks: Positive momentum

SEC Sentiment: 0.01 (7 filings, neutral)

=== AGENT STATE ===
Cash Balance: $10,000.00
Current Position: None
Open Orders: None
Daily Trades: 0 / 5
Risk Capacity: 100%

=== RISK LIMITS ===
Max Position Size: $5,000
Stop Loss: 3%
Take Profit: 6%
Min Confidence: 0.65

=== REQUEST ===
Based on the above analysis and your personality, should you:
1. BUY TSLA
2. SELL TSLA
3. HOLD (no action)

Provide your decision with reasoning.
```

**Response Format** (`oversight/subagent_responses/{agent_id}_{timestamp}.txt`):
```
DECISION: BUY
QUANTITY: 20 shares
REASONING:
- Strong bullish sentiment (0.72 confidence, 75% agreement)
- Technical confirmation: price above SMA 50 and 200
- High volume (1.25x) confirms conviction
- RSI at 58.5 (room to run, not overbought)
- News catalyst: earnings beat + analyst upgrades
- Position sizing: $4,915 (49% capital, within 50% limit)
- Stop loss: $238.37 (3% below entry)
- Take profit: $260.50 (6% above entry)

RISK ASSESSMENT:
- Well within risk limits
- High confidence in setup
- Clear exit plan (stop + target)
```

The system parses this response and executes the trade (or simulates in dry-run mode).

---

## Creating a New Agent

### Step-by-Step Guide

1. **Create agent directory**:
```bash
mkdir -p agents/agent_symbol
cd agents/agent_symbol
```

2. **Create context.yaml**:
```yaml
agent:
  id: agent_symbol
  name: Symbol Trading Agent
  asset: SYMBOL
  status: active
  created: '2025-11-13T00:00:00'

strategy:
  type: sentiment_momentum  # or mean_reversion
  timeframe: 15m
  description: >
    Brief strategy description

risk:
  max_position_size: 5000.0
  stop_loss: 0.025
  take_profit: 0.05
  max_daily_trades: 4
  min_confidence: 0.65

personality:
  risk_tolerance: moderate  # conservative, moderate, aggressive
  description: >
    Brief personality description

trading:
  market_hours: regular  # or extended, 24/7
  weekend_trading: false

performance:
  allocated_capital: 10000.0
```

3. **Create personality.md**:
```markdown
# Agent Personality: Symbol Trading Agent

## Core Philosophy
Why this strategy works for this asset...

## Market Context
Asset-specific characteristics...

## Entry Signals
When to buy (with specific thresholds)...

## Exit Signals
When to sell (with specific thresholds)...

## Risk Management
How to protect capital...

## Sentiment Integration
How to use sentiment data...

## Technical Confirmation
How to validate with TA...

## Common Pitfalls
What to avoid...
```

4. **Create initial state.json**:
```json
{
  "agent_id": "agent_symbol",
  "current_position": null,
  "cash_balance": 10000.0,
  "total_value": 10000.0,
  "open_positions": [],
  "trade_history": [],
  "daily_stats": {
    "trades_today": 0,
    "pnl_today": 0.0,
    "last_reset": "2025-11-13"
  },
  "last_updated": "2025-11-13T00:00:00"
}
```

5. **Test in dry-run mode**:
```bash
uv run ztrade agent run agent_symbol --subagent --dry-run
```

6. **Backtest before live trading**:
```bash
uv run ztrade backtest run agent_symbol --start 2024-01-01 --end 2024-12-31
```

7. **Paper trade** for 2-4 weeks minimum

8. **Only then consider** live trading (if ever)

---

## Agent Performance Analysis

### Tracking Metrics

```python
from cli.utils.performance_tracker import get_performance_tracker

tracker = get_performance_tracker()

# Log a trade with sentiment
trade_id = tracker.log_trade_with_sentiment(
    agent_id="agent_tsla",
    symbol="TSLA",
    action="buy",
    quantity=20,
    price=245.75,
    sentiment_score=0.35,
    sentiment_confidence=0.72,
    technical_signals={'rsi': 58.5, 'trend': 'bullish'}
)

# Log trade outcome
tracker.log_trade_outcome(
    trade_id=trade_id,
    exit_price=260.50,
    pnl=294.00,
    reason="Take profit hit"
)

# Generate performance report
report = tracker.generate_report(agent_id="agent_tsla", lookback_days=30)
```

**Report Includes**:
- Win rate by sentiment score bucket
- Average P&L by confidence level
- Source effectiveness (which source predicts best)
- Technical indicator performance
- Time-of-day patterns
- Entry/exit timing analysis

---

## Sentiment-Driven Strategy Principles

### Core Insight: Sentiment Alpha Inversely Correlates with Market Cap

| Market Cap | Example | Sentiment Edge | HFT % | Our Position |
|------------|---------|---------------|-------|--------------|
| Mega-cap ($50T) | SPY | 0% | 70%+ | ❌ Avoid |
| Large-cap ($3T) | AAPL | <5% | 60% | ❌ Avoid |
| Large-cap ($800B) | TSLA | 10-15% | 40-50% | ✅ Trade |
| Small-cap ($2T) | IWM | 20-30% | 10-20% | ✅ Trade |
| Crypto ($1.5T) | BTC | 40-60% | 30% | ✅ Trade |

**Academic Support** (ADR-009):
- Tetlock (2007): Sentiment predicts returns in small stocks
- Da et al. (2015): Attention predicts small-cap returns, not large-caps
- Market microstructure: Large-cap sentiment lag <1s, small-cap 15-60 min

### Trading Where Retail Has Edge

**Avoid**:
- HFT-dominated markets (SPY, QQQ)
- Mega-caps with instant price discovery (AAPL, MSFT)
- Ultra-liquid futures (ES, NQ)

**Target**:
- Volatile large-caps with retail interest (TSLA)
- Small-caps with limited analyst coverage (IWM components)
- Crypto with 24/7 global sentiment (BTC, ETH)
- Stocks with social media catalysts

**Strategy**:
1. Identify sentiment-sensitive assets
2. Measure sentiment-to-price lag
3. Enter when sentiment leads price
4. Exit when price catches up
5. Risk management on failed signals

---

## Common Agent Development Tasks

### Tuning Stop Loss / Take Profit
```yaml
# Conservative (low volatility assets)
risk:
  stop_loss: 0.015  # 1.5%
  take_profit: 0.03  # 3%

# Moderate (TSLA-like)
risk:
  stop_loss: 0.03    # 3%
  take_profit: 0.06  # 6%

# Aggressive (crypto)
risk:
  stop_loss: 0.04    # 4%
  take_profit: 0.08  # 8%
```

### Adjusting Confidence Threshold
```yaml
# Safer (fewer trades, higher quality)
risk:
  min_confidence: 0.75

# Balanced
risk:
  min_confidence: 0.65

# Aggressive (more trades, lower quality)
risk:
  min_confidence: 0.55
```

### Changing Timeframes
```yaml
# Scalping (very active)
strategy:
  timeframe: 1m

# Day trading (TSLA)
strategy:
  timeframe: 5m

# Swing trading (IWM)
strategy:
  timeframe: 15m

# Position trading (BTC)
strategy:
  timeframe: 1h
```

---

## Files You'll Work With Most

**Agent Config**:
- `agents/agent_{symbol}/context.yaml`
- `agents/agent_{symbol}/personality.md`
- `agents/agent_{symbol}/state.json`

**Sentiment Analysis**:
- `cli/utils/finbert_analyzer.py` - FinBERT implementation
- `cli/utils/sentiment_aggregator.py` - Multi-source aggregation
- `cli/utils/news_analyzer.py` - News sentiment (FinBERT)
- `cli/utils/reddit_analyzer.py` - Reddit sentiment (FinBERT)
- `cli/utils/sec_analyzer.py` - SEC filings (VADER)

**Technical Analysis**:
- `cli/utils/technical_analyzer.py` - All TA indicators

**Performance**:
- `cli/utils/performance_tracker.py` - Trade logging and analysis

---

## Documentation References

- ADR-008: FinBERT Sentiment Analysis
- ADR-009: Sentiment-Driven Asset Selection
- `agents/_archived/README.md` - Why SPY/AAPL were archived
- Full system: `CLAUDE.md`

---

**Last Updated**: 2025-11-13
**Context Version**: 1.0 (Agent Specialist Persona)
