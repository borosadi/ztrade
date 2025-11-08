# Development Commands

Quick reference for all CLI commands and development workflows.

---

## Environment Setup

```bash
# Using uv (recommended)
uv sync

# Or traditional setup
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Verify environment setup
uv run ztrade hello
```

---

## Running the CLI

### Basic Commands

```bash
# Main CLI entry point
uv run ztrade [COMMAND]

# Get help
uv run ztrade --help
uv run ztrade agent --help
```

### Agent Commands

```bash
# List all agents
uv run ztrade agent list

# Show agent status
uv run ztrade agent status AGENT_ID

# Create new agent
uv run ztrade agent create AGENT_ID
```

### Trading Modes

```bash
# Subagent mode (dry-run, recommended for testing)
uv run ztrade agent run AGENT_ID --subagent --dry-run

# Subagent mode (paper trading)
uv run ztrade agent run AGENT_ID --subagent

# Manual mode (no API key needed, dry-run)
uv run ztrade agent run AGENT_ID --manual --dry-run

# Manual mode (paper trading)
uv run ztrade agent run AGENT_ID --manual

# Automated mode (requires ANTHROPIC_API_KEY)
uv run ztrade agent run AGENT_ID
```

### Company Commands

```bash
# View company dashboard
uv run ztrade company dashboard

# Show all positions
uv run ztrade company positions

# Run risk check
uv run ztrade company risk-check
```

### Risk Management Commands

```bash
# Show risk status
uv run ztrade risk status

# Show correlations between assets
uv run ztrade risk correlations

# Simulate market scenarios
uv run ztrade risk simulate market_crash
```

### Monitoring Commands

```bash
# Monitor agent decisions
uv run ztrade monitor decisions AGENT_ID

# Monitor trades
uv run ztrade monitor trades AGENT_ID
```

---

## Celery Orchestration (Production)

### Control Script

```bash
# Start all Celery services (worker + beat + flower)
./celery_control.sh start

# Check service status
./celery_control.sh status

# Stop all services
./celery_control.sh stop

# Restart services
./celery_control.sh restart

# View logs
./celery_control.sh logs worker
./celery_control.sh logs beat
./celery_control.sh logs flower

# Send test task
./celery_control.sh test

# Purge all tasks from queue
./celery_control.sh purge
```

### Web UI

- **Flower Dashboard**: http://localhost:5555
  - Real-time task monitoring
  - Task history and results
  - Worker statistics
  - Task rate graphs

---

## Testing

```bash
# Run all backtests
python -m pytest tests/backtests/

# Run paper trading tests
python -m pytest tests/paper_trading/

# Run specific test file
python -m pytest tests/backtests/test_strategy.py

# Run with verbose output
python -m pytest -v tests/

# Run with coverage
python -m pytest --cov=cli tests/
```

---

## Git Workflow

```bash
# Check status
git status

# Stage changes
git add .

# Commit with message
git commit -m "Your commit message"

# Push to remote
git push origin main

# View commit history
git log --oneline -10
```

---

## Common Development Tasks

### Adding a New Dependency

```bash
# Add to requirements.txt
echo "package-name>=version" >> requirements.txt

# Install with uv
uv sync

# Or with pip
pip install package-name
```

### Running Python Scripts Directly

```bash
# Run with uv
uv run python script.py

# Or activate venv first
source venv/bin/activate
python script.py
```

### Checking Logs

```bash
# View agent decisions
cat logs/agent_decisions/YYYY-MM-DD/agent_spy.log

# View trades
cat logs/trades/YYYY-MM-DD/agent_spy.log

# View system logs
cat logs/system/YYYY-MM-DD.log

# Tail logs in real-time
tail -f logs/trades/YYYY-MM-DD/agent_spy.log
```

---

## Debugging Tips

### Check Market Data

```bash
# Quick test to fetch market data
uv run python -c "
from cli.utils.market_data import MarketDataProvider
provider = MarketDataProvider()
data = provider.get_market_context('SPY')
print(data)
"
```

### Check Sentiment Analysis

```bash
# Test sentiment aggregator
uv run python -c "
from cli.utils.sentiment_aggregator import get_sentiment_aggregator
agg = get_sentiment_aggregator()
sentiment = agg.get_aggregated_sentiment('TSLA')
print(sentiment)
"
```

### Check Broker Connection

```bash
# Test Alpaca connection
uv run python -c "
from cli.utils.broker import Broker
broker = Broker()
account = broker.get_account_info()
print(f'Buying power: ${account.buying_power}')
"
```

---

## Environment Variables

Required `.env` file:

```bash
# Alpaca API (required)
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Anthropic API (optional, only for automated mode)
ANTHROPIC_API_KEY=your_key_here

# Reddit API (optional, for Reddit sentiment)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT="Ztrade:v1.0 (by /u/your_username)"

# TradingView API (optional)
TRADINGVIEW_API_KEY=your_key_here
```
