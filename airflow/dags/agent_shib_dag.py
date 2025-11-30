"""
Airflow DAG for Agent SHIB/USD - Shiba Inu Meme Sentiment Trading

Schedule: Every 60 minutes, 24/7 (crypto never closes)
Strategy: Sentiment-Momentum (60% sentiment + 40% technical)
Focus: Meme coin, Shib Army community sentiment
"""
from trading_dag_factory import create_trading_dag

dag = create_trading_dag(
    agent_id='agent_shib',
    asset='SHIB/USD',
    interval_minutes=60,
    schedule='0 */60 * * *',
    tags=['trading', 'shib', 'crypto', 'meme', 'sentiment_momentum', 'algorithmic'],
    is_crypto=True
)
