# Data Accumulation Plan - Organic Growth Strategy

**Strategy**: Live paper trading with organic historical data accumulation
**Start Date**: 2025-11-26
**Target**: 30 days validation period
**Cost**: $0 (no paid data providers)

---

## 🎯 Overview

Instead of backfilling historical data (blocked by free-tier API limitations), we're starting paper trading immediately and letting the system accumulate production data organically as the DAGs run.

**Benefits**:
- ✅ Tests the complete system end-to-end under real conditions
- ✅ Zero additional cost
- ✅ Database grows naturally with production-quality data
- ✅ Validates both sentiment analysis and technical analysis pipelines

**Trade-offs**:
- ⚠️ First 7 days: Limited trading activity (sentiment-only, low confidence)
- ⚠️ Days 7-14: Technical analysis activates as 100+ bars accumulate
- ⚠️ Day 30+: Full validation dataset ready for backtesting

---

## 📊 Current System Status

### Active DAGs

| Agent | Asset | Schedule | Status | Successful Runs (24hrs) |
|-------|-------|----------|--------|-------------------------|
| **agent_tsla** | TSLA | Every 5 minutes | ✅ Running | 49 runs |
| **agent_iwm** | IWM | Every 15 minutes | ✅ Running | 26 runs |
| **agent_btc** | BTC/USD | Every 60 minutes (24/7) | ✅ **FIXED** | 0 runs (just fixed) |

### Database Status

**Tables Created**: ✅
- `market_bars` - 0 rows (will accumulate)
- `sentiment_history` - 0 rows (will accumulate)
- `backtest_runs` - 0 rows
- `backtest_trades` - 0 rows

**Migration**: ✅ SQLite (no PostgreSQL port conflicts)

---

## 📅 30-Day Timeline & Milestones

### Days 1-7: **Sentiment-Only Trading** ⚠️

**What's Happening**:
- DAGs run every 5m (TSLA), 15m (IWM), 1h (BTC)
- Sentiment analysis: ✅ Working (News + SEC filings)
- Technical analysis: ❌ Empty (no historical data yet)
- Decision confidence: ~35-58% (below 70% threshold)

**Expected Results**:
- Trades executed: **0-2 trades** (insufficient confidence)
- Market bars accumulated:
  - TSLA: ~546 bars (7 days × 78 bars/day)
  - IWM: ~182 bars (7 days × 26 bars/day)
  - BTC: ~168 bars (7 days × 24 bars/day)

**Milestone**: ⚠️ **Approaching 100-bar minimum for technical analysis**

---

### Days 7-14: **Technical Analysis Activation** ✅

**What's Happening**:
- 100+ bars available → Technical indicators start working
- RSI calculations: ✅ Enabled (requires 14 bars)
- SMA crossovers: ✅ Enabled (requires 20-50 bars)
- Trend detection: ✅ Enabled (requires 100 bars)
- Combined confidence: ~65-75% (meeting 70% threshold)

**Expected Results**:
- Trades executed: **5-10 trades** (technical analysis kicks in)
- Market bars accumulated:
  - TSLA: ~1,092 bars (14 days)
  - IWM: ~364 bars (14 days)
  - BTC: ~336 bars (14 days)

**Milestone**: ✅ **First meaningful trades executed**

---

### Days 14-30: **Full Strategy Validation** 🚀

**What's Happening**:
- Full sentiment + technical synthesis operational
- All 3 agents trading independently
- Risk management rules enforced
- Performance tracking active

**Expected Results**:
- Trades executed: **20-40 trades** across all agents
- Market bars accumulated:
  - TSLA: ~2,340 bars (30 days)
  - IWM: ~780 bars (30 days)
  - BTC: ~720 bars (30 days)

**Milestone**: ✅ **Validation dataset complete, ready for backtesting**

---

### Day 30: **Checkpoint Decision** 🎯

**Validation Criteria**:
```
✅ At least 20 trades executed
✅ Win rate > 60% (target: match backtest 91.2%)
✅ Max drawdown < 10%
✅ All 3 agents individually profitable
✅ No circuit breaker violations
✅ 30+ days continuous operation
```

**Decision Tree**:
```
After 30 days:
├─ Win rate > 60% + Positive returns?
│  ├─ YES → Upgrade to paid data provider for advanced backtesting
│  │        ($29-50/month Polygon.io or Alpha Vantage Premium)
│  └─ NO → Continue paper trading, optimize parameters
│
└─ System stable and reliable?
   ├─ YES → Plan live trading transition (small capital)
   └─ NO → Debug and extend validation period
```

---

## 🔧 Daily Monitoring

### Quick Health Check

Run the monitoring script daily:

```bash
cd /Users/aboros/Ztrade
./check_data_status.sh
```

**What to Look For**:
- ✅ All DAGs running successfully
- ✅ Bar count increasing daily
- ⚠️ Failed runs < 5% of total
- ⚠️ Database size growing

### Manual Database Check

```bash
docker exec airflow-airflow-scheduler-1 python -c "
from ztrade.core.database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.execute('''
        SELECT symbol, timeframe, COUNT(*) as bars,
               MIN(timestamp) as oldest, MAX(timestamp) as newest
        FROM market_bars
        GROUP BY symbol, timeframe
        ORDER BY symbol, timeframe
    ''')

    for row in cursor:
        print(f'{row[0]:6} {row[1]:4} {row[2]:5} bars from {row[3][:10]} to {row[4][:10]}')
"
```

### Airflow UI Monitoring

**URL**: http://localhost:8080 (admin/admin)

**What to Check**:
- DAG runs: Green = success, Red = failed
- Task duration: Should be < 30 seconds per task
- XCom data: Check sentiment scores, technical signals
- Logs: Review decision rationale, trade rejections

