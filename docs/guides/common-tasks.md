# Common Tasks

Step-by-step guides for frequent development tasks.

---

## Adding a New Trading Agent

### 1. Create Agent Directory

```bash
mkdir -p agents/agent_[name]
```

### 2. Create Configuration Files

Create `agents/agent_[name]/context.yaml`:

```yaml
agent:
  id: agent_[name]
  name: "[Descriptive Name]"
  asset: [SYMBOL]
  strategy:
    type: [momentum|mean_reversion|breakout]
    timeframe: [5m|15m|1h|4h|daily]
  risk:
    max_position_size: [USD amount]
    stop_loss: [percentage as decimal, e.g., 0.02 for 2%]
    max_daily_trades: [integer]
    min_confidence: [0.0 to 1.0]
  personality:
    risk_tolerance: [conservative|moderate|aggressive]
```

Create `agents/agent_[name]/personality.md`:

```markdown
# [Agent Name] - Trading Personality

## Philosophy
[Describe trading philosophy and approach]

## Strategy
[Explain core strategy and decision-making criteria]

## Risk Management
[Detail risk tolerance and position sizing approach]

## Decision Framework
[Outline how the agent evaluates opportunities]
```

Create initial state files:

```bash
# state.json
echo '{"positions": [], "daily_pnl": 0.0, "trade_count": 0}' > agents/agent_[name]/state.json

# performance.json
echo '{"total_trades": 0, "win_rate": 0.0, "sharpe_ratio": null}' > agents/agent_[name]/performance.json

# learning.json
echo '{"patterns": [], "insights": []}' > agents/agent_[name]/learning.json
```

### 3. Update Company Configuration

Add asset to `config/company_config.yaml`:

```yaml
allowed_assets:
  - SPY
  - TSLA
  - AAPL
  - [NEW_SYMBOL]  # Add your new asset
```

### 4. Test the Agent

```bash
# Dry-run mode first
uv run ztrade agent run agent_[name] --subagent --dry-run

# Then paper trading
uv run ztrade agent run agent_[name] --subagent
```

---

## Implementing a New CLI Command

### 1. Choose Command Group

Identify which command group your command belongs to:
- `cli/commands/agent.py` - Agent-related commands
- `cli/commands/company.py` - Company-level commands
- `cli/commands/risk.py` - Risk management commands
- `cli/commands/monitor.py` - Monitoring commands
- Or create a new file for a new command group

### 2. Add Command Function

```python
import click
from cli.utils.logger import log_info, log_error

@click.command()
@click.argument('param1')
@click.option('--flag', is_flag=True, help='Optional flag')
def my_command(param1, flag):
    """
    Brief description of what this command does.

    PARAM1: Description of the parameter
    """
    try:
        log_info(f"Executing command with param: {param1}")

        # Command logic here
        result = do_something(param1, flag)

        log_info(f"Command completed: {result}")

    except Exception as e:
        log_error(f"Command failed: {str(e)}")
        raise
```

### 3. Register Command

If creating a new command group:

```python
# In the new commands file
import click

@click.group()
def mygroup():
    """Description of command group"""
    pass

mygroup.add_command(my_command)
```

Then in `cli/main.py`:

```python
from cli.commands.mygroup import mygroup

cli.add_command(mygroup)
```

### 4. Test Command

```bash
# Check help text
uv run ztrade mygroup my-command --help

# Run command
uv run ztrade mygroup my-command param1 --flag
```

---

## Adding Risk Validation

### 1. Define Risk Rule

Add to `config/risk_limits.yaml`:

```yaml
rules:
  # Existing rules...

  - name: RULE_XXX
    description: "Description of the new rule"
    type: [position|exposure|correlation|volatility]
    threshold: [numeric value]
    action: [warn|block|halt]
```

### 2. Implement Check Function

