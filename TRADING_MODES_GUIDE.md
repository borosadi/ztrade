# Trading Modes Guide - Running Agents Outside Claude Code

## 🎯 Problem Solved

You can now run trading agents in **three different modes** depending on your use case:

1. **Automated Mode** (RECOMMENDED for background/production) - Uses Anthropic API
2. **Subagent Mode** (for development in Claude Code terminal)
3. **Manual Mode** (for interactive testing)

---

## ✅ Automated Mode (Background Trading)

**Use When**: Running agents in the background (Celery, cron, tmux, production)

**Requirements**:
```bash
# 1. Install Anthropic SDK
uv pip install anthropic

# 2. Add API key to .env
echo "ANTHROPIC_API_KEY=your_api_key_here" >> .env

# Get your API key at: https://console.anthropic.com/
```

**Usage**:
```bash
# Single cycle
uv run ztrade agent run agent_tsla --automated --dry-run

# Continuous loop (recommended)
uv run ztrade loop start agent_tsla --automated --interval 300
```

**How It Works**:
- ✅ Agent makes decisions using Anthropic API (Claude 3.5 Sonnet)
- ✅ Runs completely autonomously
- ✅ No Claude Code terminal required
- ✅ Perfect for background processes (Celery, cron, tmux)
- ✅ Uses same personality and context as subagent mode

**Cost**: ~$0.003 per decision (~$3 for 1000 decisions)

---

## 🔧 Subagent Mode (Development in Claude Code)

**Use When**: Testing within Claude Code terminal (this chat)

**Requirements**:
- Claude Code terminal running (this chat)
- No API key needed

**Usage**:
```bash
# Single cycle
uv run ztrade agent run agent_tsla --subagent --dry-run

# Continuous loop
uv run ztrade loop start agent_tsla --subagent --interval 300
```

**How It Works**:
- ✅ Agent creates decision request file
- ✅ Claude Code subagent (me!) analyzes and responds
- ✅ File-based communication (no API calls)
- ❌ Requires Claude Code terminal to be running
- ❌ Won't work in background processes

**Cost**: Free (uses your Claude Code session)

**Best For**: Development, testing, learning how agents work

---

## 🧪 Manual Mode (Interactive Testing)

**Use When**: You want to manually review each decision

**Requirements**: None

**Usage**:
```bash
uv run ztrade agent run agent_tsla --manual --dry-run
```

**How It Works**:
1. Agent displays trading context
2. You copy context and ask Claude Code to analyze
3. Claude Code provides JSON decision
4. You paste JSON back into terminal
5. Agent executes (or simulates) trade

**Best For**: Learning, debugging, understanding decisions

---

## 📋 Comparison Table

| Feature | Automated Mode | Subagent Mode | Manual Mode |
|---------|---------------|---------------|-------------|
| **Background Operation** | ✅ Yes | ❌ No (needs terminal) | ❌ No (interactive) |
| **API Key Required** | ✅ Yes | ❌ No | ❌ No |
| **Cost** | ~$3/1000 decisions | Free | Free |
| **Claude Code Terminal** | ❌ Not required | ✅ Required | ✅ Required |
| **Celery/Cron Compatible** | ✅ Yes | ❌ No | ❌ No |
| **Decision Speed** | ~1-2 seconds | ~1-2 seconds | Manual |
| **Production Ready** | ✅ Yes | ❌ No | ❌ No |

---

## 🚀 Recommended Setup for Monday's Test

### Option A: Automated Mode (Best for all-day unattended trading)

```bash
# Set up API key (one time)
export ANTHROPIC_API_KEY="your_api_key_here"
echo "ANTHROPIC_API_KEY=your_api_key_here" >> .env

# Install SDK
uv pip install anthropic

# Start agents (at market open)
uv run ztrade loop start agent_tsla --automated --dry-run --interval 300 &
uv run ztrade loop start agent_iwm --automated --dry-run --interval 900 &

# Monitor logs
tail -f logs/decisions/agent_tsla_*.log
```

**Pros**:
- ✅ Runs all day without your attention
- ✅ Can close terminal and keep running (use `tmux` or `screen`)
- ✅ Production-ready setup

**Cons**:
- ❌ Costs ~$0.003 per decision (~$5-10 for full day)
- ❌ Requires API key setup

