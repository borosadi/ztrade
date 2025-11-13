# Persona: Dashboard Developer

**Role**: Frontend engineer responsible for all user-facing interfaces and real-time data visualizations.

**When to use this persona**:
- Adding new dashboard features
- Creating charts and visualizations
- Improving dashboard layout and UX
- Fixing UI bugs
- Connecting dashboard to new data sources
- Performance optimization of dashboard
- Adding new metrics displays

---

## Dashboard Overview

**Technology**: Streamlit (Python-based web framework)
**Port**: http://localhost:8501
**Auto-reload**: Yes (development mode)

**Purpose**: Real-time monitoring of:
- Agent statuses and positions
- Company-wide metrics
- Recent trades
- Performance charts
- Risk exposure
- Market sentiment

---

## Quick Start

### Running the Dashboard

```bash
# Development (manual)
uv run streamlit run dashboard.py

# Development (with auto-reload)
./run_dashboard.sh

# Production (Docker)
docker-compose up dashboard
# Dashboard available at http://localhost:8501
```

### File Structure

```
Ztrade/
├── dashboard.py         # Main Streamlit application
├── run_dashboard.sh    # Development startup script
└── docs/guides/dashboard-guide.md  # Comprehensive guide
```

---

## Current Dashboard Features

### 1. Company Overview Section

**Displays**:
- Total portfolio value
- Total P&L ($ and %)
- Cash balance
- Number of active agents
- Number of open positions
- Today's trade count

**Implementation**:
```python
import streamlit as st
from cli.utils.database import get_db_connection

# Company metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Portfolio Value", f"${portfolio_value:,.2f}",
              delta=f"{pnl_pct:+.2f}%")

with col2:
    st.metric("Cash Balance", f"${cash:,.2f}")

with col3:
    st.metric("Active Agents", agent_count)
```

---

### 2. Agent Status Table

**Displays** (for each agent):
- Agent ID
- Asset symbol
- Status (active/paused/error)
- Current position (if any)
- Unrealized P&L
- Today's P&L
- Trade count

**Implementation**:
```python
import pandas as pd

# Fetch agent data
agents_data = fetch_all_agent_statuses()

# Create DataFrame
df = pd.DataFrame(agents_data)

# Display table
st.dataframe(
    df,
    column_config={
        "unrealized_pnl": st.column_config.NumberColumn(
            "Unrealized P&L",
            format="$%.2f",
        ),
        "status": st.column_config.Column(
            "Status",
            help="Agent operational status"
        ),
    },
    hide_index=True,
)
```

---

### 3. Recent Trades Section

**Displays** (last 20 trades):
- Timestamp
- Agent ID
- Symbol
- Action (BUY/SELL)
- Quantity
- Price
- P&L (for sells)
- Reasoning

**Color Coding**:
- 🟢 Green: Profitable trades (P&L > 0)
- 🔴 Red: Losing trades (P&L < 0)
- ⚪ Gray: Buys (no P&L yet)

**Implementation**:
```python
# Fetch trades
trades = fetch_recent_trades(limit=20)

# Format and display
for trade in trades:
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 3])

        with col1:
            st.write(f"**{trade['timestamp']}**")
            st.caption(f"{trade['agent_id']} - {trade['symbol']}")

        with col2:
            action_color = "green" if trade['action'] == 'BUY' else "red"
            st.markdown(f":{action_color}[{trade['action']}]")

        with col3:
            st.write(f"{trade['quantity']} @ ${trade['price']:.2f}")

        with col4:
            if trade['pnl'] is not None:
                pnl_color = "green" if trade['pnl'] > 0 else "red"
                st.markdown(f":{pnl_color}[${trade['pnl']:+.2f}]")
```

---

### 4. Performance Chart

**Displays**:
- Portfolio value over time (line chart)
- Agent-specific performance (multi-line chart)
- Cumulative P&L by agent

**Implementation**:
```python
import plotly.express as px

# Fetch time-series data
performance_data = fetch_portfolio_performance(days=30)

# Create line chart
fig = px.line(
    performance_data,
    x='timestamp',
    y='portfolio_value',
    title='Portfolio Value (Last 30 Days)',
    labels={'portfolio_value': 'Value ($)', 'timestamp': 'Date'}
)

# Customize
fig.update_layout(
    hovermode='x unified',
    showlegend=True
)

# Display
st.plotly_chart(fig, use_container_width=True)
```

---

### 5. Risk Exposure Section

**Displays**:
- Current exposure by agent (pie chart)
- Position concentration
- Correlation warnings
- Risk limit utilization

