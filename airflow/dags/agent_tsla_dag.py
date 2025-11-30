"""
Airflow DAG for Agent TSLA - Tesla Momentum Trading

Schedule: Every 5 minutes during market hours (Mon-Fri, 9:30 AM - 4:00 PM EST)
Strategy: Sentiment-Momentum (60% sentiment + 40% technical)
Validated: 91.2% win rate in backtest
"""
from trading_dag_factory import create_trading_dag

# Create DAG using factory
dag = create_trading_dag(
    agent_id='agent_tsla',
    asset='TSLA',
    interval_minutes=5,
    schedule='*/5 14-20 * * 1-5',  # Every 5 min, 9 AM-4 PM EST (14-21 UTC), Mon-Fri
    tags=['trading', 'tsla', 'stocks', 'momentum', 'algorithmic'],
    is_crypto=False,
    description='TSLA sentiment-momentum trading agent - 5-minute cycles (validated: 91.2% win rate)'
)
