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


# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Agent SPY - Every 5 minutes during market hours
    'agent-spy-trading-cycle': {
        'task': 'ztrade.trading_cycle',
        'schedule': timedelta(minutes=5),
        'args': ('agent_spy', True, True),  # dry_run=True, manual=True
        'options': {
            'expires': 240,  # Expire if not executed within 4 minutes
        }
    },

    # Agent TSLA - Every 5 minutes during market hours
    'agent-tsla-trading-cycle': {
        'task': 'ztrade.trading_cycle',
        'schedule': timedelta(minutes=5),
        'args': ('agent_tsla', True, True),
        'options': {
            'expires': 240,
        }
    },

    # Agent AAPL - Every 1 hour during market hours
    'agent-aapl-trading-cycle': {
        'task': 'ztrade.trading_cycle',
        'schedule': timedelta(hours=1),
        'args': ('agent_aapl', True, True),
        'options': {
            'expires': 3300,  # 55 minutes
        }
    },

    # Test task - every minute (for testing)
    'test-task': {
        'task': 'ztrade.test_task',
        'schedule': timedelta(minutes=1),
    },
}


if __name__ == '__main__':
    app.start()
