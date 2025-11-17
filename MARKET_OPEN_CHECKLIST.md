# Market Open Checklist - Paper Trading Test

**Date**: Monday, November 18, 2025
**Market Open**: 9:30 AM ET
**Test Duration**: Full trading day (9:30 AM - 4:00 PM ET)
**Mode**: Paper Trading (Dry-Run)
**Agents**: agent_tsla, agent_iwm

---

## ✅ Pre-Flight Validation Complete

All systems tested and verified (2025-11-16 23:50):
- ✅ Market data fetching (Alpaca API)
- ✅ Technical analysis pipeline
- ✅ Multi-source sentiment aggregation (News, Reddit, SEC)
- ✅ Agent configuration loading
- ✅ Full decision cycle integration
- ✅ Risk validation logic

---

## 📋 Market Open Procedure

### T-30 Minutes (9:00 AM ET)

1. **Run Pre-Flight Check**
   ```bash
   cd /Users/aboros/Ztrade
   uv run python preflight_check.py
   ```
   - Verify all checks pass
   - Confirm market data is flowing (bars available)
   - Check sentiment sources are responding

2. **Verify API Connectivity**
   ```bash
   uv run ztrade company status
   ```
   - Confirm Alpaca API connected
   - Verify paper trading account accessible
   - Check account balance

### T-15 Minutes (9:15 AM ET)

3. **Test Agent Decision Cycle (Dry-Run)**
   ```bash
   # Test TSLA agent
   uv run ztrade agent run agent_tsla --subagent --dry-run

   # Test IWM agent
   uv run ztrade agent run agent_iwm --subagent --dry-run
   ```
   - Verify agents can fetch market data
   - Confirm sentiment analysis works
   - Check technical indicators calculated
   - Review decision-making logic

### T-0 Minutes (9:30 AM ET - Market Open)

4. **Start Trading Loops**

   **Option A: Individual Agents (Recommended for first test)**
   ```bash
   # Terminal 1: TSLA agent
   uv run ztrade loop start agent_tsla --interval 300

   # Terminal 2: IWM agent
   uv run ztrade loop start agent_iwm --interval 900
   ```

   **Option B: Celery Orchestration (Advanced)**
   ```bash
   ./celery_control.sh start
   # Monitor at http://localhost:5555
   ```

5. **Start Dashboard**
   ```bash
   # Terminal 3: Dashboard
   ./run_dashboard.sh
   # View at http://localhost:8501
   ```

---

## 🔍 Monitoring During Market Hours

### Every Hour (10:30 AM, 11:30 AM, 12:30 PM, 1:30 PM, 2:30 PM, 3:30 PM)

1. **Check Agent Status**
   ```bash
   uv run ztrade agent status agent_tsla
   uv run ztrade agent status agent_iwm
   ```

2. **Review Loop State**
   ```bash
   uv run ztrade loop status
   ```

3. **Monitor Logs**
   ```bash
   tail -50 logs/decisions/agent_tsla_*.log
   tail -50 logs/decisions/agent_iwm_*.log
   ```

4. **Check Dashboard**
   - Open http://localhost:8501
   - Review agent performance
   - Check trade decisions
   - Monitor sentiment trends

### Watch For

**🟢 Good Signs:**
- Agents making decisions based on complete data (TA + sentiment)
- Clear reasoning in decision logs
- Risk validation passing
- No errors in logs

**🔴 Red Flags:**
- Repeated errors fetching market data
- Sentiment sources timing out
- Risk validation failures
- Missing bars/indicators

---

## 📊 What to Observe

### Agent Decisions
- **Entry Signals**: Are they triggered by sentiment + TA confirmation?
- **Exit Signals**: Stop loss vs take profit hits
- **Hold Decisions**: When confidence is low or signals conflict

### Sentiment Analysis
- **News Source**: Are we getting TSLA/IWM news?
- **Reddit**: Are mentions being captured?
- **SEC**: Are filings being analyzed?
- **Agreement**: Do sources agree or conflict?

### Technical Analysis
- **RSI**: Is it calculated correctly from bars?
- **SMA**: Are 50/200 period SMAs reasonable?
- **Trend**: Does it match visual chart inspection?
- **Volume**: Is volume data available?

### Integration
- **Complete Context**: Each decision has market data + sentiment + TA
- **Personality**: Agent follows its personality guidelines
- **Risk Management**: Position sizing, stop loss, take profit enforced

---

## 🛑 Stop Conditions

**Stop trading immediately if:**
1. ❌ Repeated API errors (>3 consecutive failures)
2. ❌ Missing critical data (no bars, no quotes)
3. ❌ Sentiment sources all failing
4. ❌ Risk validation not working
5. ❌ Unexpected trade executions (should be dry-run only!)

**How to Stop:**
```bash
# Stop loops
uv run ztrade loop stop agent_tsla
uv run ztrade loop stop agent_iwm

# Or stop Celery
./celery_control.sh stop
```

