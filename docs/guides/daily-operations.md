# Daily Trading Operations Guide

Complete guide for running daily trading operations, from pre-market checks to market close procedures.

---

## Overview

This guide covers:
- Pre-market validation (9:00-9:25 AM ET)
- Market open procedures (9:30 AM ET)
- Intraday monitoring
- Market close procedures (4:00 PM ET)
- Post-market analysis

---

## Pre-Market Procedures (9:00 - 9:25 AM ET)

### 1. System Validation

Run the pre-flight check script to verify all systems are operational:

```bash
cd /Users/aboros/Ztrade
uv run python preflight_check.py
```

**Expected Output**:
```
================================================================================
  TOTAL: 6/6 tests passed
  STATUS: ✅ READY FOR PAPER TRADING
================================================================================
```

**What It Checks**:
- ✅ Market data API connection (Alpaca)
- ✅ Technical analysis functions (RSI, SMA, trend)
- ✅ Sentiment analysis (News, Reddit, SEC)
- ✅ Multi-source aggregation
- ✅ Agent configuration loading
- ✅ Full decision cycle integration

**If Tests Fail**:
1. Check API keys in `.env`
2. Verify internet connection
3. Check logs: `tail -f logs/system/*.log`
4. Review troubleshooting section below

---

### 2. Review Overnight News

Check for market-moving news that may require adjustments:

```bash
# Quick sentiment check for each agent
uv run ztrade agent status agent_tsla
uv run ztrade agent status agent_iwm
uv run ztrade agent status agent_btc
```

**Key Items to Review**:
- Earnings announcements
- Fed statements
- Major regulatory news
- Geopolitical events
- Crypto-specific news (ETF approvals, regulations)

---

### 3. Verify Agent Configurations

Ensure no accidental config changes:

```bash
# Check agent directories
ls -la agents/

# Verify active agents
uv run ztrade agent list
```

**Expected Active Agents**:
- agent_tsla (TSLA, 5m bars)
- agent_iwm (IWM, 15m bars)
- agent_btc (BTC/USD, 1h bars)

---

## Market Open Procedures (9:30 AM ET)

### Option A: Automated Start (Recommended)

**Using Scheduler Script** (starts automatically at 9:30 AM):

```bash
# Run before 9:30 AM (waits until market open)
cd /Users/aboros/Ztrade
./start_trading_at_market_open.sh --automated
```

**Manual Start** (run at exactly 9:30 AM):

```bash
# Start all agents
uv run ztrade loop start agent_tsla --automated --dry-run --interval 300 &
uv run ztrade loop start agent_iwm --automated --dry-run --interval 900 &
uv run ztrade loop start agent_btc --automated --dry-run --interval 3600 &

# View logs
tail -f logs/decisions/agent_tsla_*.log
```

---

### Option B: Subagent Mode (Development)

**Requirements**:
- Keep Claude Code terminal open
- Keep computer awake
- Stay connected to session

```bash
# In Claude Code terminal at 9:30 AM
uv run ztrade loop start agent_tsla --subagent --dry-run --interval 300
```

**Note**: Subagent mode stops if terminal closes. Use automated mode for all-day operation.

---

## Intraday Monitoring

### Every Hour: Check Agent Status

```bash
# Quick status check
uv run ztrade loop status

# Detailed agent status
uv run ztrade agent status agent_tsla
uv run ztrade agent status agent_iwm
uv run ztrade agent status agent_btc
```

**Key Metrics to Monitor**:
- ✅ Loops are running (not stopped)
- ✅ Recent decisions (< 15 min old)
- ✅ No error messages in logs
- ✅ P&L within expected range
- ✅ Sentiment data is fresh

---

### Live Log Monitoring

**View all agents**:
```bash
tail -f logs/decisions/*.log
```

**View specific agent**:
```bash
# TSLA
tail -f logs/decisions/agent_tsla_*.log

# IWM
tail -f logs/decisions/agent_iwm_*.log

# BTC
tail -f logs/decisions/agent_btc_*.log
```

---

### Dashboard Monitoring

```bash
# Start Streamlit dashboard
./run_dashboard.sh

# Or manually
uv run streamlit run dashboard.py
```

**Access**: http://localhost:8501

**Dashboard Sections**:
- Real-time P&L
- Position summary
- Recent decisions
- Sentiment trends
- Technical indicators

---

## Market Close Procedures (4:00 PM ET)

### 1. Review Day's Performance

```bash
# Company-wide summary
uv run ztrade company dashboard

# Individual agent performance
uv run ztrade agent status agent_tsla
uv run ztrade agent status agent_iwm
```

---

### 2. Stop Trading Loops (Optional)

**If stopping for the day**:
```bash
uv run ztrade loop stop agent_tsla
uv run ztrade loop stop agent_iwm
# BTC continues 24/7
```

**Note**: Agents can continue running for after-hours trading. BTC trades 24/7.

---

### 3. Export Logs

