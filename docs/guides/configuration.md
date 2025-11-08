# Configuration Guide

Complete guide to configuring the Ztrade trading system.

---

## Environment Variables (.env)

### Required Variables

```bash
# Alpaca API - Paper Trading (Required)
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

**Where to get**: Sign up at [Alpaca](https://alpaca.markets) and generate paper trading API keys

### Optional Variables

```bash
# Anthropic Claude API (Optional - only for automated mode)
ANTHROPIC_API_KEY=your_anthropic_api_key

# Reddit API (Optional - for Reddit sentiment analysis)
# Get from: https://www.reddit.com/prefs/apps
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT="Ztrade:v1.0 (by /u/your_username)"

# TradingView API (Optional - for advanced charting)
TRADINGVIEW_API_KEY=your_tradingview_api_key
```

---

## Agent Configuration

### Agent Context (`agents/[agent_id]/context.yaml`)

```yaml
agent:
  id: agent_spy
  name: "SPY Momentum Trader"
  asset: SPY

  strategy:
    type: momentum              # Options: momentum, mean_reversion, breakout
    timeframe: 15m              # Options: 5m, 15m, 1h, 4h, daily
    indicators:                 # Technical indicators to use
      - RSI
      - SMA
      - volume

  risk:
    max_position_size: 10000    # Maximum position size in USD
    stop_loss: 0.02             # Stop loss percentage (2%)
    max_daily_trades: 5         # Maximum trades per day
    min_confidence: 0.60        # Minimum confidence to execute (0-1)
    max_concurrent_positions: 3 # Maximum positions held at once

  personality:
    risk_tolerance: moderate    # Options: conservative, moderate, aggressive
    decision_style: analytical  # Described in personality.md
```

### Agent Personality (`agents/[agent_id]/personality.md`)

Define the agent's trading philosophy, decision-making style, and approach to risk. This file is read by the LLM to guide trading decisions.

Example structure:

```markdown
# [Agent Name] - Trading Personality

## Philosophy
I am a momentum trader focused on capturing short-term trends...

## Strategy
I look for assets showing strong directional movement...

## Risk Management
I use tight stop losses and position sizing based on volatility...

## Decision Framework
I consider:
1. Technical momentum signals
2. Volume confirmation
3. Market sentiment
4. Risk/reward ratio
```

---

## Company Configuration

### Company Config (`config/company_config.yaml`)

```yaml
company:
  name: "Ztrade AI Trading Company"
  initial_capital: 100000

  risk_management:
    max_total_exposure: 0.80        # 80% of capital max deployed
    max_daily_loss: 0.02            # 2% daily loss limit
    max_agent_allocation: 0.10      # 10% per agent max
    correlation_threshold: 0.70     # Max correlation allowed

  allowed_assets:
    - SPY
    - TSLA
    - AAPL
    - QQQ

  trading_hours:
    regular:
      start: "09:30"
      end: "16:00"
      timezone: "America/New_York"
    pre_market:
      enabled: false
      start: "04:00"
      end: "09:30"
    after_hours:
      enabled: false
      start: "16:00"
      end: "20:00"
```

### Risk Limits (`config/risk_limits.yaml`)

```yaml
rules:
  - name: RULE_001
    description: "No agent can exceed 10% of total capital"
    type: position
    threshold: 0.10
    action: block

  - name: RULE_002
    description: "Daily loss limit triggers immediate halt"
    type: exposure
    threshold: 0.02
    action: halt

  - name: RULE_003
    description: "All trades must have stop losses"
    type: position
    threshold: null
    action: block

  - name: RULE_004
    description: "Maximum 3 correlated positions (correlation > 0.7)"
    type: correlation
    threshold: 0.70
    action: warn

  - name: RULE_005
    description: "Position size never exceeds 5% of capital"
    type: position
    threshold: 0.05
    action: block

  - name: RULE_006
    description: "No more than 80% capital deployed"
    type: exposure
    threshold: 0.80
    action: block
