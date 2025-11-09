# Ztrade Dashboard Guide

Complete guide to using the Ztrade real-time monitoring dashboard.

---

## Overview

The Ztrade Dashboard is a web-based real-time monitoring interface built with Streamlit. It provides comprehensive visibility into your autonomous trading system with auto-refresh capabilities.

**Access URL**: http://localhost:8501

---

## Features

### 📊 Company Overview
- Account equity and cash balance
- Buying power
- Active agent count
- Trading status

### 🤖 Agent Status
- Real-time status for all agents
- Allocated capital per agent
- P&L tracking (today)
- Trade count
- Current positions per agent

### 📈 Open Positions
- All open positions across agents
- Entry price, current price, and market value
- Unrealized P&L in dollars and percentage
- Total portfolio metrics

### 📊 P&L Charts
- Interactive bar chart comparing agent performance
- Visual representation of winners and losers
- Easy identification of best/worst performers

### 💭 Sentiment Tracking
- Real-time sentiment for each asset
- Multi-source aggregated scores
- Confidence levels and source agreement
- Visual gauge charts (-1 to +1 scale)

### ⚠️ Risk Monitoring
- Capital utilization percentage
- Daily P&L as percentage of capital
- Open positions count
- Risk rule compliance status (RULE_001, RULE_002, RULE_006)
- Real-time alerts for rule violations

### 📝 Recent Activity
- Today's trading decisions
- Timestamp, agent, action, and confidence
- Last 5 decisions shown

---

## Starting the Dashboard

### Quick Start

```bash
# Using the launch script
./run_dashboard.sh

# Or manually
uv run streamlit run dashboard.py
```

The dashboard will automatically open in your browser at http://localhost:8501

### Background Mode

```bash
# Start in background
uv run streamlit run dashboard.py --server.headless=true &

# Stop background dashboard
pkill -f streamlit
```

---

## Dashboard Controls

### Sidebar Settings

**Auto-refresh Toggle**
- Enabled by default
- Refreshes data every 30 seconds
- Toggle off for manual control

**Manual Refresh Button**
- Click "🔄 Refresh Now" to manually update data
- Clears cache and reloads all information

**Quick Links**
- Flower Dashboard: http://localhost:5555 (Celery monitoring)
- Alpaca Dashboard: https://app.alpaca.markets/paper/dashboard/overview

---

## Data Refresh

### Automatic Refresh
- Dashboard auto-refreshes every 30 seconds when enabled
- Data is cached for 30 seconds using `@st.cache_data`
- Prevents excessive API calls while maintaining freshness

### Manual Refresh
- Click the "🔄 Refresh Now" button in the sidebar
- Clears all cached data
- Forces immediate reload of all metrics

---

## Understanding the Metrics

### Account Equity
Total value of your trading account (cash + positions)

### Buying Power
Amount available for new trades (includes margin)

### Capital Utilization
Percentage of total capital allocated to agents
- **Normal**: < 80%
- **Warning**: 80-100%
- **Critical**: > 100%

### Daily P&L %
Today's profit/loss as percentage of total capital
- **Normal**: > -2%
- **Warning**: -2% to -5%
- **Critical**: < -5%

### Sentiment Score
Aggregated sentiment from news, Reddit, and SEC filings
- **Bearish**: -1.0 to -0.3
- **Neutral**: -0.3 to 0.3
- **Bullish**: 0.3 to 1.0

### Risk Rule Status
- **✅ PASS**: Rule is satisfied
- **❌ FAIL**: Rule is violated (trading may be blocked)

---

## Troubleshooting

### Dashboard Won't Start

```bash
# Check if port 8501 is in use
lsof -i :8501

# Kill existing streamlit processes
pkill -f streamlit

# Try starting again
./run_dashboard.sh
```

### "Error loading data"

**Check broker connection:**
```bash
uv run python -c "from cli.utils.broker import get_broker; print(get_broker().get_account_info())"
```

**Check environment variables:**
```bash
cat .env | grep ALPACA
```

### Slow Performance

**Install Watchdog for better file watching:**
```bash
xcode-select --install
uv pip install watchdog
```

**Disable auto-refresh:**
- Uncheck "Auto-refresh (30s)" in sidebar
- Use manual refresh when needed

