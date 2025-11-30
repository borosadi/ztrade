"""
Airflow DAG for Agent NET - Cloudflare Sentiment Trading

Schedule: Every 15 minutes during market hours (Mon-Fri, 9:30 AM - 4:00 PM EST)
Strategy: Sentiment-Momentum (60% sentiment + 40% technical)
Focus: Cloud/security narratives
"""
from trading_dag_factory import create_trading_dag

dag = create_trading_dag(
    agent_id='agent_net',
    asset='NET',
    interval_minutes=15,
    schedule='*/15 14-20 * * 1-5',
    tags=['trading', 'net', 'stocks', 'sentiment_momentum', 'algorithmic'],
    is_crypto=False
)