---

### Option B: Subagent Mode (Best for learning/testing)

```bash
# No setup needed, just run (in this Claude Code terminal)
uv run ztrade loop start agent_tsla --subagent --dry-run --interval 300
```

**Pros**:
- ✅ Free (uses Claude Code session)
- ✅ No API key needed
- ✅ Great for learning how decisions are made

**Cons**:
- ❌ Must keep Claude Code terminal open all day
- ❌ If terminal closes, trading stops
- ❌ Not suitable for production

---

## 🎯 Quick Start for Monday

### If You Have Anthropic API Key (Recommended):

```bash
# 1. Install SDK
uv pip install anthropic

# 2. Set API key
export ANTHROPIC_API_KEY="your_api_key"

# 3. Test it works
uv run ztrade agent run agent_tsla --automated --dry-run

# 4. At market open (9:30 AM):
uv run ztrade loop start agent_tsla --automated --dry-run --interval 300
```

---

### If You Don't Have API Key (Use Subagent):

```bash
# Must keep Claude Code terminal open all day

# At market open (9:30 AM):
uv run ztrade loop start agent_tsla --subagent --dry-run --interval 300
```

---

## 📊 Celery Integration (Future)

For production deployment with Celery, update `.env`:

```bash
# Required for automated decisions in Celery
ANTHROPIC_API_KEY=your_api_key_here
```

Then update `celery_app.py` beat schedule to use automated mode:

```python
'agent-tsla-trading-cycle': {
    'task': 'ztrade.trading_cycle_automated',  # New task
    'schedule': timedelta(minutes=5),
    'args': ('agent_tsla', False, True),  # (agent_id, dry_run, automated)
}
```

---

## 🔒 Security Notes

1. **NEVER commit API keys** to git
2. **Use .env file** for API keys (already in .gitignore)
3. **Start with dry-run** mode (no real trades)
4. **Monitor logs** for first few days
5. **Set up cost alerts** in Anthropic console

---

## ⚡ Performance Expectations

### Decision Latency:
- Automated Mode: 1-3 seconds per decision
- Subagent Mode: 1-3 seconds per decision
- Manual Mode: As fast as you can copy/paste

### Costs (Automated Mode Only):
- Per Decision: ~$0.003
- Per Hour (12 decisions): ~$0.036
- Per Day (7 hours, 84 decisions): ~$0.25
- Per Month (20 trading days): ~$5.00

---

## 🐛 Troubleshooting

### "Anthropic API not configured"
```bash
# Fix:
uv pip install anthropic
export ANTHROPIC_API_KEY="your_key"
```

### "No response from Claude Code subagent"
```bash
# Fix: Either
# 1. Make sure Claude Code terminal is running, OR
# 2. Switch to automated mode: --automated instead of --subagent
```

### "ERROR: No decision mode specified"
```bash
# Fix: Add one of these flags:
--automated  # For background
--subagent   # For Claude Code terminal
--manual     # For interactive
```

---

## ✅ Pre-Flight Check

Before Monday, verify automated mode works:

```bash
# 1. Install SDK
uv pip install anthropic

# 2. Set key (get from https://console.anthropic.com/)
export ANTHROPIC_API_KEY="your_key_here"

# 3. Test single cycle
uv run ztrade agent run agent_tsla --automated --dry-run

# You should see:
# ✅ Decision received: BUY/SELL/HOLD
# ✅ Confidence: XX%
# ✅ API response time: ~1000ms
```

---

## 📞 Quick Reference

```bash
# Automated mode (background)
uv run ztrade agent run agent_tsla --automated --dry-run

# Subagent mode (Claude Code terminal)
uv run ztrade agent run agent_tsla --subagent --dry-run

# Manual mode (interactive)
uv run ztrade agent run agent_tsla --manual --dry-run

# Continuous loop (automated, recommended for Monday)
uv run ztrade loop start agent_tsla --automated --dry-run --interval 300

# Check status
uv run ztrade loop status
uv run ztrade agent status agent_tsla

# Stop loop
uv run ztrade loop stop agent_tsla
```

---

**Last Updated**: 2025-11-17 00:15 ET
**Ready for**: Monday market open with automated mode ✅