### Missing Data

**Agent data not showing:**
- Verify agents are configured: `uv run ztrade agent list`
- Check agent state files exist: `ls -la agents/*/state.json`

**Sentiment data missing:**
- Check API credentials (Reddit, Alpaca)
- Market may be closed (sentiment requires recent data)

---

## Best Practices

### 1. Keep Dashboard Open During Trading Hours
Monitor real-time performance and risk metrics continuously during active trading.

### 2. Watch Risk Monitoring Section
Pay special attention to:
- Capital utilization approaching 80%
- Daily P&L approaching -2%
- Any risk rule failures

### 3. Review Sentiment Regularly
- Compare sentiment across assets
- Look for divergence between sentiment and price action
- Use as confirmation for agent decisions

### 4. Monitor Agent Performance
- Identify underperforming agents
- Review decision logs for agents with losses
- Adjust strategies based on patterns

### 5. Use in Combination with Flower
- Dashboard: High-level business metrics
- Flower: Low-level task and worker monitoring
- Together: Complete system visibility

---

## Customization

### Change Auto-Refresh Interval

Edit `dashboard.py`:

```python
@st.cache_data(ttl=30)  # Change 30 to desired seconds
def load_dashboard_data():
    ...
```

### Modify Dashboard Layout

The dashboard uses Streamlit columns:

```python
col1, col2, col3 = st.columns(3)  # Change number for different layouts
```

### Add New Sections

1. Create new render function:
```python
def render_my_section(data):
    st.markdown('<h2>My Section</h2>', unsafe_allow_html=True)
    # Your code here
```

2. Add to main():
```python
render_my_section(data)
st.markdown("---")
```

### Change Color Scheme

Edit CSS in `st.markdown()` at the top of `dashboard.py`:

```python
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #YOUR_COLOR_1 0%, #YOUR_COLOR_2 100%);
    }
</style>
""", unsafe_allow_html=True)
```

---

## Performance Tips

### 1. Data Caching
- Dashboard caches data for 30 seconds
- Reduces API calls and improves speed
- Adjust `ttl` parameter if needed

### 2. Limit Historical Data
- Recent activity shows last 5 decisions
- Increase/decrease based on needs
- More data = slower loading

### 3. Disable Unused Sections
Comment out sections you don't need in `main()`:

```python
# render_sentiment_tracking(data)  # Disabled
```

---

## Keyboard Shortcuts

Streamlit supports these shortcuts:

- `R` - Rerun the app (same as refresh button)
- `C` - Clear cache
- `?` - Show keyboard shortcuts help

---

## Integration with Other Tools

### With Celery/Flower
- Dashboard shows business metrics
- Flower shows technical metrics
- Use both for complete monitoring

### With CLI Commands
- Dashboard for monitoring
- CLI for control and management
- Example: `uv run ztrade agent run agent_spy` while watching dashboard

### With Logs
- Dashboard shows summary
- Logs show detailed decisions
- Example: `tail -f logs/agent_decisions/YYYY-MM-DD/agent_spy.log`

---

## Security Notes

### Production Deployment

**Never expose dashboard to public internet without:**
1. Authentication (Streamlit doesn't include auth by default)
2. HTTPS encryption
3. Firewall rules
4. VPN or IP whitelist

**For local use only:**
- Dashboard binds to localhost by default
- Only accessible from your machine
- Safe for development and testing

---

## Support

**For issues:**
1. Check troubleshooting section above
2. Review streamlit logs in terminal
3. Check system logs: `cat logs/system/YYYY-MM-DD.log`
4. File issue at: https://github.com/anthropics/claude-code/issues

---

## Future Enhancements

**Planned Features:**
- Historical P&L charts (7-day, 30-day trends)
- Trade execution timeline
- Custom alerts and notifications
- Export data to CSV/Excel
- Dark mode toggle
- Mobile-responsive design
- Performance analytics deep-dive
- Backtesting results visualization
- Multi-timeframe analysis

**Under Consideration:**
- User authentication
- Multi-user support
- Email/SMS alerts
- Integration with TradingView
- Advanced charting with technical indicators
- Real-time trade execution from dashboard
