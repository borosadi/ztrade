"""
Airflow DAG for Agent DOGE/USD - Dogecoin Meme Sentiment Trading

Schedule: Every 60 minutes, 24/7 (crypto never closes)
Strategy: Sentiment-Momentum (60% sentiment + 40% technical)
Focus: Meme coin, Elon-driven narratives
"""
from trading_dag_factory import create_trading_dag

dag = create_trading_dag(
    agent_id='agent_doge',
    asset='DOGE/USD',
    interval_minutes=60,
    schedule='0 */60 * * *',
    tags=['trading', 'doge', 'crypto', 'meme', 'sentiment_momentum', 'algorithmic'],
    is_crypto=True
)
