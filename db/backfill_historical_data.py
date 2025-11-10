#!/usr/bin/env python3
"""Backfill historical market data from Alpaca API for backtesting."""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import time
from typing import List, Dict, Any
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.utils.broker import get_broker
from cli.utils.database import market_data_store, sentiment_data_store
from cli.utils.sentiment_aggregator import get_sentiment_aggregator
from cli.utils.logger import get_logger

logger = get_logger(__name__)


def discover_symbols() -> List[str]:
    """Auto-discover symbols from agent configs."""
    symbols = []
    agents_dir = Path('agents')

    if not agents_dir.exists():
        logger.error("agents/ directory not found")
        return symbols

    for agent_dir in agents_dir.iterdir():
        if agent_dir.is_dir():
            config_file = agent_dir / 'context.yaml'
            if config_file.exists():
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                    asset = config.get('agent', {}).get('asset')
                    if asset:
                        symbols.append(asset)

    return list(set(symbols))


def fetch_bars_for_period(
    broker,
    symbol: str,
    timeframe: str,
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """
    Fetch bars for a date range using pagination.

    Alpaca has a limit of 10,000 bars per request, so we need to paginate
    for longer time periods.
    """
    all_bars = []

    # Calculate approximate number of bars we'll need
    duration = (end_date - start_date).total_seconds()

    # Estimate bars per period
    bars_per_day = {
        '1Min': 390,   # Market hours: 6.5 hours = 390 minutes
        '5Min': 78,    # 390 / 5
        '15Min': 26,   # 390 / 15
        '1Hour': 6,    # Approximately 6.5 hours
        '1Day': 1,
    }

    # Use broker's get_bars which has 10,000 limit
    # For longer periods, we'll need to chunk
    timeframe_alpaca = {
        '1m': '1Min',
        '5m': '5Min',
        '15m': '15Min',
        '1h': '1Hour',
        '1d': '1Day',
    }.get(timeframe, timeframe)

    # Calculate total days
    days = (end_date - start_date).days

    # Estimate total bars
    estimated_bars = days * bars_per_day.get(timeframe_alpaca, 100)

    logger.info(f"Fetching {symbol} {timeframe} data from {start_date.date()} to {end_date.date()}")
    logger.info(f"Estimated bars: ~{estimated_bars}")

    if estimated_bars <= 10000:
        # Single request with date range
        bars = broker.get_bars(
            symbol,
            timeframe_alpaca,
            limit=10000,
            start=start_date.isoformat(),
            end=end_date.isoformat()
        )

        # Add all bars (already filtered by API)
        all_bars.extend(bars)
    else:
        # Need to paginate - fetch in chunks
        chunk_days = 30  # Fetch 1 month at a time for minute data
        if timeframe_alpaca in ['1Hour', '1Day']:
            chunk_days = 365  # 1 year at a time for hourly/daily

        current_start = start_date

        while current_start < end_date:
            current_end = min(current_start + timedelta(days=chunk_days), end_date)

            logger.info(f"  Fetching chunk: {current_start.date()} to {current_end.date()}")

            bars = broker.get_bars(
                symbol,
                timeframe_alpaca,
                limit=10000,
                start=current_start.isoformat(),
                end=current_end.isoformat()
            )

            # Add all bars from this chunk
            all_bars.extend(bars)

            current_start = current_end + timedelta(days=1)

            # Rate limiting
            time.sleep(0.5)

    logger.info(f"  Fetched {len(all_bars)} bars for {symbol}")
    return all_bars


def fetch_sentiment_for_period(
    symbol: str,
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, Any]]:
    """
    Fetch sentiment data for historical period.

    Note: This will only fetch current sentiment, not historical.
    For true historical backtesting, you'd need a service that provides
    historical sentiment or archived news data.
    """
    sentiments = []

    # Get current sentiment as a sample
    aggregator = get_sentiment_aggregator()

    try:
        sentiment_data = aggregator.get_aggregated_sentiment(
            symbol,
            news_lookback_hours=24,
            reddit_lookback_hours=24,
            sec_lookback_days=30
        )

        # Store current sentiment with current timestamp
        # Note: This is a limitation - we're using current sentiment
        # for historical backtesting. Real historical sentiment would require
        # a different data source.
        timestamp = datetime.now(timezone.utc)

        for source in ['news', 'reddit', 'sec']:
            if source in sentiment_data.get('sources', {}):
                source_data = sentiment_data['sources'][source]
                sentiments.append({
                    'symbol': symbol,
                    'timestamp': timestamp,
                    'source': source,
                    'sentiment': source_data['sentiment'],
                    'score': source_data['score'],
                    'confidence': source_data['confidence'],
                    'metadata': source_data.get('metadata', {})
                })

        logger.info(f"  Fetched {len(sentiments)} sentiment records for {symbol}")

    except Exception as e:
        logger.warning(f"Could not fetch sentiment for {symbol}: {e}")

    return sentiments