---

## 📈 Expected Data Growth

| Day | TSLA Bars | IWM Bars | BTC Bars | Technical Analysis | Trading Activity |
|-----|-----------|----------|----------|-------------------|------------------|
| 1 | 78 | 26 | 24 | ❌ Insufficient | 0 trades |
| 3 | 234 | 78 | 72 | ⚠️ Marginal | 0-1 trades |
| 7 | 546 | 182 | 168 | ✅ **Activated** | 1-3 trades |
| 14 | 1,092 | 364 | 336 | ✅ Fully functional | 5-10 trades |
| 21 | 1,638 | 546 | 504 | ✅ Mature dataset | 10-20 trades |
| 30 | 2,340 | 780 | 720 | ✅ **Validation ready** | 20-40 trades |

---

## 🎯 Success Metrics (30-Day Checkpoint)

### Trading Performance

| Metric | Target | Backtest Baseline (TSLA) |
|--------|--------|-------------------------|
| **Win Rate** | > 60% | 91.2% |
| **Total Return** | > 0% | 8.51% (60 days) |
| **Max Drawdown** | < 10% | 2.06% |
| **Sharpe Ratio** | > 0.0 | -0.53 |
| **Avg Trade P&L** | > $0 | $26.68 |

### System Reliability

| Metric | Target |
|--------|--------|
| DAG Success Rate | > 95% |
| Database Uptime | 100% |
| API Errors | < 5% of requests |
| Circuit Breakers | 0 triggered |

---

## ⚠️ Known Issues & Solutions

### Issue: BTC DAG Was Failing (100% Failure Rate)

**Status**: ✅ **FIXED** (2025-11-26)

**Root Cause**: Market hours check used stock trading hours (9am-4pm M-F) instead of 24/7 crypto trading

**Fix**: Updated `agent_btc_dag.py` `is_market_hours()` function to always return `True` for crypto

**Verification**: BTC DAG should start running successfully within 1 hour

---

### Issue: No Historical Data for Technical Analysis

**Status**: ✅ **EXPECTED** (by design)

**Root Cause**: Free-tier API limitations prevent backfilling 60 days of intraday data

**Solution**: Organic accumulation over 7-14 days (current strategy)

**Timeline**: Technical analysis activates around Day 7 (100+ bars)

---

### Issue: Low Trade Frequency (First Week)

**Status**: ✅ **EXPECTED** (by design)

**Root Cause**: Without technical analysis, sentiment-only confidence is ~35-58%, below 70% threshold

**Solution**: Wait for Day 7+ when technical analysis activates

**Expected**: 0-2 trades in first week, 5-10 trades in second week

---

## 💰 Cost Analysis

### Current Strategy (Option 1): **$0/month**

**Pros**:
- ✅ Zero cost
- ✅ Tests real production conditions
- ✅ Proves system works before investing

**Cons**:
- ⚠️ 7-14 day ramp-up period
- ⚠️ Cannot backtest until 30+ days of data

---

### Future Upgrade (Option 2): **$29-50/month**

**When to Consider**: After 30-day checkpoint, if win rate > 60%

**Providers**:
- **Polygon.io** ($29/month starter): Real-time + historical data, WebSocket support
- **Alpha Vantage Premium** ($50/month): Unlimited API calls, full historical intraday

**Benefits**:
- ✅ Immediate backfilling (60+ days in 1 hour)
- ✅ Walk-forward testing
- ✅ Parameter optimization
- ✅ Monte Carlo simulations

**Decision Rule**: Only upgrade if paper trading shows consistent profitability

---

## 🚀 Next Steps

### Immediate (Today)

1. ✅ **Monitor BTC DAG**: Check that it starts running successfully (fixed market hours)
2. ✅ **Run daily health check**: `./check_data_status.sh`
3. ✅ **Review Airflow UI**: http://localhost:8080 - check for any errors

### Week 1

4. **Daily monitoring**: Run `check_data_status.sh` once per day
5. **Document observations**: Note any errors, unexpected behavior
6. **Be patient**: Expect 0-2 trades (low confidence is normal)

### Week 2

7. **Check technical analysis activation**: Verify 100+ bars accumulated
8. **Monitor trade execution**: Should see 5-10 trades as confidence increases
9. **Review trade decisions**: Check Airflow logs for decision rationale

### Week 4 (Day 30 Checkpoint)

10. **Run performance analysis**: Calculate win rate, returns, drawdown
11. **Make upgrade decision**: Compare results to validation criteria
12. **Plan next phase**: Live trading prep or extended paper trading

---

## 📚 References

- **Paper Trading Analysis Report**: See conversation history (2025-11-26)
- **Backtest Validation**: Run #8 - TSLA 91.2% win rate, 8.51% return
- **ADR-010**: Airflow Orchestration Strategy
- **ADR-007**: Data Collection & Backtesting Architecture

---

## 💡 Pro Tips

1. **Don't panic if no trades in first week** - This is expected and correct behavior. Low confidence means the system is working properly.

2. **Check database growth daily** - Market bars should increase by ~78 (TSLA), ~26 (IWM), ~24 (BTC) per day.

3. **Monitor sentiment vs technical weight** - Early days: 100% sentiment. Day 7+: 60% sentiment, 40% technical.

4. **Review failed DAG runs** - Some failures are expected (API rate limits, temporary network issues). > 5% failure rate indicates a problem.

5. **Save logs for analysis** - After 30 days, you'll want to review decision logs for strategy optimization.

---

**Last Updated**: 2025-11-26
**Strategy**: Organic Data Accumulation
**Status**: ✅ Active - Day 1 of 30