**Implementation**:
```python
import plotly.graph_objects as go

# Fetch position data
positions = fetch_all_positions()

# Calculate exposure by agent
exposure_by_agent = calculate_exposure(positions)

# Create pie chart
fig = go.Figure(data=[go.Pie(
    labels=list(exposure_by_agent.keys()),
    values=list(exposure_by_agent.values()),
    hole=0.3  # Donut chart
)])

fig.update_layout(title='Exposure by Agent')

st.plotly_chart(fig, use_container_width=True)

# Risk warnings
if max_exposure > 0.5:
    st.warning("⚠️ Single agent exceeds 50% of capital!")
```

---

### 6. Sentiment Overview

**Displays** (per active agent):
- Current sentiment score (-1 to +1)
- Confidence level
- Sources used
- Sentiment trend (sparkline)

**Implementation**:
```python
from cli.utils.sentiment_aggregator import get_sentiment_aggregator

aggregator = get_sentiment_aggregator()

for agent_id in active_agents:
    symbol = get_agent_symbol(agent_id)
    sentiment = aggregator.get_aggregated_sentiment(symbol)

    # Display sentiment
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(f"{symbol} Sentiment", f"{sentiment['score']:+.2f}")

    with col2:
        confidence_pct = sentiment['confidence'] * 100
        st.metric("Confidence", f"{confidence_pct:.0f}%")

    with col3:
        # Color-coded indicator
        if sentiment['score'] > 0.3:
            st.success("🟢 Bullish")
        elif sentiment['score'] < -0.3:
            st.error("🔴 Bearish")
        else:
            st.info("⚪ Neutral")
```

---

## Data Sources

### Database Queries

**Agent Status**:
```python
def fetch_agent_status(agent_id):
    """Fetch current agent state from database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT agent_id, asset, status,
                   current_position, unrealized_pnl,
                   trades_today
            FROM agent_state
            WHERE agent_id = %s
        """, (agent_id,))
        return cursor.fetchone()
```

**Recent Trades**:
```python
def fetch_recent_trades(limit=20):
    """Fetch recent trades across all agents."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, agent_id, symbol,
                   action, quantity, price, pnl
            FROM trades
            ORDER BY timestamp DESC
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()
```

**Performance Time Series**:
```python
def fetch_portfolio_performance(days=30):
    """Fetch historical portfolio values."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, total_value, cash_balance,
                   total_positions
            FROM portfolio_snapshots
            WHERE timestamp >= NOW() - INTERVAL '%s days'
            ORDER BY timestamp ASC
        """, (days,))
        return cursor.fetchall()
```

### Real-Time Data

**Live Market Data**:
```python
from cli.utils.broker import get_broker

broker = get_broker()

# Get current quotes
quotes = broker.get_latest_quotes(['TSLA', 'IWM', 'BTC/USD'])

# Display
for symbol, quote in quotes.items():
    st.metric(
        symbol,
        f"${quote.ask_price:.2f}",
        delta=f"{quote.change_pct:+.2f}%"
    )
```

**Live Sentiment**:
```python
from cli.utils.sentiment_aggregator import get_sentiment_aggregator

# Refresh every 60 seconds
if 'last_sentiment_update' not in st.session_state or \
   time.time() - st.session_state.last_sentiment_update > 60:

    aggregator = get_sentiment_aggregator()
    st.session_state.sentiment = aggregator.get_aggregated_sentiment("TSLA")
    st.session_state.last_sentiment_update = time.time()

# Display cached sentiment
st.write(st.session_state.sentiment)
```

---

## Streamlit Best Practices

### Session State Management

```python
# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.selected_agent = None
    st.session_state.time_range = '30d'

# Update state
if st.button("Select Agent"):
    st.session_state.selected_agent = agent_id
```

### Caching

```python
# Cache expensive operations
@st.cache_data(ttl=60)  # Cache for 60 seconds
def load_historical_data(symbol, days):
    """Load historical data (cached)."""
    # Expensive database query
    return fetch_bars(symbol, days=days)

# Use cached function
data = load_historical_data('TSLA', 30)
```

### Auto-Refresh

```python
import time

# Auto-refresh every 10 seconds
refresh_interval = 10  # seconds

# Add refresh button
if st.button("🔄 Refresh"):
    st.rerun()

# Auto-refresh (experimental)
placeholder = st.empty()

while True:
    with placeholder.container():
        display_dashboard()

    time.sleep(refresh_interval)
    st.rerun()
```

### Layout Optimization

```python
# Use columns for side-by-side content
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.header("Main Content")
    st.write("Wide column")

with col2:
    st.metric("Metric 1", "100")

with col3:
    st.metric("Metric 2", "200")

# Use expanders for collapsible sections
with st.expander("Advanced Settings"):
    st.slider("Risk Tolerance", 0, 100, 50)

# Use tabs for navigation
tab1, tab2, tab3 = st.tabs(["Overview", "Performance", "Settings"])

with tab1:
    st.write("Overview content")

with tab2:
    st.write("Performance content")
```

---

## Common Dashboard Tasks

### Adding a New Metric

1. **Fetch data**:
```python
def fetch_new_metric():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM winning_trades")
        return cursor.fetchone()[0]
```

