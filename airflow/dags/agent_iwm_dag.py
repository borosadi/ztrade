"""
Airflow DAG for Agent IWM - Russell 2000 Small-Cap Trading

Schedule: Every 15 minutes during market hours (Mon-Fri, 9:30 AM - 4:00 PM EST)
Strategy: Sentiment-Momentum (60% sentiment + 40% technical)
Focus: Small-cap sentiment edge
"""
from trading_dag_factory import create_trading_dag

dag = create_trading_dag(
    agent_id='agent_iwm',
    asset='IWM',
    interval_minutes=15,
    schedule='*/15 14-20 * * 1-5',  # Every 15 min, 9 AM-4 PM EST, Mon-Fri
    tags=['trading', 'iwm', 'stocks', 'small-cap', 'sentiment_momentum', 'algorithmic'],
    is_crypto=False
)