def backfill_data(
    symbols: List[str] = None,
    days_back: int = 30,
    timeframes: List[str] = None,
    fetch_sentiment: bool = True
):
    """
    Backfill historical data from Alpaca.

    Args:
        symbols: List of symbols (auto-discovered if None)
        days_back: Number of days to backfill
        timeframes: List of timeframes to fetch (default: ['1m', '5m', '15m', '1h', '1d'])
        fetch_sentiment: Whether to fetch sentiment data
    """
    broker = get_broker()

    # Auto-discover symbols if not provided
    if symbols is None:
        symbols = discover_symbols()

    if not symbols:
        logger.error("No symbols found to backfill")
        return

    # Default timeframes
    if timeframes is None:
        timeframes = ['1m', '5m', '15m', '1h', '1d']

    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)

    logger.info(f"="*60)
    logger.info(f"HISTORICAL DATA BACKFILL")
    logger.info(f"="*60)
    logger.info(f"Symbols: {', '.join(symbols)}")
    logger.info(f"Timeframes: {', '.join(timeframes)}")
    logger.info(f"Period: {start_date.date()} to {end_date.date()} ({days_back} days)")
    logger.info(f"Fetch sentiment: {fetch_sentiment}")
    logger.info(f"="*60)

    total_bars = 0
    total_sentiment = 0

    for symbol in symbols:
        logger.info(f"\n📊 Processing {symbol}...")

        # Fetch bars for each timeframe
        for timeframe in timeframes:
            try:
                bars = fetch_bars_for_period(
                    broker, symbol, timeframe, start_date, end_date
                )

                if not bars:
                    logger.warning(f"  No bars fetched for {symbol} {timeframe}")
                    continue

                # Prepare for bulk insert
                db_bars = []
                for bar in bars:
                    # Parse timestamp
                    timestamp = datetime.fromisoformat(
                        bar['timestamp'].replace('Z', '+00:00')
                    )

                    db_bars.append({
                        'symbol': symbol,
                        'timestamp': timestamp,
                        'timeframe': timeframe,
                        'open': bar['open'],
                        'high': bar['high'],
                        'low': bar['low'],
                        'close': bar['close'],
                        'volume': bar['volume'],
                        'vwap': None,  # Alpaca's get_bars doesn't include VWAP
                        'trade_count': None
                    })

                # Bulk insert
                count = market_data_store.insert_bars_bulk(db_bars)
                total_bars += count
                logger.info(f"  ✅ Inserted {count} bars for {timeframe}")

            except Exception as e:
                logger.error(f"  ❌ Error fetching {symbol} {timeframe}: {e}")

        # Fetch sentiment
        if fetch_sentiment:
            try:
                sentiments = fetch_sentiment_for_period(
                    symbol, start_date, end_date
                )

                if sentiments:
                    count = sentiment_data_store.insert_sentiments_bulk(sentiments)
                    total_sentiment += count
                    logger.info(f"  ✅ Inserted {count} sentiment records")
            except Exception as e:
                logger.error(f"  ❌ Error fetching sentiment for {symbol}: {e}")

        # Rate limiting between symbols
        time.sleep(1)

    logger.info(f"\n" + "="*60)
    logger.info(f"✅ BACKFILL COMPLETE")
    logger.info(f"="*60)
    logger.info(f"Total bars inserted: {total_bars:,}")
    logger.info(f"Total sentiment records: {total_sentiment}")
    logger.info(f"\nYou can now run backtests with:")
    logger.info(f"  uv run ztrade backtest run agent_spy --start {start_date.date()} --end {end_date.date()}")
    logger.info("="*60)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Backfill historical market data from Alpaca'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to backfill (default: 30)'
    )
    parser.add_argument(
        '--symbols',
        nargs='+',
        help='Symbols to backfill (auto-discovered if not provided)'
    )
    parser.add_argument(
        '--timeframes',
        nargs='+',
        choices=['1m', '5m', '15m', '1h', '1d'],
        help='Timeframes to fetch (default: all)'
    )
    parser.add_argument(
        '--no-sentiment',
        action='store_true',
        help='Skip sentiment data collection'
    )

    args = parser.parse_args()

    backfill_data(
        symbols=args.symbols,
        days_back=args.days,
        timeframes=args.timeframes,
        fetch_sentiment=not args.no_sentiment
    )
