"""
Airflow DAG for Agent SOL/USD - Solana Sentiment Trading

Schedule: Every 60 minutes, 24/7 (crypto never closes)
Strategy: Sentiment-Momentum (60% sentiment + 40% technical)
Focus: NFT/ecosystem sentiment
"""
from trading_dag_factory import create_trading_dag

dag = create_trading_dag(
    agent_id='agent_sol',
    asset='SOL/USD',
    interval_minutes=60,
    schedule='0 */60 * * *',
    tags=['trading', 'sol', 'crypto', 'sentiment_momentum', 'algorithmic'],
    is_crypto=True
)
