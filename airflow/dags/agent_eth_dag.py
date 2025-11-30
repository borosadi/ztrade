"""
Airflow DAG for Agent ETH/USD - Ethereum Sentiment Trading

Schedule: Every 60 minutes, 24/7 (crypto never closes)
Strategy: Sentiment-Momentum (60% sentiment + 40% technical)
Focus: DeFi ecosystem narratives
"""
from trading_dag_factory import create_trading_dag

dag = create_trading_dag(
    agent_id='agent_eth',
    asset='ETH/USD',
    interval_minutes=60,
    schedule='0 */60 * * *',
    tags=['trading', 'eth', 'crypto', 'sentiment_momentum', 'algorithmic'],
    is_crypto=True
)
