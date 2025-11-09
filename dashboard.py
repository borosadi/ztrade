"""
Ztrade Trading Dashboard - Real-time monitoring for autonomous trading agents.

Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from cli.utils.config import get_config
from cli.utils.broker import get_broker
from cli.utils.market_data import MarketDataProvider
from cli.utils.sentiment_aggregator import get_sentiment_aggregator

# Page configuration
st.set_page_config(
    page_title="Ztrade Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .positive {
        color: #00c851;
        font-weight: bold;
    }
    .negative {
        color: #ff4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=30)
def load_dashboard_data():
    """Load all dashboard data with 30-second cache."""
    config = get_config()

    try:
        # Load configurations
        company_config = config.load_company_config()
        agents = config.list_agents()

        # Get broker data
        broker = get_broker()
        account = broker.get_account_info()
        positions = broker.get_positions()

        # Get agent data
        agent_data = []
        for agent_id in agents:
            agent_config = config.load_agent_config(agent_id)
            agent_state = config.load_agent_state(agent_id)
            agent_data.append({
                'id': agent_id,
                'name': agent_config.get('agent', {}).get('name', agent_id),
                'asset': agent_config.get('agent', {}).get('asset', 'N/A'),
                'status': agent_config.get('agent', {}).get('status', 'unknown'),
                'strategy': agent_config.get('strategy', {}).get('type', 'N/A'),
                'allocated_capital': agent_config.get('performance', {}).get('allocated_capital', 0),
                'pnl_today': agent_state.get('pnl_today', 0),
                'trades_today': agent_state.get('trades_today', 0),
                'positions': agent_state.get('positions', []),
            })

        return {
            'company_config': company_config,
            'account': account,
            'positions': positions,
            'agents': agent_data,
            'timestamp': datetime.now()
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def render_company_overview(data):
    """Render company overview section."""
    st.markdown('<h2>📊 Company Overview</h2>', unsafe_allow_html=True)

    account = data['account']

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 Account Equity",
            value=f"${account['equity']:,.2f}",
            delta=f"${account['equity'] - 100000:,.2f}"
        )

    with col2:
        st.metric(
            label="💵 Cash Available",
            value=f"${account['cash']:,.2f}"
        )

    with col3:
        st.metric(
            label="⚡ Buying Power",
            value=f"${account['buying_power']:,.2f}"
        )

    with col4:
        active_agents = sum(1 for a in data['agents'] if a['status'] == 'active')
        st.metric(
            label="🤖 Active Agents",
            value=f"{active_agents} / {len(data['agents'])}"
        )

    # Trading status
    if account.get('trading_blocked'):
        st.error("⚠️ Trading is currently BLOCKED")
    else:
        st.success("✅ Trading is active")


def render_agent_status(data):
    """Render agent status section."""
    st.markdown('<h2>🤖 Agent Status</h2>', unsafe_allow_html=True)

    agents_df = pd.DataFrame(data['agents'])

    if not agents_df.empty:
        # Calculate totals
        total_capital = agents_df['allocated_capital'].sum()
        total_pnl = agents_df['pnl_today'].sum()
        total_trades = agents_df['trades_today'].sum()

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💼 Total Allocated", f"${total_capital:,.2f}")
        with col2:
            pnl_color = "normal" if total_pnl >= 0 else "inverse"
            st.metric("📈 Total P&L Today", f"${total_pnl:+,.2f}",
                     delta_color=pnl_color)
        with col3:
            st.metric("📊 Total Trades Today", f"{total_trades}")

        st.markdown("---")

        # Agent cards
        for agent in data['agents']:
            with st.expander(f"{'✅' if agent['status'] == 'active' else '⏸'} {agent['name']} ({agent['asset']})",
                           expanded=False):
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Strategy", agent['strategy'].title())
                with col2:
                    st.metric("Allocated", f"${agent['allocated_capital']:,.2f}")
                with col3:
                    pnl_value = agent['pnl_today']
                    st.markdown(
                        f"<div>P&L Today<br/><span class=\"{'positive' if pnl_value >= 0 else 'negative'}\">"
                        f"${pnl_value:+,.2f}</span></div>",
                        unsafe_allow_html=True
                    )
                with col4:
                    st.metric("Trades Today", agent['trades_today'])

                # Show positions if any
                if agent['positions']:
                    st.markdown("**Current Positions:**")
                    for pos in agent['positions']:
                        st.text(f"  {pos.get('symbol')}: {pos.get('qty')} shares @ ${pos.get('entry_price', 0):.2f}")
    else:
        st.info("No agents configured yet.")


def render_positions(data):
    """Render open positions section."""
    st.markdown('<h2>📈 Open Positions</h2>', unsafe_allow_html=True)

    positions = data['positions']

    if not positions:
        st.info("No open positions.")
        return

    # Create positions dataframe
    positions_data = []
    for pos in positions:
        positions_data.append({
            'Symbol': pos['symbol'],
            'Side': pos['side'].upper(),
            'Quantity': pos['qty'],
            'Entry Price': f"${pos['avg_entry_price']:.2f}",
            'Current Price': f"${pos['current_price']:.2f}",
            'Market Value': f"${pos['market_value']:,.2f}",
            'P&L': f"${pos['unrealized_pl']:+,.2f}",
            'P&L %': f"{pos['unrealized_plpc']*100:+.2f}%"
        })

    positions_df = pd.DataFrame(positions_data)
    st.dataframe(positions_df, width="stretch")

    # Total P&L
    total_pl = sum(p['unrealized_pl'] for p in positions)
    total_value = sum(p['market_value'] for p in positions)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Market Value", f"${total_value:,.2f}")
    with col2:
        pnl_color = "normal" if total_pl >= 0 else "inverse"
        st.metric("Total Unrealized P&L", f"${total_pl:+,.2f}", delta_color=pnl_color)


def render_pnl_chart(data):
    """Render P&L chart."""
    st.markdown('<h2>📊 Agent P&L Comparison</h2>', unsafe_allow_html=True)

    agents_df = pd.DataFrame(data['agents'])

    if agents_df.empty:
        st.info("No agent data available.")
        return

    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=agents_df['name'],
            y=agents_df['pnl_today'],
            marker_color=['green' if x >= 0 else 'red' for x in agents_df['pnl_today']],
            text=[f"${x:+,.2f}" for x in agents_df['pnl_today']],
            textposition='outside'
        )
    ])

    fig.update_layout(
        title='Agent P&L Today',
        xaxis_title='Agent',
        yaxis_title='P&L ($)',
        showlegend=False,
        height=400
    )

    st.plotly_chart(fig)


def render_sentiment_tracking(data):
    """Render sentiment tracking section."""
    st.markdown('<h2>💭 Sentiment Tracking</h2>', unsafe_allow_html=True)

    try:
        aggregator = get_sentiment_aggregator()

        sentiment_data = []
        for agent in data['agents']:
            asset = agent['asset']
            if asset and asset != 'N/A':
                try:
                    sentiment = aggregator.get_aggregated_sentiment(
                        symbol=asset,
                        news_lookback_hours=24,
                        reddit_lookback_hours=24,
                        sec_lookback_days=30
                    )
                    sentiment_data.append({
                        'Asset': asset,
                        'Sentiment': sentiment.get('overall_sentiment', 'N/A'),
                        'Score': sentiment.get('sentiment_score', 0),
                        'Confidence': f"{sentiment.get('confidence', 0)*100:.0f}%",
                        'Sources': sentiment.get('sources_used', 0),
                        'Agreement': f"{sentiment.get('agreement_level', 0)}%"
                    })
                except Exception as e:
                    st.warning(f"Could not fetch sentiment for {asset}: {e}")

        if sentiment_data:
            sentiment_df = pd.DataFrame(sentiment_data)
            st.dataframe(sentiment_df, width="stretch")

            # Sentiment gauge charts - create individual columns for each
            num_assets = len(sentiment_data)
            if num_assets == 1:
                cols = [st.columns(1)[0]]
            elif num_assets == 2:
                cols = st.columns(2)
            else:
                cols = st.columns(3)

            for idx, item in enumerate(sentiment_data):
                with cols[idx % len(cols)]:
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=item['Score'],
                        title={'text': f"{item['Asset']} Sentiment", 'font': {'size': 20}},
                        delta={'reference': 0},
                        gauge={
                            'axis': {'range': [-1, 1], 'tickwidth': 1, 'tickcolor': "darkgray"},
                            'bar': {'color': "darkblue"},
                            'bgcolor': "white",
                            'borderwidth': 2,
                            'bordercolor': "gray",
                            'steps': [
                                {'range': [-1, -0.3], 'color': "lightcoral"},
                                {'range': [-0.3, 0.3], 'color': "lightyellow"},
                                {'range': [0.3, 1], 'color': "lightgreen"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 0.9
                            }
                        }
                    ))

                    fig.update_layout(
                        height=250,
                        margin=dict(l=20, r=20, t=50, b=20)
                    )
                    st.plotly_chart(fig)
        else:
            st.info("No sentiment data available.")

    except Exception as e:
        st.error(f"Error loading sentiment data: {e}")


def render_risk_monitoring(data):
    """Render risk monitoring section."""
    st.markdown('<h2>⚠️ Risk Monitoring</h2>', unsafe_allow_html=True)

    company_config = data['company_config']
    max_capital = company_config.get('max_capital_allocation', 100000)

    # Calculate risk metrics
    total_allocated = sum(a['allocated_capital'] for a in data['agents'])
    utilization = (total_allocated / max_capital * 100) if max_capital > 0 else 0

    total_pnl_today = sum(a['pnl_today'] for a in data['agents'])
    daily_loss_pct = (total_pnl_today / max_capital * 100) if max_capital > 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Capital Utilization",
            f"{utilization:.1f}%",
            help="Percentage of total capital allocated to agents"
        )
        if utilization > 80:
            st.warning("⚠️ High capital utilization!")

    with col2:
        st.metric(
            "Daily P&L %",
            f"{daily_loss_pct:+.2f}%",
            help="Today's P&L as percentage of total capital"
        )
        if daily_loss_pct < -2:
            st.error("🚨 Daily loss limit approaching!")

    with col3:
        open_positions = len(data['positions'])
        st.metric(
            "Open Positions",
            open_positions,
            help="Total number of open positions across all agents"
        )

    # Risk rules status
    st.markdown("### Risk Rules Status")

    risk_checks = []

    # RULE_001: No agent exceeds 10% of capital
    for agent in data['agents']:
        pct = (agent['allocated_capital'] / max_capital * 100) if max_capital > 0 else 0
        risk_checks.append({
            'Rule': 'RULE_001',
            'Description': f"{agent['name']}: Agent allocation",
            'Status': '✅ PASS' if pct <= 10 else '❌ FAIL',
            'Value': f"{pct:.1f}% (limit: 10%)"
        })

    # RULE_002: Daily loss limit
    risk_checks.append({
        'Rule': 'RULE_002',
        'Description': 'Daily loss limit',
        'Status': '✅ PASS' if daily_loss_pct >= -2 else '❌ FAIL',
        'Value': f"{daily_loss_pct:+.2f}% (limit: -2%)"
    })

    # RULE_006: Max 80% capital deployed
    risk_checks.append({
        'Rule': 'RULE_006',
        'Description': 'Maximum capital deployed',
        'Status': '✅ PASS' if utilization <= 80 else '❌ FAIL',
        'Value': f"{utilization:.1f}% (limit: 80%)"
    })

    risk_df = pd.DataFrame(risk_checks)
    st.dataframe(risk_df, width="stretch")


def render_recent_activity(data):
    """Render recent trading activity."""
    st.markdown('<h2>📝 Recent Activity</h2>', unsafe_allow_html=True)

    # Look for recent logs
    logs_dir = Path('logs/agent_decisions')

    if not logs_dir.exists():
        st.info("No recent activity logs found.")
        return

    # Get today's logs
    today = datetime.now().strftime('%Y-%m-%d')
    today_dir = logs_dir / today

    if today_dir.exists():
        log_files = sorted(today_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)

        if log_files:
            st.markdown(f"**Found {len(log_files)} decisions today**")

            # Show last 5 decisions
            for log_file in log_files[:5]:
                try:
                    with open(log_file, 'r') as f:
                        decision = json.load(f)

                    timestamp = decision.get('timestamp', 'N/A')
                    agent_id = decision.get('agent_id', 'N/A')
                    action = decision.get('action', 'N/A')
                    confidence = decision.get('confidence', 0)

                    st.text(f"{timestamp} | {agent_id} | {action.upper()} | Confidence: {confidence:.0%}")
                except Exception as e:
                    st.warning(f"Could not read {log_file.name}: {e}")
        else:
            st.info("No decisions logged today yet.")
    else:
        st.info("No activity today yet.")


def main():
    """Main dashboard function."""

    # Header
    st.markdown('<h1 class="main-header">🚀 Ztrade Trading Dashboard</h1>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)

        if auto_refresh:
            st.info("Dashboard refreshes every 30 seconds")

        # Manual refresh button
        if st.button("🔄 Refresh Now"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Navigation")
        st.markdown("- Company Overview")
        st.markdown("- Agent Status")
        st.markdown("- Open Positions")
        st.markdown("- P&L Charts")
        st.markdown("- Sentiment Tracking")
        st.markdown("- Risk Monitoring")
        st.markdown("- Recent Activity")

        st.markdown("---")
        st.markdown("### 🔗 Quick Links")
        st.markdown("[Flower Dashboard](http://localhost:5555)")
        st.markdown("[Alpaca Dashboard](https://app.alpaca.markets/paper/dashboard/overview)")

        st.markdown("---")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load data
    data = load_dashboard_data()

    if data is None:
        st.error("Failed to load dashboard data. Check your configuration and broker connection.")
        return

    # Render sections
    render_company_overview(data)
    st.markdown("---")

    render_agent_status(data)
    st.markdown("---")

    render_positions(data)
    st.markdown("---")

    render_pnl_chart(data)
    st.markdown("---")

    render_sentiment_tracking(data)
    st.markdown("---")

    render_risk_monitoring(data)
    st.markdown("---")

    render_recent_activity(data)

    # Auto-refresh
    if auto_refresh:
        import time
        time.sleep(30)
        st.rerun()


if __name__ == "__main__":
    main()
