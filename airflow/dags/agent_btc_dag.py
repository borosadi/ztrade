"""
Airflow DAG for Agent BTC/USD - Bitcoin Sentiment Trading

Schedule: Every 60 minutes, 24/7 (crypto never closes)
Strategy: Sentiment-Momentum (60% sentiment + 40% technical)
Expected Sentiment Alpha: 40-60%
"""
from trading_dag_factory import create_trading_dag

dag = create_trading_dag(
    agent_id='agent_btc',
    asset='BTC/USD',
    interval_minutes=60,
    schedule='0 */60 * * *',
    tags=['trading', 'btc', 'crypto', 'sentiment_momentum', 'algorithmic'],
    is_crypto=True
)
