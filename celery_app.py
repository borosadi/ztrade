"""Celery app for orchestrating trading agent loops with web monitoring."""
import os
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta
from cli.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize Celery app
# Use environment variable for Redis URL, fallback to localhost for local development
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
app = Celery(
    'ztrade',
    broker=redis_url,
    backend=redis_url
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/New_York',  # EST for market hours
    enable_utc=False,
    task_track_started=True,
    task_time_limit=600,  # 10 minute max per task
    worker_prefetch_multiplier=1,  # Process one task at a time
)


@app.task(bind=True, name='ztrade.trading_cycle', max_retries=3)
def trading_cycle(self, agent_id: str, dry_run: bool = True, manual: bool = True):
    """
    Execute a single trading cycle for an agent.

    Args:
        agent_id: ID of the agent to run
        dry_run: If True, simulate trades without execution
        manual: If True, use manual mode (Claude Code terminal)

    Returns:
        Dict with cycle results
    """
    try:
        logger.info(f"Starting Celery trading cycle for {agent_id}")

        # Import here to avoid circular dependencies
        from cli.utils.config import get_config
        from cli.utils.broker import get_broker
        from cli.utils.market_data import get_market_data_provider
        from cli.utils.technical_analyzer import get_technical_analyzer

        # Load agent config
        config = get_config()
        if not config.agent_exists(agent_id):
            raise ValueError(f"Agent {agent_id} not found")

        agent_config = config.load_agent_config(agent_id)
        asset = agent_config.get('agent', {}).get('asset', 'UNKNOWN')

        # Fetch market data
        broker = get_broker()
        quote = broker.get_latest_quote(asset)

        if not quote:
            logger.warning(f"Could not fetch quote for {asset}")
            return {
                'status': 'skipped',
                'reason': 'no_quote',
                'agent_id': agent_id
            }

        current_price = quote.get('ask', 0)

        # Get market context with sentiment
        market_provider = get_market_data_provider()
        timeframe = agent_config.get('strategy', {}).get('timeframe', '15m')
        market_context = market_provider.get_market_context(asset, timeframe)

        # Run technical analysis
        technical_analyzer = get_technical_analyzer()
        technical_analysis = technical_analyzer.analyze(market_context)

        # Log cycle completion
        logger.info(
            f"Cycle completed for {agent_id}: {asset} @ ${current_price:.2f}, "
            f"Signal: {technical_analysis.overall_signal.value}, "
            f"Sentiment: {market_context.get('sentiment', {}).get('overall_sentiment', 'N/A')}"
        )

        return {
            'status': 'success',
            'agent_id': agent_id,
            'asset': asset,
            'price': current_price,
            'signal': technical_analysis.overall_signal.value,
            'sentiment': market_context.get('sentiment', {}).get('overall_sentiment'),
            'sentiment_score': market_context.get('sentiment', {}).get('sentiment_score', 0)
        }

    except Exception as exc:
        logger.error(f"Error in trading cycle for {agent_id}: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@app.task(name='ztrade.test_task')
def test_task():
    """Simple test task to verify Celery is working."""
    logger.info("Test task executed successfully!")
    return {'status': 'success', 'message': 'Celery is working!'}


@app.task(bind=True, name='ztrade.collect_market_bars', max_retries=3)
def collect_market_bars(self, symbols: list = None):
    """
    Collect and store market bars for tracked symbols.

    Args:
        symbols: List of symbols to collect (defaults to all tracked symbols)

    Returns:
        Dict with collection results
    """
    try:
        from cli.utils.database import market_data_store
        from cli.utils.broker import get_broker
        from cli.utils.config import get_config
        from datetime import datetime, timezone

        # Get symbols from config if not provided
        if not symbols:
            config = get_config()
            symbols = [
                config.load_agent_config(agent_id).get('agent', {}).get('asset')
                for agent_id in config.list_agents()
            ]
            symbols = [s for s in symbols if s]  # Filter None

        if not symbols:
            logger.warning("No symbols to collect")
            return {'status': 'skipped', 'reason': 'no_symbols'}

        broker = get_broker()
        total_bars = 0

        for symbol in symbols:
            try:
                # Get 1-minute bars for the last hour
                bars_1m = broker.get_bars(symbol, '1Min', limit=60)

                if bars_1m:
                    # Convert to database format
                    bar_records = []
                    for bar in bars_1m:
                        bar_records.append({
                            'symbol': symbol,
                            'timestamp': bar.get('timestamp', datetime.now(timezone.utc)),
                            'timeframe': '1m',
                            'open': bar.get('open'),
                            'high': bar.get('high'),
                            'low': bar.get('low'),
                            'close': bar.get('close'),
                            'volume': bar.get('volume'),
                            'vwap': bar.get('vwap'),
                            'trade_count': bar.get('trade_count')
                        })

                    # Store in database
                    count = market_data_store.insert_bars_bulk(bar_records)
                    total_bars += count
                    logger.info(f"Collected {count} bars for {symbol}")

            except Exception as e:
                logger.error(f"Error collecting bars for {symbol}: {e}")
                continue

        logger.info(f"Total bars collected: {total_bars}")
        return {
            'status': 'success',
            'symbols': len(symbols),
            'total_bars': total_bars
        }

    except Exception as exc:
        logger.error(f"Error in collect_market_bars: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@app.task(bind=True, name='ztrade.collect_sentiment', max_retries=3)
def collect_sentiment(self, symbols: list = None):
    """
    Collect and store sentiment data for tracked symbols.

    Args:
        symbols: List of symbols to collect (defaults to all tracked symbols)

    Returns:
        Dict with collection results
    """
    try:
        from cli.utils.database import sentiment_data_store
        from cli.utils.sentiment_aggregator import get_sentiment_aggregator
        from cli.utils.config import get_config
        from datetime import datetime, timezone

        # Get symbols from config if not provided
        if not symbols:
            config = get_config()
            symbols = [
                config.load_agent_config(agent_id).get('agent', {}).get('asset')
                for agent_id in config.list_agents()
            ]
            symbols = [s for s in symbols if s]

        if not symbols:
            logger.warning("No symbols to collect sentiment for")
            return {'status': 'skipped', 'reason': 'no_symbols'}

        aggregator = get_sentiment_aggregator()
        total_records = 0
        timestamp = datetime.now(timezone.utc)

        for symbol in symbols:
            try:
                # Get aggregated sentiment (calls all sources)
                result = aggregator.get_aggregated_sentiment(symbol)

                sentiment_records = []

                # Store individual source sentiments
                for source_name, source_data in result.get('source_breakdown', {}).items():
                    if source_data and source_data.get('score') is not None:
                        sentiment_records.append({
                            'symbol': symbol,
                            'timestamp': timestamp,
                            'source': source_name,
                            'sentiment': source_data.get('sentiment', 'neutral'),
                            'score': source_data.get('score', 0.0),
                            'confidence': source_data.get('confidence', 0.0),
                            'metadata': {
                                'article_count': source_data.get('article_count'),
                                'mention_count': source_data.get('mention_count'),
                                'filing_count': source_data.get('filing_count')
                            }
                        })

                if sentiment_records:
                    count = sentiment_data_store.insert_sentiments_bulk(sentiment_records)
                    total_records += count
                    logger.info(f"Collected {count} sentiment records for {symbol}")

            except Exception as e:
                logger.error(f"Error collecting sentiment for {symbol}: {e}")
                continue

        logger.info(f"Total sentiment records collected: {total_records}")
        return {
            'status': 'success',
            'symbols': len(symbols),
            'total_records': total_records
        }

    except Exception as exc:
        logger.error(f"Error in collect_sentiment: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Agent TSLA - Every 5 minutes during market hours
    'agent-tsla-trading-cycle': {
        'task': 'ztrade.trading_cycle',
        'schedule': timedelta(minutes=5),
        'args': ('agent_tsla', True, True),  # dry_run=True, manual=True
        'options': {
            'expires': 240,  # Expire if not executed within 4 minutes
        }
    },

    # Agent IWM - Every 15 minutes during market hours
    'agent-iwm-trading-cycle': {
        'task': 'ztrade.trading_cycle',
        'schedule': timedelta(minutes=15),
        'args': ('agent_iwm', True, True),
        'options': {
            'expires': 840,  # Expire if not executed within 14 minutes
        }
    },

    # Agent BTC - Every 1 hour (24/7 crypto trading)
    'agent-btc-trading-cycle': {
        'task': 'ztrade.trading_cycle',
        'schedule': timedelta(hours=1),
        'args': ('agent_btc', True, True),
        'options': {
            'expires': 3300,  # Expire if not executed within 55 minutes
        }
    },

    # Test task - every minute (for testing)
    'test-task': {
        'task': 'ztrade.test_task',
        'schedule': timedelta(minutes=1),
    },

    # Data collection tasks
    'collect-market-bars': {
        'task': 'ztrade.collect_market_bars',
        'schedule': timedelta(minutes=5),  # Every 5 minutes
        'options': {
            'expires': 240,  # Expire if not executed within 4 minutes
        }
    },

    'collect-sentiment-data': {
        'task': 'ztrade.collect_sentiment',
        'schedule': timedelta(minutes=15),  # Every 15 minutes
        'options': {
            'expires': 840,  # Expire if not executed within 14 minutes
        }
    },
}


if __name__ == '__main__':
    app.start()
