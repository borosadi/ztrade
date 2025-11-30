"""
Airflow DAG for Agent PLTR - Palantir Sentiment Trading

Schedule: Every 15 minutes during market hours (Mon-Fri, 9:30 AM - 4:00 PM EST)
Strategy: Sentiment-Momentum (60% sentiment + 40% technical)
Focus: AI/defense contract narratives
"""
from trading_dag_factory import create_trading_dag

dag = create_trading_dag(
    agent_id='agent_pltr',
    asset='PLTR',
    interval_minutes=15,
    schedule='*/15 14-20 * * 1-5',
    tags=['trading', 'pltr', 'stocks', 'sentiment_momentum', 'algorithmic'],
    is_crypto=False
)