---

## 📝 Data to Collect

### Decision Logs
Location: `logs/decisions/`
- agent_tsla decisions
- agent_iwm decisions
- Timestamp, price, signals, reasoning

### Performance Metrics
Track manually or via dashboard:
- Number of decisions made
- Buy/Sell/Hold distribution
- Sentiment score ranges
- Technical signal distribution
- Decision confidence levels

### Issues Encountered
Document in a notes file:
- API timeouts
- Data gaps
- Unexpected behavior
- Performance bottlenecks

---

## 🐛 Common Issues & Fixes

### No Bars Available
**Symptom**: "No historical data available"
**Fix**:
- Check if market is open
- Verify Alpaca API key has market data access
- Try different timeframe (5m vs 15m vs 1h)

### Sentiment Sources Failing
**Symptom**: "No sentiment data available"
**Fix**:
- Check API rate limits (Alpaca News, Reddit, SEC)
- Verify credentials in `.env`
- Fall back to single source if needed

### Agent Not Making Decisions
**Symptom**: Only "HOLD" decisions
**Fix**:
- Check min_confidence threshold (may be too high)
- Verify sentiment data is flowing
- Review technical indicators (may need more bars)

### Loop Stopped Unexpectedly
**Symptom**: Loop status shows "stopped"
**Fix**:
- Check logs for errors: `logs/system/ztrade_*.log`
- Restart loop manually
- Verify no timeout issues

---

## 📈 Success Criteria

By end of day, we should have:
1. ✅ **Complete Decision Logs**: All trading hours covered
2. ✅ **No Critical Errors**: System stayed online
3. ✅ **Integrated Decisions**: Each decision used TA + sentiment
4. ✅ **Risk Validation**: All trades within risk limits
5. ✅ **Personality Adherence**: Agents followed their strategies

---

## 🔄 End of Day Procedure (4:00 PM ET)

1. **Stop All Loops**
   ```bash
   uv run ztrade loop stop agent_tsla
   uv run ztrade loop stop agent_iwm
   # Or: ./celery_control.sh stop
   ```

2. **Review Performance**
   ```bash
   uv run ztrade agent status agent_tsla --verbose
   uv run ztrade agent status agent_iwm --verbose
   ```

3. **Analyze Decision Logs**
   ```bash
   # Count total decisions
   wc -l logs/decisions/agent_tsla_*.log
   wc -l logs/decisions/agent_iwm_*.log

   # Check for errors
   grep -i error logs/system/ztrade_*.log
   ```

4. **Generate Summary Report**
   - Total decisions made
   - Sentiment vs TA agreement rate
   - Most common decision type (buy/sell/hold)
   - Issues encountered
   - Improvements needed

---

## 🎯 Next Steps (Based on Results)

### If Successful (No Major Issues)
- ✅ Continue paper trading for 2-4 weeks
- ✅ Start collecting performance metrics
- ✅ Consider adding ETH agent
- ✅ Fine-tune confidence thresholds

### If Issues Found
- ❌ Fix critical bugs before continuing
- ❌ Improve error handling
- ❌ Add more logging/monitoring
- ❌ Re-test with fixes before resuming

---

## 📞 Quick Reference Commands

```bash
# Pre-flight check
uv run python preflight_check.py

# Company status
uv run ztrade company status

# Start agent (dry-run)
uv run ztrade agent run agent_tsla --subagent --dry-run

# Start loop
uv run ztrade loop start agent_tsla --interval 300

# Check status
uv run ztrade agent status agent_tsla
uv run ztrade loop status

# Stop loop
uv run ztrade loop stop agent_tsla

# View logs
tail -f logs/decisions/agent_tsla_*.log
tail -f logs/system/ztrade_*.log

# Dashboard
./run_dashboard.sh
# http://localhost:8501

# Celery (alternative)
./celery_control.sh start
./celery_control.sh status
./celery_control.sh stop
# http://localhost:5555
```

---

## ⚠️ Important Reminders

1. **This is PAPER TRADING** - No real money at risk
2. **Dry-run mode enabled** - Trades are simulated, not executed
3. **Monitor actively** - Don't leave unattended for first test
4. **Take notes** - Document everything for post-analysis
5. **BTC agent disabled** - Crypto support needs more work, test later

---

## 🎉 Good Luck!

You've built an impressive sentiment-driven trading system. Tomorrow is the first live test of the complete integrated pipeline:
- ✅ Real-time market data
- ✅ Multi-source sentiment analysis
- ✅ Technical indicators
- ✅ AI-driven decision making
- ✅ Risk management
- ✅ Agent personalities

**Remember**: The goal is to validate the system works end-to-end, not to make profitable trades (yet!). Focus on observing how all the pieces work together.

---

**Last Updated**: 2025-11-16 23:50 ET
**Prepared By**: Claude Code
**System Status**: ✅ READY FOR PAPER TRADING
