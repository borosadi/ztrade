"""
Airflow DAG for Agent IWM - Russell 2000 Small-Cap Trading

This DAG orchestrates the complete trading pipeline:
1. Fetch market data (price, bars)
2. Analyze sentiment (news, reddit, SEC)
3. Perform technical analysis
4. Make algorithmic decision
5. Execute trade (if buy/sell)
6. Log performance

Schedule: Every 5 minutes during market hours
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.time_sensor import TimeSensor
from airflow.utils.dates import days_ago
import sys
import os

# Add Ztrade to Python path
sys.path.insert(0, '/opt/airflow/ztrade')

# Import Ztrade modules
from ztrade.broker import get_broker
from ztrade.market_data import get_market_data_provider
from ztrade.decision.algorithmic import get_algorithmic_decision_maker
from ztrade.execution.risk import RiskValidator
from ztrade.execution.trade_executor import TradeExecutor
from ztrade.core.config import get_config
from ztrade.core.logger import get_logger
from ztrade.core.database import market_data_store, sentiment_data_store, decision_data_store

logger = get_logger(__name__)

# Agent configuration
AGENT_ID = 'agent_roku'
ASSET = 'ROKU'
INTERVAL_MINUTES = 15

# Default DAG arguments
default_args = {
    'owner': 'ztrade',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(seconds=30),
}

def is_market_hours(**context):
    """Check if current time is within market hours (9:30 AM - 4:00 PM EST)."""
    from datetime import datetime, time
    import pytz

    est = pytz.timezone('America/New_York')
    now = datetime.now(est).time()

    market_open = time(9, 30)
    market_close = time(16, 0)

    is_open = market_open <= now < market_close
    logger.info(f"Market hours check: {now} EST, market_open={is_open}")

    if not is_open:
        raise Exception(f"Market closed: current time {now} EST")

    return is_open

def fetch_market_data(**context):
    """Task 1: Fetch current market data for IWM and save to database."""
    logger.info(f"[{AGENT_ID}] Fetching market data for {ASSET}")

    broker = get_broker()
    config = get_config()
    agent_config = config.load_agent_config(AGENT_ID)
    timeframe = agent_config.get('strategy', {}).get('timeframe', '15m')

    # Get current quote
    quote = broker.get_latest_quote(ASSET)

    if not quote:
        raise ValueError(f"Could not fetch quote for {ASSET}")

    current_price = float(quote.get('ask') or quote.get('bid'))
    logger.info(f"[{AGENT_ID}] Current price: ${current_price:.2f}")

    # Fetch and save latest bars to database
    try:
        # Fetch latest 10 bars (to ensure we get at least 1 new bar)
        bars = broker.get_bars(ASSET, timeframe=timeframe, limit=10)

        if bars:
            # Save bars to database
            bars_to_insert = []
            for bar in bars:
                bars_to_insert.append({
                    'symbol': ASSET,
                    'timestamp': bar['timestamp'],
                    'timeframe': timeframe,
                    'open': bar['open'],
                    'high': bar['high'],
                    'low': bar['low'],
                    'close': bar['close'],
                    'volume': bar['volume'],
                    'vwap': None,
                    'trade_count': None
                })

            if bars_to_insert:
                inserted_count = market_data_store.insert_bars_bulk(bars_to_insert)
                logger.info(f"[{AGENT_ID}] Saved {inserted_count} bars to database (timeframe: {timeframe})")
        else:
            logger.warning(f"[{AGENT_ID}] No bars fetched from broker")

    except Exception as e:
        logger.error(f"[{AGENT_ID}] Error fetching/saving bars: {e}")

    # Push to XCom for next tasks
    context['task_instance'].xcom_push(key='current_price', value=current_price)
    context['task_instance'].xcom_push(key='asset', value=ASSET)

    return current_price

def analyze_sentiment(**context):
    """Task 2: Analyze multi-source sentiment (news, reddit, SEC) and save to database."""
    logger.info(f"[{AGENT_ID}] Analyzing sentiment for {ASSET}")

    market_provider = get_market_data_provider()
    config = get_config()
    agent_config = config.load_agent_config(AGENT_ID)
    timeframe = agent_config.get('strategy', {}).get('timeframe', '5m')

    # Get market context (includes sentiment)
    market_context = market_provider.get_market_context(ASSET, timeframe)
    sentiment = market_context.get('sentiment', {})

    logger.info(
        f"[{AGENT_ID}] Sentiment: score={sentiment.get('sentiment_score', 0):.3f}, "
        f"confidence={sentiment.get('confidence', 0):.2%}"
    )

    # Save sentiment data to database (one record per source)
    try:
        from datetime import datetime
        timestamp = datetime.now()
        source_breakdown = sentiment.get('source_breakdown', {})

        saved_count = 0
        for source_name, source_data in source_breakdown.items():
            if isinstance(source_data, dict):
                source_sentiment = source_data.get('overall_sentiment', 'neutral')
                source_score = source_data.get('sentiment_score', 0.0)
                source_confidence = source_data.get('confidence', 0.0)

                # Save to database
                success = sentiment_data_store.insert_sentiment(
                    symbol=ASSET,
                    timestamp=timestamp,
                    source=source_name,
                    sentiment=source_sentiment,
                    score=source_score,
                    confidence=source_confidence,
                    metadata=source_data  # Save full details
                )

                if success:
                    saved_count += 1

        if saved_count > 0:
            logger.info(f"[{AGENT_ID}] Saved {saved_count} sentiment records to database")
    except Exception as e:
        logger.error(f"[{AGENT_ID}] Error saving sentiment data: {e}")

    # Push to XCom
    context['task_instance'].xcom_push(key='sentiment_score', value=sentiment.get('sentiment_score', 0.0))
    context['task_instance'].xcom_push(key='sentiment_confidence', value=sentiment.get('confidence', 0.0))
    context['task_instance'].xcom_push(key='sentiment_sources', value=sentiment.get('sources_used', []))

    return sentiment

def analyze_technical(**context):
    """Task 3: Perform technical analysis (RSI, SMA, trend, volume)."""
    logger.info(f"[{AGENT_ID}] Performing technical analysis for {ASSET}")

    market_provider = get_market_data_provider()
    config = get_config()
    agent_config = config.load_agent_config(AGENT_ID)
    timeframe = agent_config.get('strategy', {}).get('timeframe', '5m')

    # Get market context (includes technical analysis)
    market_context = market_provider.get_market_context(ASSET, timeframe)
    technical = market_context.get('technical', {})

    logger.info(
        f"[{AGENT_ID}] Technical: signal={technical.get('signal', 'neutral')}, "
        f"confidence={technical.get('confidence', 0):.2%}"
    )

    # Push to XCom
    context['task_instance'].xcom_push(key='technical_signal', value=technical.get('signal', 'neutral'))
    context['task_instance'].xcom_push(key='technical_confidence', value=technical.get('confidence', 0.0))

    return technical

def make_decision(**context):
    """Task 4: Make algorithmic trading decision based on sentiment + technical."""
    logger.info(f"[{AGENT_ID}] Making algorithmic decision")

    ti = context['task_instance']

    # Pull data from previous tasks
    current_price = ti.xcom_pull(task_ids='fetch_market_data', key='current_price')
    sentiment_score = ti.xcom_pull(task_ids='analyze_sentiment', key='sentiment_score')
    sentiment_confidence = ti.xcom_pull(task_ids='analyze_sentiment', key='sentiment_confidence')
    technical_signal = ti.xcom_pull(task_ids='analyze_technical', key='technical_signal')
    technical_confidence = ti.xcom_pull(task_ids='analyze_technical', key='technical_confidence')

    # Load agent config
    config = get_config()
    agent_config = config.load_agent_config(AGENT_ID)

    # Make decision using algorithmic decision maker
    decision_maker = get_algorithmic_decision_maker(
        sentiment_weight=0.6,
        technical_weight=0.4
    )

    decision = decision_maker.make_decision(
        sentiment_score=sentiment_score,
        sentiment_confidence=sentiment_confidence,
        technical_signal=technical_signal,
        technical_confidence=technical_confidence,
        current_price=current_price,
        agent_config=agent_config
    )

    logger.info(
        f"[{AGENT_ID}] Decision: {decision.get('decision', 'hold').upper()} "
        f"(confidence: {decision.get('confidence', 0):.1%})"
    )
    logger.info(f"[{AGENT_ID}] Rationale: {decision.get('rationale', 'N/A')}")

    # Save decision to database
    try:
        from datetime import datetime
        sentiment_sources = ti.xcom_pull(task_ids='analyze_sentiment', key='sentiment_sources')

        decision_data_store.insert_decision(
            timestamp=datetime.now(),
            agent_id=AGENT_ID,
            symbol=ASSET,
            decision=decision.get('decision', 'hold'),
            confidence=decision.get('confidence', 0.0),
            sentiment_score=sentiment_score,
            sentiment_confidence=sentiment_confidence,
            sentiment_sources=sentiment_sources,
            technical_signal=technical_signal,
            technical_confidence=technical_confidence,
            quantity=decision.get('quantity', 0),
            price=current_price,
            stop_loss=decision.get('stop_loss'),
            rationale=decision.get('rationale', ''),
            trade_approved=False,  # Will be updated by validate_risk task
            rejection_reason=None,
            trade_executed=False,  # Will be updated by execute_trade task
            order_id=None
        )
        logger.info(f"[{AGENT_ID}] Decision logged to database")
    except Exception as e:
        logger.error(f"[{AGENT_ID}] Error logging decision to database: {e}")

    # Push to XCom
    context['task_instance'].xcom_push(key='decision', value=decision.get('decision', 'hold'))
    context['task_instance'].xcom_push(key='quantity', value=decision.get('quantity', 0))
    context['task_instance'].xcom_push(key='confidence', value=decision.get('confidence', 0.0))
    context['task_instance'].xcom_push(key='stop_loss', value=decision.get('stop_loss'))
    context['task_instance'].xcom_push(key='rationale', value=decision.get('rationale', ''))

    return decision

def validate_risk(**context):
    """Task 5: Validate decision against risk rules."""
    logger.info(f"[{AGENT_ID}] Validating against risk rules")

    ti = context['task_instance']

    # Pull decision data
    decision = ti.xcom_pull(task_ids='make_decision', key='decision')
    quantity = ti.xcom_pull(task_ids='make_decision', key='quantity')
    confidence = ti.xcom_pull(task_ids='make_decision', key='confidence')
    current_price = ti.xcom_pull(task_ids='fetch_market_data', key='current_price')

    # Skip validation if HOLD
    if decision == 'hold':
        logger.info(f"[{AGENT_ID}] Decision is HOLD, skipping risk validation")
        context['task_instance'].xcom_push(key='trade_approved', value=False)
        return False

    # Load agent config
    config = get_config()
    agent_config = config.load_agent_config(AGENT_ID)
    agent_state = config.load_agent_state(AGENT_ID)

    # Validate
    validator = RiskValidator()
    is_valid, reason = validator.validate_trade(
        agent_id=AGENT_ID,
        action=decision,
        asset=ASSET,
        quantity=quantity,
        price=current_price,
        agent_config=agent_config,
        agent_state=agent_state
    )

    if is_valid:
        logger.info(f"[{AGENT_ID}] ✓ Trade validated")
        context['task_instance'].xcom_push(key='trade_approved', value=True)
    else:
        logger.warning(f"[{AGENT_ID}] ✗ Trade rejected: {reason}")
        context['task_instance'].xcom_push(key='trade_approved', value=False)
        context['task_instance'].xcom_push(key='rejection_reason', value=reason)

    return is_valid

def execute_trade(**context):
    """Task 6: Execute the trade if approved."""
    logger.info(f"[{AGENT_ID}] Executing trade")

    ti = context['task_instance']

    # Check if trade was approved
    trade_approved = ti.xcom_pull(task_ids='validate_risk', key='trade_approved')

    if not trade_approved:
        logger.info(f"[{AGENT_ID}] Trade not approved, skipping execution")
        return None

    # Pull trade details
    decision = ti.xcom_pull(task_ids='make_decision', key='decision')
    quantity = ti.xcom_pull(task_ids='make_decision', key='quantity')
    current_price = ti.xcom_pull(task_ids='fetch_market_data', key='current_price')
    stop_loss = ti.xcom_pull(task_ids='make_decision', key='stop_loss')

    # Execute trade
    executor = TradeExecutor()
    broker = get_broker()

    config = get_config()
    agent_config = config.load_agent_config(AGENT_ID)

    result = executor.execute_trade(
        broker=broker,
        action=decision,
        asset=ASSET,
        quantity=quantity,
        price=current_price,
        agent_id=AGENT_ID,
        agent_config=agent_config,
        dry_run=False  # Set to True for testing
    )

    if result['success']:
        logger.info(f"[{AGENT_ID}] ✓ Trade executed successfully: {result.get('order_id')}")
        context['task_instance'].xcom_push(key='trade_executed', value=True)
        context['task_instance'].xcom_push(key='order_id', value=result.get('order_id'))
    else:
        logger.error(f"[{AGENT_ID}] ✗ Trade execution failed: {result.get('error')}")
        context['task_instance'].xcom_push(key='trade_executed', value=False)
        context['task_instance'].xcom_push(key='error', value=result.get('error'))

    return result

def log_performance(**context):
    """Task 7: Log the trading cycle performance metrics."""
    logger.info(f"[{AGENT_ID}] Logging performance metrics")

    ti = context['task_instance']

    # Gather all metrics
    metrics = {
        'timestamp': context['ts'],
        'agent_id': AGENT_ID,
        'asset': ASSET,
        'current_price': ti.xcom_pull(task_ids='fetch_market_data', key='current_price'),
        'sentiment_score': ti.xcom_pull(task_ids='analyze_sentiment', key='sentiment_score'),
        'sentiment_confidence': ti.xcom_pull(task_ids='analyze_sentiment', key='sentiment_confidence'),
        'technical_signal': ti.xcom_pull(task_ids='analyze_technical', key='technical_signal'),
        'technical_confidence': ti.xcom_pull(task_ids='analyze_technical', key='technical_confidence'),
        'decision': ti.xcom_pull(task_ids='make_decision', key='decision'),
        'confidence': ti.xcom_pull(task_ids='make_decision', key='confidence'),
        'trade_approved': ti.xcom_pull(task_ids='validate_risk', key='trade_approved'),
        'trade_executed': ti.xcom_pull(task_ids='execute_trade', key='trade_executed'),
    }

    logger.info(f"[{AGENT_ID}] Performance metrics: {metrics}")

    # TODO: Store metrics in database or monitoring system

    return metrics

# Define the DAG
dag = DAG(
    dag_id='agent_roku_trading',
    default_args=default_args,
    description='IWM sentiment_momentum trading agent - 15-minute cycles',
    schedule_interval=f'*/{INTERVAL_MINUTES} 14-20 * * 1-5',  # Every 15 min, 9 AM-4 PM EST (14-21 UTC), Mon-Fri
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=['trading', 'roku', 'sentiment_momentum', 'algorithmic'],
)

# Task 0: Check if market is open
check_market_hours = PythonOperator(
    task_id='check_market_hours',
    python_callable=is_market_hours,
    dag=dag,
)

# Task 1: Fetch market data
task_fetch_data = PythonOperator(
    task_id='fetch_market_data',
    python_callable=fetch_market_data,
    dag=dag,
)

# Task 2: Analyze sentiment
task_sentiment = PythonOperator(
    task_id='analyze_sentiment',
    python_callable=analyze_sentiment,
    dag=dag,
)

# Task 3: Analyze technical
task_technical = PythonOperator(
    task_id='analyze_technical',
    python_callable=analyze_technical,
    dag=dag,
)

# Task 4: Make decision
task_decision = PythonOperator(
    task_id='make_decision',
    python_callable=make_decision,
    dag=dag,
)

# Task 5: Validate risk
task_risk = PythonOperator(
    task_id='validate_risk',
    python_callable=validate_risk,
    dag=dag,
)

# Task 6: Execute trade
task_execute = PythonOperator(
    task_id='execute_trade',
    python_callable=execute_trade,
    dag=dag,
)

# Task 7: Log performance
task_log = PythonOperator(
    task_id='log_performance',
    python_callable=log_performance,
    dag=dag,
)

# Define task dependencies (pipeline flow)
check_market_hours >> task_fetch_data
task_fetch_data >> [task_sentiment, task_technical]
[task_sentiment, task_technical] >> task_decision
task_decision >> task_risk >> task_execute >> task_log
