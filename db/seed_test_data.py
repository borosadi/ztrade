#!/usr/bin/env python3
"""Seed test data for backtesting demonstration."""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.utils.database import market_data_store, sentiment_data_store
from cli.utils.logger import get_logger

logger = get_logger(__name__)


def generate_sample_bars(symbol: str, days: int = 30) -> list:
    """Generate sample OHLCV bars for testing."""
    bars = []
    base_price = {'SPY': 450.0, 'TSLA': 250.0, 'AAPL': 180.0}.get(symbol, 100.0)

    # Generate daily bars
    current_date = datetime.now(timezone.utc) - timedelta(days=days)

    for day in range(days):
        # Market hours: 9:30 AM - 4:00 PM ET (390 minutes)
        # Generate 78 5-minute bars per day
        date = current_date + timedelta(days=day)

        # Only generate for weekdays
        if date.weekday() >= 5:  # Saturday or Sunday
            continue

        daily_open = base_price + random.uniform(-5, 5)
        daily_trend = random.uniform(-2, 2)  # Daily trend

        for minute in range(0, 390, 5):  # 5-minute bars
            timestamp = date.replace(hour=9, minute=30) + timedelta(minutes=minute)

            # Add some random walk
            noise = random.uniform(-1, 1)
            trend_component = (minute / 390) * daily_trend

            open_price = daily_open + trend_component + noise
            close_price = open_price + random.uniform(-0.5, 0.5)
            high_price = max(open_price, close_price) + abs(random.uniform(0, 0.3))
            low_price = min(open_price, close_price) - abs(random.uniform(0, 0.3))
            volume = random.randint(100000, 1000000)

            bars.append({
                'symbol': symbol,
                'timestamp': timestamp,
                'timeframe': '5m',
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume,
                'vwap': round((open_price + close_price) / 2, 2),
                'trade_count': random.randint(100, 500)
            })

        # Update base price for next day
        base_price = bars[-1]['close'] if bars else base_price

    return bars


def generate_sample_sentiment(symbol: str, days: int = 30) -> list:
    """Generate sample sentiment data for testing."""
    sentiments = []
    sources = ['news', 'reddit', 'sec']

    current_date = datetime.now(timezone.utc) - timedelta(days=days)

    for day in range(days):
        date = current_date + timedelta(days=day)

        # Only generate for weekdays
        if date.weekday() >= 5:
            continue

        # Generate sentiment at market open and mid-day
        for hour in [9, 14]:
            timestamp = date.replace(hour=hour, minute=0, second=0)

            for source in sources:
                # Random sentiment
                score = random.uniform(-0.5, 0.8)  # Slightly bullish bias
                if score > 0.3:
                    sentiment = 'positive'
                elif score < -0.3:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'

                confidence = random.uniform(0.5, 0.95)

                sentiments.append({
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'source': source,
                    'sentiment': sentiment,
                    'score': round(score, 4),
                    'confidence': round(confidence, 4),
                    'metadata': {
                        'article_count': random.randint(1, 10) if source == 'news' else None,
                        'mention_count': random.randint(5, 50) if source == 'reddit' else None,
                        'filing_count': random.randint(1, 3) if source == 'sec' else None
                    }
                })

    return sentiments


def seed_data():
    """Seed the database with test data."""
    symbols = ['SPY', 'TSLA', 'AAPL']
    days = 60  # 60 days of data

    logger.info(f"Seeding test data for {len(symbols)} symbols over {days} days...")

    total_bars = 0
    total_sentiment = 0

    for symbol in symbols:
        logger.info(f"Generating data for {symbol}...")

        # Generate and insert bars
        bars = generate_sample_bars(symbol, days)
        count = market_data_store.insert_bars_bulk(bars)
        total_bars += count
        logger.info(f"  Inserted {count} bars for {symbol}")

        # Generate and insert sentiment
        sentiments = generate_sample_sentiment(symbol, days)
        count = sentiment_data_store.insert_sentiments_bulk(sentiments)
        total_sentiment += count
        logger.info(f"  Inserted {count} sentiment records for {symbol}")

    logger.info(f"\n✅ Seeding complete!")
    logger.info(f"   Total bars: {total_bars}")
    logger.info(f"   Total sentiment records: {total_sentiment}")
    logger.info(f"\nYou can now run backtests with:")
    logger.info(f"  uv run ztrade backtest run agent_spy --start 2025-09-10 --end 2025-11-10")


if __name__ == '__main__':
    seed_data()