In `cli/utils/risk_validator.py` (or create if doesn't exist):

```python
def check_new_rule(agent_id, context):
    """
    Check if the new risk rule is violated.

    Args:
        agent_id: The agent making the trade
        context: Trading context with position details

    Returns:
        dict: {'passed': bool, 'reason': str, 'severity': str}
    """
    # Implement validation logic
    threshold = get_risk_limit('RULE_XXX')

    if violation_detected:
        return {
            'passed': False,
            'reason': f"Rule XXX violated: {details}",
            'severity': 'high'
        }

    return {
        'passed': True,
        'reason': 'Rule XXX check passed',
        'severity': 'low'
    }
```

### 3. Add to Pre-Trade Validation

In the pre-trade validation flow (likely in `cli/commands/agent.py`):

```python
# Add to validation checks
validation_results = []

# Existing checks...
validation_results.append(check_position_size(...))
validation_results.append(check_daily_limit(...))

# New check
validation_results.append(check_new_rule(agent_id, context))

# Evaluate results
for result in validation_results:
    if not result['passed']:
        log_error(f"Validation failed: {result['reason']}")
        # Handle failure based on severity
```

### 4. Update Audit Log

Log validation in `oversight/audit_log.json`:

```python
from cli.utils.logger import log_audit

log_audit({
    'timestamp': datetime.now().isoformat(),
    'agent_id': agent_id,
    'rule': 'RULE_XXX',
    'result': result,
    'action_taken': 'trade_blocked' if not result['passed'] else 'trade_approved'
})
```

---

## Using Multi-Source Sentiment Analysis

### Quick Usage

```python
from cli.utils.sentiment_aggregator import get_sentiment_aggregator

# Get aggregator instance
aggregator = get_sentiment_aggregator()

# Fetch aggregated sentiment
sentiment = aggregator.get_aggregated_sentiment(
    symbol="TSLA",
    news_lookback_hours=24,
    reddit_lookback_hours=24,
    sec_lookback_days=30
)

# Access results
print(f"Overall sentiment: {sentiment['overall_sentiment']}")
print(f"Score: {sentiment['sentiment_score']}")
print(f"Confidence: {sentiment['confidence']}")
print(f"Sources used: {sentiment['sources_used']}")
print(f"Agreement: {sentiment['agreement_level']}")
```

### Using Individual Sources

```python
# News only
from cli.utils.news_analyzer import get_news_analyzer
news = get_news_analyzer()
news_sentiment = news.get_news_sentiment("SPY", lookback_hours=24)

# Reddit only (requires credentials)
from cli.utils.reddit_analyzer import get_reddit_analyzer
reddit = get_reddit_analyzer()
reddit_sentiment = reddit.get_reddit_sentiment("TSLA", lookback_hours=24)

# SEC only
from cli.utils.sec_analyzer import get_sec_analyzer
sec = get_sec_analyzer()
sec_sentiment = sec.get_sec_sentiment("AAPL", lookback_days=30)
```

### Configuring Weights

Edit weights in `cli/utils/sentiment_aggregator.py`:

```python
DEFAULT_WEIGHTS = {
    'news': 0.40,     # 40% weight
    'reddit': 0.25,   # 25% weight
    'sec': 0.25,      # 25% weight
    'stocktwits': 0.10  # 10% weight (future)
}
```

---

## Tracking Performance

### Log Trade with Sentiment

```python
from cli.utils.performance_tracker import get_performance_tracker

tracker = get_performance_tracker()

# When entering trade
trade_id = tracker.log_trade_with_sentiment(
    agent_id="agent_spy",
    symbol="SPY",
    action="buy",
    sentiment_data=sentiment_dict,  # From sentiment_aggregator
    entry_price=677.50,
    quantity=100,
    confidence=0.75,
    rationale="Strong bullish sentiment across all sources"
)

# When exiting trade
tracker.log_trade_outcome(
    trade_id=trade_id,
    exit_price=680.00,
    exit_quantity=100,
    pnl=250.0,
    pnl_pct=0.37,
    exit_reason="Profit target hit"
)
```

### Generate Performance Report

```python
# Generate report
report = tracker.generate_report(lookback_days=30)

# Access metrics
print(f"Sentiment accuracy: {report['sentiment_accuracy']}")
print(f"Source effectiveness: {report['source_effectiveness']}")
print(f"Agreement impact: {report['agreement_impact']}")

# Save to file
tracker.save_report(report, "oversight/sentiment_performance/summary.json")
```

---

## Debugging Common Issues

### Issue: "No module named 'cli'"

**Solution**: Make sure you're using `uv run` or have activated the virtual environment:

```bash
# With uv
uv run ztrade agent list

# Or activate venv
source venv/bin/activate
ztrade agent list
```

### Issue: "Alpaca API authentication failed"

**Solution**: Check your `.env` file:

```bash
# Verify credentials are set
cat .env | grep ALPACA

# Test connection
uv run python -c "from cli.utils.broker import Broker; print(Broker().get_account_info())"
```

### Issue: "Sentiment analysis returns empty results"

**Solution**: Check API credentials and network connectivity:

```bash
# Test news API
uv run python -c "from cli.utils.news_analyzer import get_news_analyzer; print(get_news_analyzer().get_news_sentiment('SPY'))"

# Check Reddit credentials (optional)
cat .env | grep REDDIT
```

### Issue: "Agent state not persisting"

**Solution**: Verify state file permissions and path:

```bash
# Check if state file exists
ls -la agents/agent_spy/state.json

# Verify write permissions
chmod 644 agents/agent_spy/state.json

# Manually view state
cat agents/agent_spy/state.json | python -m json.tool
```