```bash
# Create daily log archive
DATE=$(date +%Y%m%d)
mkdir -p logs/daily_archives/
cp logs/decisions/*.log logs/daily_archives/${DATE}/
```

---

### 4. Document Notable Events

Create a brief summary of the day:

```bash
# Example daily log
cat > logs/daily_archives/${DATE}/summary.txt << EOF
Date: $(date +%Y-%m-%d)
Market: [Open/Volatile/Quiet/Trending]

TSLA:
- Trades: X
- P&L: $XXX
- Notable: [Any significant events]

IWM:
- Trades: X
- P&L: $XXX
- Notable: [Any significant events]

BTC:
- Trades: X
- P&L: $XXX
- Notable: [Any significant events]

Notes: [Key learnings, observations, anomalies]
EOF
```

---

## Weekend Procedures

### Saturday: Weekly Review

```bash
# Generate weekly performance report
uv run ztrade company performance --days 7

# Check position status
uv run ztrade company positions
```

**Review Questions**:
1. Which agents performed best/worst?
2. Which sentiment sources were most accurate?
3. Were there any risk limit violations?
4. Any configuration adjustments needed?

---

### Sunday: Prepare for Monday

**Checklist**:
- [ ] Review economic calendar for Monday
- [ ] Check for upcoming earnings (affects TSLA)
- [ ] Verify API keys haven't expired
- [ ] Update agent configs if needed
- [ ] Test pre-flight check
- [ ] Review and update this guide if procedures changed

---

## Troubleshooting

### Agents Not Starting

**Symptoms**: Loop status shows "stopped" or "not found"

**Solutions**:
```bash
# Check if loops are actually stopped
ps aux | grep ztrade

# Kill any hanging processes
pkill -f "ztrade loop"

# Restart fresh
uv run ztrade loop start agent_tsla --automated --interval 300
```

---

### No Recent Decisions

**Symptoms**: Last decision > 30 minutes old

**Solutions**:
```bash
# Check logs for errors
tail -50 logs/system/*.log | grep ERROR

# Verify market data
uv run python -c "from cli.utils.broker import get_broker; print(get_broker().get_latest_quote('TSLA'))"

# Restart loop
uv run ztrade loop stop agent_tsla
uv run ztrade loop start agent_tsla --automated --interval 300
```

---

### Sentiment Data Missing

**Symptoms**: Sentiment score = 0.0 or "No sentiment data available"

**Solutions**:
```bash
# Check API keys
grep "API_KEY" .env

# Test news API
uv run python -c "from cli.utils.news_analyzer import get_news_analyzer; print(get_news_analyzer().get_news_sentiment('TSLA'))"

# Test Reddit API
uv run python -c "from cli.utils.reddit_analyzer import get_reddit_analyzer; print(get_reddit_analyzer().get_reddit_sentiment('TSLA'))"
```

---

### High API Costs (Automated Mode)

**Symptoms**: Anthropic API bill higher than expected

**Monitor Costs**:
- Check Anthropic console: https://console.anthropic.com/
- Expected: ~$0.003 per decision
- Daily (7 hours, 84 decisions): ~$0.25
- Monthly (20 trading days): ~$5.00

**Reduce Costs**:
1. Increase decision interval (300s → 600s)
2. Switch to subagent mode for development
3. Reduce number of active agents
4. Use dry-run mode for testing

---

## Emergency Stop

**If something goes wrong and you need to stop everything immediately**:

```bash
# Stop all loops
uv run ztrade loop stop agent_tsla
uv run ztrade loop stop agent_iwm
uv run ztrade loop stop agent_btc

# Kill all ztrade processes
pkill -f "ztrade loop"

# Verify everything stopped
ps aux | grep ztrade
```

**Then**:
1. Review logs to understand what happened
2. Fix the issue
3. Run pre-flight check before restarting
4. Restart with dry-run mode first

---

## Quick Command Reference

```bash
# Pre-market
uv run python preflight_check.py                          # Validate system
uv run ztrade agent list                                  # List agents

# Market open
./start_trading_at_market_open.sh --automated             # Scheduled start
uv run ztrade loop start agent_tsla --automated --interval 300  # Manual start

# Monitoring
uv run ztrade loop status                                 # Loop status
uv run ztrade agent status agent_tsla                     # Agent status
tail -f logs/decisions/agent_tsla_*.log                   # Live logs

# Market close
uv run ztrade company dashboard                           # Daily summary
uv run ztrade loop stop agent_tsla                        # Stop trading

# Emergency
pkill -f "ztrade loop"                                    # Kill all loops
```

---

## Notes

- **Paper Trading**: All operations use Alpaca paper trading. No real money at risk.
- **Dry-Run Mode**: Use `--dry-run` flag to simulate without executing trades.
- **Logging**: All decisions logged to `logs/decisions/` and `logs/system/`.
- **Monitoring**: Dashboard available at http://localhost:8501 when running.

---

**Last Updated**: 2025-11-17
**For**: Daily trading operations (paper trading)
