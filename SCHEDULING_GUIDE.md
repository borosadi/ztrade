# Trading Schedule Automation Guide

**Goal**: Automatically start trading agents at market open (9:30 AM ET) using subagent mode in Claude Code terminal.

---

## ⚠️ Important: Subagent Mode Requirements

**For subagent mode to work, you MUST**:
- ✅ Keep Claude Code terminal window **open and active**
- ✅ Keep your computer **awake** (don't let it sleep)
- ✅ Keep Claude Code **connected** to the session

**If any of these break**: Trading will stop immediately.

**Recommendation**: For unattended trading, use `--automated` mode instead (requires `ANTHROPIC_API_KEY`).

---

## 🚀 Option 1: Simple Script (RECOMMENDED for Subagent Mode)

**Best for**: Running once on Monday morning in this terminal

### Usage:

```bash
# Navigate to project
cd /Users/aboros/Ztrade

# Run the script (will wait until 9:30 AM, then start agents)
./start_trading_at_market_open.sh
```

### What it does:
1. ✅ Calculates time until market open (9:30 AM ET)
2. ✅ Waits automatically (you can leave it running)
3. ✅ Runs pre-flight check 5 minutes before open
4. ✅ Starts both agents at exactly 9:30 AM
5. ✅ Shows live logs from both agents

### Example:

```bash
$ ./start_trading_at_market_open.sh

╔════════════════════════════════════════════════════════════╗
║   Ztrade - Automatic Market Open Trading Starter          ║
╚════════════════════════════════════════════════════════════╝

Current time: 08:45
Current day: Monday
Trading mode: subagent

⏰ Scheduled Start Time: 9:30 AM ET
Time until market open: 0h 45m

═══════════════════════════════════════════════════════════
At 9:30 AM ET, the following agents will start:

  🚗 agent_tsla (TESLA)
     - Strategy: Sentiment-driven momentum
     - Timeframe: 5-minute bars
     - Interval: Every 5 minutes (300 seconds)

  📊 agent_iwm (Russell 2000 Small-Caps)
     - Strategy: Small-cap sentiment momentum
     - Timeframe: 15-minute bars
     - Interval: Every 15 minutes (900 seconds)

═══════════════════════════════════════════════════════════

Waiting until market open...
(You can press Ctrl+C to cancel)

# ... waits 40 minutes ...

⚠️  5 minutes until market open!
Running pre-flight checks...

# ... runs preflight_check.py ...

Waiting final 5 minutes...

╔════════════════════════════════════════════════════════════╗
║              🔔 MARKET IS OPEN! 🔔                         ║
╚════════════════════════════════════════════════════════════╝

Starting trading agents...
✅ Trading agents started!

# ... shows live logs ...
```

### To use automated mode instead:

```bash
./start_trading_at_market_open.sh --automated
```

---

## 🕐 Option 2: macOS launchd (Advanced)

**Best for**: Automatic daily startup (computer must be on and logged in)

⚠️ **WARNING**: This will ONLY work with `--automated` mode, NOT subagent mode, because launchd runs in background without a terminal.

### Setup:

```bash
# 1. Copy the plist file to LaunchAgents
cp /Users/aboros/Ztrade/com.ztrade.marketopen.plist ~/Library/LaunchAgents/

# 2. Load the schedule
launchctl load ~/Library/LaunchAgents/com.ztrade.marketopen.plist

# 3. Verify it's loaded
launchctl list | grep ztrade
```

### How it works:
- Runs Monday-Friday at 9:25 AM
- Waits 5 minutes, then starts agents at 9:30 AM
- Logs to `/Users/aboros/Ztrade/logs/launchd_*.log`

### To unload:

```bash
launchctl unload ~/Library/LaunchAgents/com.ztrade.marketopen.plist
```

**LIMITATION**: launchd runs in background, so subagent mode won't work. You must modify the script to use `--automated` instead.

---

## ⏰ Option 3: Manual Start with `at` Command

**Best for**: One-time scheduled start on Monday

### Usage:

```bash
# Schedule for 9:30 AM today
echo "cd /Users/aboros/Ztrade && ./start_trading_at_market_open.sh" | at 09:30

# Schedule for specific date/time
echo "cd /Users/aboros/Ztrade && ./start_trading_at_market_open.sh" | at 09:30 Nov 18

# Check scheduled jobs
atq

# Remove a scheduled job
atrm <job_number>
```

**LIMITATION**: macOS often disables `at` by default. You may need to enable it:

```bash
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.atrun.plist
```

---

## 🎯 RECOMMENDED Approach for Monday (Subagent Mode)

Since you want to use **subagent mode in this Claude Code terminal**, here's the best approach:

### Sunday Night or Monday Morning:

1. **Open Claude Code terminal** (this chat)

2. **Navigate to project**:
   ```bash
   cd /Users/aboros/Ztrade
   ```

3. **Run the scheduler script**:
   ```bash
   ./start_trading_at_market_open.sh
   ```

4. **Leave terminal open** - The script will:
   - Wait until 9:30 AM
   - Run pre-flight checks at 9:25 AM
   - Start both agents at 9:30 AM
   - Show live logs

5. **Monitor throughout the day** - Logs will stream in terminal

### Important Reminders:

- ✅ Keep Claude Code terminal **open**
- ✅ Keep your **computer awake** (disable sleep)
- ✅ Don't **disconnect** from Claude Code
- ✅ Keep this **session active**

---

## 🔄 Alternative: Use Automated Mode Instead

If you want true "set it and forget it" scheduling, consider using **automated mode**:

### Setup (one-time):

```bash
# 1. Get API key from https://console.anthropic.com/
# 2. Add to .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env

# 3. Install SDK (already done)
uv pip install anthropic
```

### Then use ANY scheduling method:

```bash
# Simple script (will work in background)
./start_trading_at_market_open.sh --automated

# Or cron (edit crontab)
crontab -e
# Add: 30 9 * * 1-5 cd /Users/aboros/Ztrade && uv run ztrade loop start agent_tsla --automated --dry-run --interval 300

# Or launchd (already configured above)
```

**Benefits**:
- ✅ Can close terminal
- ✅ Computer can sleep/wake
- ✅ More reliable for daily operation

**Cost**: ~$5-10 per full trading day

---

## 📋 Quick Reference

| Method | Terminal Must Stay Open? | Computer Must Stay Awake? | Subagent Mode? | Setup Complexity |
|--------|-------------------------|---------------------------|----------------|------------------|
| **Simple Script** | ✅ Yes | ✅ Yes | ✅ Yes | ⭐ Easy |
| **launchd** | ❌ No | ⚠️ Yes (logged in) | ❌ No (use automated) | ⭐⭐ Medium |
| **at command** | ✅ Yes | ✅ Yes | ✅ Yes | ⭐⭐ Medium |
| **Automated Mode + Any** | ❌ No | ❌ No | ❌ No (uses API) | ⭐ Easy |

---

## 🧪 Test the Script Now

You can test the script right now (it will show a countdown):

```bash
cd /Users/aboros/Ztrade

# Test run (will calculate time to market open)
./start_trading_at_market_open.sh

# If it's after market hours, it will tell you when next market open is
# If it's the weekend, it will offer to wait until Monday

# Press Ctrl+C to cancel anytime
```

---

## 🎯 For Monday Morning

**Simplest approach**:

```bash
# Sunday night or Monday morning (anytime before 9:30 AM):

cd /Users/aboros/Ztrade
./start_trading_at_market_open.sh

# Then leave this terminal open and go about your day
# Agents will start at 9:30 AM automatically
```

**Alternative if you have API key**:

```bash
# Same script, but with automated mode (can close terminal after):

./start_trading_at_market_open.sh --automated
```

---

## 💡 Pro Tips

1. **Keep Terminal Visible**: Open Claude Code in a separate window you can monitor
2. **Use tmux/screen**: If you're comfortable with terminal multiplexers
3. **Set Computer to Not Sleep**: System Preferences → Energy Saver → Prevent sleep
4. **Test Today**: Run the script now to see how it works (Ctrl+C to cancel)
5. **Have Backup**: Know how to manually start if script fails: `uv run ztrade loop start agent_tsla --subagent --dry-run --interval 300`

---

## 🚨 Troubleshooting

### "Permission denied"
```bash
chmod +x start_trading_at_market_open.sh
```

### "Script starts but agents don't run"
- Make sure you're in Claude Code terminal
- Check logs: `tail -f logs/system/*.log`
- Try manual start: `uv run ztrade agent run agent_tsla --subagent --dry-run`

### "Can't use launchd with subagent"
- Correct! launchd needs `--automated` mode
- Modify script: `./start_trading_at_market_open.sh --automated`
- Or just use the simple script approach in this terminal

---

**Last Updated**: 2025-11-17 00:30 ET
**Recommended**: Use simple script in Claude Code terminal
**Alternative**: Use automated mode for true background operation
