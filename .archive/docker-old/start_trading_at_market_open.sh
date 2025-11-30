#!/bin/bash
#
# Automatic Market Open Trading Starter
# Waits until market opens (9:30 AM ET), then starts trading agents
#
# Usage:
#   ./start_trading_at_market_open.sh
#   or
#   ./start_trading_at_market_open.sh --automated  # for automated mode instead

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default mode
MODE="subagent"
if [ "$1" == "--automated" ]; then
    MODE="automated"
fi

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Ztrade - Automatic Market Open Trading Starter          ║${NC}"
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Get current time
CURRENT_TIME=$(date +%H:%M)
CURRENT_DAY=$(date +%u)  # 1=Monday, 7=Sunday

echo "Current time: $CURRENT_TIME"
echo "Current day: $(date +%A)"
echo "Trading mode: $MODE"
echo ""

# Market open time (9:30 AM ET)
MARKET_OPEN_HOUR=9
MARKET_OPEN_MIN=30

# Check if it's a weekend
if [ "$CURRENT_DAY" -ge 6 ]; then
    echo -e "${YELLOW}⚠️  It's the weekend! Market is closed.${NC}"
    echo ""
    echo "Next market open:"
    if [ "$CURRENT_DAY" -eq 6 ]; then
        echo "  Monday at 9:30 AM ET (in ~$(( (2*24*60) + (9*60+30) - $(date +%H)*60 - $(date +%M) )) minutes)"
    else
        echo "  Monday at 9:30 AM ET (in ~$(( (1*24*60) + (9*60+30) - $(date +%H)*60 - $(date +%M) )) minutes)"
    fi
    echo ""
    read -p "Do you want to wait until Monday? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Run this script on Monday morning."
        exit 0
    fi
fi

# Calculate seconds until market open
NOW_SECONDS=$(( $(date +%H) * 3600 + $(date +%M) * 60 + $(date +%S) ))
MARKET_OPEN_SECONDS=$(( MARKET_OPEN_HOUR * 3600 + MARKET_OPEN_MIN * 60 ))
SECONDS_TO_WAIT=$(( MARKET_OPEN_SECONDS - NOW_SECONDS ))

# If market open time has passed today, wait until tomorrow
if [ $SECONDS_TO_WAIT -lt 0 ]; then
    SECONDS_TO_WAIT=$(( 86400 + SECONDS_TO_WAIT ))  # Add 24 hours
    echo -e "${YELLOW}Market has already closed for today.${NC}"
    echo "Will start at tomorrow's market open (9:30 AM ET)"
fi

# Convert to hours and minutes
HOURS_TO_WAIT=$(( SECONDS_TO_WAIT / 3600 ))
MINUTES_TO_WAIT=$(( (SECONDS_TO_WAIT % 3600) / 60 ))

echo -e "${GREEN}⏰ Scheduled Start Time: 9:30 AM ET${NC}"
echo "Time until market open: ${HOURS_TO_WAIT}h ${MINUTES_TO_WAIT}m"
echo ""

# Show what will happen
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo "At 9:30 AM ET, the following agents will start:"
echo ""
echo "  🚗 agent_tsla (TESLA)"
echo "     - Strategy: Sentiment-driven momentum"
echo "     - Timeframe: 5-minute bars"
echo "     - Interval: Every 5 minutes (300 seconds)"
echo ""
echo "  📊 agent_iwm (Russell 2000 Small-Caps)"
echo "     - Strategy: Small-cap sentiment momentum"
echo "     - Timeframe: 15-minute bars"
echo "     - Interval: Every 15 minutes (900 seconds)"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Countdown
if [ $HOURS_TO_WAIT -gt 0 ] || [ $MINUTES_TO_WAIT -gt 5 ]; then
    echo "Waiting until market open..."
    echo "(You can press Ctrl+C to cancel)"
    echo ""

    # Sleep until 5 minutes before market open
    SLEEP_SECONDS=$(( SECONDS_TO_WAIT - 300 ))  # Wake up 5 min early
    if [ $SLEEP_SECONDS -gt 0 ]; then
        sleep $SLEEP_SECONDS
    fi

    echo -e "${YELLOW}⚠️  5 minutes until market open!${NC}"
    echo "Running pre-flight checks..."
    echo ""

    # Run pre-flight check
    uv run python preflight_check.py

    echo ""
    echo "Waiting final 5 minutes..."
    sleep 300
fi

# Market is open!
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              🔔 MARKET IS OPEN! 🔔                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Starting trading agents..."
echo ""

# Start agents based on mode
if [ "$MODE" == "automated" ]; then
    echo "Starting agent_tsla in AUTOMATED mode..."
    uv run ztrade loop start agent_tsla --automated --dry-run --interval 300 &
    TSLA_PID=$!

    echo "Starting agent_iwm in AUTOMATED mode..."
    uv run ztrade loop start agent_iwm --automated --dry-run --interval 900 &
    IWM_PID=$!
else
    echo "Starting agent_tsla in SUBAGENT mode..."
    uv run ztrade loop start agent_tsla --subagent --dry-run --interval 300 &
    TSLA_PID=$!

    echo "Starting agent_iwm in SUBAGENT mode..."
    uv run ztrade loop start agent_iwm --subagent --dry-run --interval 900 &
    IWM_PID=$!
fi

echo ""
echo -e "${GREEN}✅ Trading agents started!${NC}"
echo ""
echo "Process IDs:"
echo "  agent_tsla: $TSLA_PID"
echo "  agent_iwm: $IWM_PID"
echo ""
echo "Monitoring commands:"
echo "  View logs: tail -f logs/decisions/agent_tsla_*.log"
echo "  Check status: uv run ztrade loop status"
echo "  Stop agents: uv run ztrade loop stop agent_tsla && uv run ztrade loop stop agent_iwm"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop monitoring (agents will continue running)${NC}"
echo ""

# Monitor the agents
tail -f logs/decisions/agent_tsla_*.log 2>/dev/null &
tail -f logs/decisions/agent_iwm_*.log 2>/dev/null &

# Wait for user interrupt
wait