2. **Display metric**:
```python
winning_trades = fetch_new_metric()
st.metric("Winning Trades", winning_trades)
```

### Creating a New Chart

1. **Prepare data**:
```python
import pandas as pd

data = fetch_chart_data()
df = pd.DataFrame(data, columns=['date', 'value'])
```

2. **Create chart**:
```python
import plotly.express as px

fig = px.line(df, x='date', y='value', title='Custom Chart')
st.plotly_chart(fig, use_container_width=True)
```

### Adding a Filter

```python
# Add selectbox filter
selected_agent = st.selectbox(
    "Select Agent",
    options=['All'] + list(active_agents)
)

# Apply filter to data
if selected_agent != 'All':
    filtered_data = data[data['agent_id'] == selected_agent]
else:
    filtered_data = data

# Display filtered results
st.dataframe(filtered_data)
```

### Adding a Date Range Picker

```python
import datetime

# Date range picker
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime.date.today() - datetime.timedelta(days=30)
    )

with col2:
    end_date = st.date_input(
        "End Date",
        value=datetime.date.today()
    )

# Fetch data for date range
data = fetch_data_for_range(start_date, end_date)
```

---

## Styling and Themes

### Custom CSS

```python
# Inject custom CSS
st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }

    .positive-pnl {
        color: #00c851;
        font-weight: bold;
    }

    .negative-pnl {
        color: #ff4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Use custom CSS classes
st.markdown('<div class="metric-container">Custom styled content</div>',
            unsafe_allow_html=True)
```

### Color Themes

```python
# Conditional formatting
def get_pnl_color(pnl):
    return "green" if pnl > 0 else "red"

# Apply to metric
st.metric("P&L", f"${pnl:.2f}", delta_color="normal")
```

---

## Performance Optimization

### Reduce Database Queries

```python
# Bad: Multiple queries
agent1 = fetch_agent_status('agent_tsla')
agent2 = fetch_agent_status('agent_iwm')
agent3 = fetch_agent_status('agent_btc')

# Good: Single query
agents = fetch_all_agent_statuses()
```

### Use Caching

```python
# Cache static data
@st.cache_data(ttl=3600)  # 1 hour
def load_configuration():
    return get_config()

# Cache expensive computations
@st.cache_data
def calculate_correlations(data):
    return data.corr()
```

### Lazy Loading

```python
# Only load data when tab is selected
tab1, tab2 = st.tabs(["Quick View", "Detailed Analysis"])

with tab1:
    # Light data
    st.write(fetch_summary())

with tab2:
    # Heavy data - only loads if user clicks tab
    st.write(fetch_detailed_analysis())
```

---

## Error Handling

### Graceful Degradation

```python
try:
    agent_status = fetch_agent_status('agent_tsla')
    st.success(f"✅ Agent active: {agent_status['status']}")
except Exception as e:
    st.error(f"❌ Failed to fetch agent status: {e}")
    st.info("Using cached data from 5 minutes ago")
    agent_status = load_cached_status()
```

### Connection Checks

```python
# Check database connection
try:
    with get_db_connection() as conn:
        conn.execute("SELECT 1")
    db_status = "🟢 Connected"
except Exception:
    db_status = "🔴 Disconnected"

st.sidebar.write(f"Database: {db_status}")
```

### User Feedback

```python
# Show loading spinner
with st.spinner("Loading data..."):
    data = expensive_operation()

st.success("Data loaded successfully!")

# Progress bar
progress_bar = st.progress(0)
for i in range(100):
    process_chunk(i)
    progress_bar.progress(i + 1)

st.success("Processing complete!")
```

---

## Common Issues and Solutions

### Issue: Dashboard Not Updating
**Solution**: Add manual refresh button or auto-refresh mechanism

### Issue: Slow Dashboard Loading
**Solution**: Use `@st.cache_data` for expensive queries, reduce data fetching

### Issue: Charts Not Displaying
**Solution**: Check data format, ensure Plotly is installed, verify column names

### Issue: Database Connection Timeout
**Solution**: Implement connection pooling, add retry logic, check Docker network

---

## Files You'll Work With

**Main Dashboard**:
- `dashboard.py` - All dashboard code

**Data Sources**:
- `cli/utils/database.py` - Database queries
- `cli/utils/broker.py` - Live market data
- `cli/utils/sentiment_aggregator.py` - Sentiment data
- `cli/utils/config.py` - Configuration

**Deployment**:
- `run_dashboard.sh` - Development startup
- `docker-compose.yml` - Production deployment (dashboard service)

---

## Documentation References

- Full dashboard guide: `docs/guides/dashboard-guide.md`
- Streamlit docs: https://docs.streamlit.io
- Plotly docs: https://plotly.com/python/

---

**Last Updated**: 2025-11-13
**Context Version**: 1.0 (Dashboard Developer Persona)