```

---

## Broker Configuration

### Alpaca Config (`config/broker_config.yaml`)

```yaml
broker:
  name: alpaca
  mode: paper                # Options: paper, live

  api:
    base_url: ${ALPACA_BASE_URL}
    key_id: ${ALPACA_API_KEY}
    secret_key: ${ALPACA_SECRET_KEY}

  trading:
    default_order_type: market
    allow_fractional_shares: true
    time_in_force: day

  rate_limits:
    requests_per_minute: 200
    orders_per_minute: 60
```

---

## Sentiment Analysis Configuration

### Weights Configuration

Edit `cli/utils/sentiment_aggregator.py`:

```python
DEFAULT_WEIGHTS = {
    'news': 0.40,      # News from Alpaca/Benzinga (40%)
    'reddit': 0.25,    # Reddit r/wallstreetbets, r/stocks (25%)
    'sec': 0.25,       # SEC EDGAR filings (25%)
    'stocktwits': 0.10 # StockTwits (10%, future)
}
```

### Source-Specific Settings

**News Analyzer** (`cli/utils/news_analyzer.py`):
```python
DEFAULT_LOOKBACK_HOURS = 24
DEFAULT_MAX_ARTICLES = 25
```

**Reddit Analyzer** (`cli/utils/reddit_analyzer.py`):
```python
DEFAULT_SUBREDDITS = ['wallstreetbets', 'stocks', 'investing']
DEFAULT_LOOKBACK_HOURS = 24
DEFAULT_MAX_POSTS = 50
```

**SEC Analyzer** (`cli/utils/sec_analyzer.py`):
```python
DEFAULT_LOOKBACK_DAYS = 30
DEFAULT_MAX_FILINGS = 10
FILING_TYPES = ['10-K', '10-Q', '8-K']
```

---

## Loop Configuration

### Market Hours

Edit `cli/utils/loop_manager.py`:

```python
MARKET_OPEN = time(9, 30)      # 9:30 AM
MARKET_CLOSE = time(16, 0)     # 4:00 PM
MARKET_TIMEZONE = 'America/New_York'
```

### Default Intervals

```python
DEFAULT_INTERVAL = 300  # 5 minutes (in seconds)
DEFAULT_MAX_CYCLES = None  # Run indefinitely
```

---

## Celery Configuration

### Task Scheduling

Edit `celery_app.py`:

```python
app.conf.beat_schedule = {
    'agent-spy-trading-loop': {
        'task': 'celery_app.run_trading_cycle',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'args': ('agent_spy',)
    },
    'agent-tsla-trading-loop': {
        'task': 'celery_app.run_trading_cycle',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'args': ('agent_tsla',)
    },
    'agent-aapl-trading-loop': {
        'task': 'celery_app.run_trading_cycle',
        'schedule': crontab(minute='0', hour='*'),  # Every hour
        'args': ('agent_aapl',)
    },
}
```

### Celery Settings

```python
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.timezone = 'America/New_York'
```

---

## Logging Configuration

### Log Levels

Edit `cli/utils/logger.py`:

```python
LOG_LEVEL = 'INFO'  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Log Directories

```
logs/
├── trades/           # Trade execution logs
│   └── YYYY-MM-DD/
├── agent_decisions/  # Agent reasoning logs
│   └── YYYY-MM-DD/
└── system/           # System events
    └── YYYY-MM-DD.log
```

---

## Configuration Best Practices

### 1. Never Commit Secrets
- Keep `.env` in `.gitignore`
- Use environment variables for all credentials
- Share `.env.example` as template

### 2. Start Conservative
- Use paper trading mode initially
- Set low position sizes
- Enable all risk limits
- Require high confidence thresholds

### 3. Gradual Configuration Changes
- Change one parameter at a time
- Test thoroughly after each change
- Document why changes were made
- Monitor impact on performance

### 4. Regular Backups
```bash
# Backup agent states
cp -r agents/ backups/agents_$(date +%Y%m%d)/

# Backup configurations
cp -r config/ backups/config_$(date +%Y%m%d)/
```

### 5. Version Control Configurations
- Commit config changes with clear messages
- Tag important configuration milestones
- Document configuration decisions in ADRs
