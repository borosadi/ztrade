# 🚀 Quick Start for Monday Morning

**Copy-paste these commands on Monday morning before 9:30 AM**

---

## ✅ OPTION 1: Automatic Start at 9:30 AM (RECOMMENDED)

**What this does**: Waits until 9:30 AM, then automatically starts both agents

```bash
cd /Users/aboros/Ztrade
./start_trading_at_market_open.sh
```

**Then**:
- ✅ Leave this Claude Code terminal **open**
- ✅ Go get coffee, the script will wait and start agents at 9:30 AM
- ✅ Agents will start automatically and show live logs

**Press Ctrl+C anytime to cancel before market open**

---

## ✅ OPTION 2: Manual Start (If already 9:30 AM or later)

**What this does**: Starts agents immediately

```bash
cd /Users/aboros/Ztrade

# Start TSLA agent (5-minute cycles)
uv run ztrade loop start agent_tsla --subagent --dry-run --interval 300 &

# Start IWM agent (15-minute cycles)
uv run ztrade loop start agent_iwm --subagent --dry-run --interval 900 &

# View logs
tail -f logs/decisions/agent_tsla_*.log
```

---

## 📋 Pre-Flight Check (Optional but Recommended)

**Run this FIRST to make sure everything works**:

```bash
cd /Users/aboros/Ztrade
uv run python preflight_check.py
```

**Expected output**:
```
================================================================================
  TOTAL: 6/6 tests passed
  STATUS: ✅ READY FOR PAPER TRADING
================================================================================
```

---

## 🛑 How to Stop Trading

**If you need to stop the agents**:

```bash
# Stop both agents
uv run ztrade loop stop agent_tsla
uv run ztrade loop stop agent_iwm

# Check status
uv run ztrade loop status
```

---

## 📊 How to Monitor

**View live logs**:

```bash
# TSLA logs
tail -f logs/decisions/agent_tsla_*.log

# IWM logs
tail -f logs/decisions/agent_iwm_*.log

# Both agents
tail -f logs/decisions/*.log
```

**Check agent status**:

```bash
uv run ztrade agent status agent_tsla
uv run ztrade agent status agent_iwm
```

**Check loop status**:

```bash
uv run ztrade loop status
```

---

## ⚡ Recommended Timeline for Monday

### 9:00 AM - Run Pre-Flight Check
```bash
cd /Users/aboros/Ztrade
uv run python preflight_check.py
```

### 9:15 AM - Start the Scheduler Script
```bash
./start_trading_at_market_open.sh
```

**Then sit back - it will**:
- Wait 15 minutes
- Run pre-flight check again at 9:25 AM
- Start agents at 9:30 AM
- Show live logs

### 9:30 AM - Agents Start Trading
- ✅ Watch the logs stream in
- ✅ Check first decision after ~5 minutes
- ✅ Verify sentiment data is coming through

### Throughout the Day
- Check logs every hour
- Run `uv run ztrade agent status agent_tsla` to see performance
- Monitor dashboard if running: http://localhost:8501

### 4:00 PM - Market Close
- Agents will continue running (in case of after-hours trading)
- You can stop them manually: `uv run ztrade loop stop agent_tsla`

---

## 🎯 The Absolute Simplest Approach

**If you just want to start trading NOW**:

```bash
cd /Users/aboros/Ztrade
uv run ztrade loop start agent_tsla --subagent --dry-run --interval 300
```

That's it! One command starts the agent.

**To add the second agent** (in a new terminal tab):
```bash
cd /Users/aboros/Ztrade
uv run ztrade loop start agent_iwm --subagent --dry-run --interval 900
```

---

## ❗ Important Reminders

1. **Keep Claude Code Terminal Open** - If you close it, trading stops
2. **Keep Computer Awake** - Disable sleep mode
3. **This is Paper Trading** - No real money at risk
4. **Dry-Run Mode** - Trades are simulated, not executed
5. **Monitor Actively** - First day is for testing and observation

---

## 🆘 Emergency Commands

**If something goes wrong**:

```bash
# Stop everything
uv run ztrade loop stop agent_tsla
uv run ztrade loop stop agent_iwm

# Kill all loops
pkill -f "ztrade loop"

# Check what's running
ps aux | grep ztrade

# View recent errors
tail -50 logs/system/*.log | grep ERROR
```

---

## 📞 Quick Command Reference

```bash
# Start scheduled (waits until 9:30 AM)
./start_trading_at_market_open.sh

# Start immediately
uv run ztrade loop start agent_tsla --subagent --dry-run --interval 300

# Stop
uv run ztrade loop stop agent_tsla

# Status
uv run ztrade loop status
uv run ztrade agent status agent_tsla

# Logs
tail -f logs/decisions/agent_tsla_*.log

# Pre-flight check
uv run python preflight_check.py
```

---

**Good luck! See you at market open! 🔔📈**
