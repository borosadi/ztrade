"""
Airflow DAG for Agent DDOG - Datadog Sentiment Trading

Schedule: Every 15 minutes during market hours (Mon-Fri, 9:30 AM - 4:00 PM EST)
Strategy: Sentiment-Momentum (60% sentiment + 40% technical)
Focus: DevOps/observability sector
"""
from trading_dag_factory import create_trading_dag

dag = create_trading_dag(
    agent_id='agent_ddog',
    asset='DDOG',
    interval_minutes=15,
    schedule='*/15 14-20 * * 1-5',
    tags=['trading', 'ddog', 'stocks', 'sentiment_momentum', 'algorithmic'],
    is_crypto=False
)
