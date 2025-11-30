"""
Factory for creating trading DAGs with identical pipeline structure.

This module eliminates code duplication across all trading agent DAGs by
providing a single implementation of the 7-task trading pipeline.

Usage:
    from trading_dag_factory import create_trading_dag

    dag = create_trading_dag(
        agent_id='agent_tsla',
        asset='TSLA',
        interval_minutes=5,
        schedule='*/5 14-20 * * 1-5',
        tags=['trading', 'tsla', 'momentum'],
        is_crypto=False
    )
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import ztrade_setup  # Shared path setup

# Import Ztrade modules
from ztrade.broker import get_broker
from ztrade.market_data import get_market_data_provider
from ztrade.decision.algorithmic import get_algorithmic_decision_maker
from ztrade.execution.risk import RiskValidator
from ztrade.execution.trade_executor import TradeExecutor
from ztrade.core.config import get_config
from ztrade.core.logger import get_logger


# Default DAG arguments
DEFAULT_ARGS = {
    'owner': 'ztrade',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(seconds=30),
}


def create_market_hours_check(agent_id, is_crypto):
    """Create market hours check function for this agent."""
    def is_market_hours(**context):
        """Check if market is open (crypto: always, stocks: market hours)."""
        from datetime import datetime, time
        import pytz
        from ztrade.core.logger import get_logger

        logger = get_logger(__name__)
        est = pytz.timezone('America/New_York')
        now = datetime.now(est)

        if is_crypto:
            logger.info(f"[{agent_id}] Market hours check: {now.strftime('%Y-%m-%d %H:%M:%S')} EST - Crypto trades 24/7")
            return True
        else:
            # Stock market hours: 9:30 AM - 4:00 PM EST
            current_time = now.time()
            market_open = time(9, 30)
            market_close = time(16, 0)

            is_open = market_open <= current_time < market_close
            logger.info(f"[{agent_id}] Market hours check: {now.strftime('%Y-%m-%d %H:%M:%S')} EST, market_open={is_open}")

            if not is_open:
                raise Exception(f"Market closed: current time {current_time} EST")

            return is_open

    return is_market_hours


def create_fetch_market_data(agent_id, asset):
    """Create market data fetching function for this agent."""
    def fetch_market_data(**context):
        """Task 1: Fetch current market data and save to database."""
        from ztrade.core.logger import get_logger
        from ztrade.core.database import market_data_store

        logger = get_logger(__name__)
        logger.info(f"[{agent_id}] Fetching market data for {asset}")

        broker = get_broker()
        config = get_config()
        agent_config = config.load_agent_config(agent_id)
        timeframe = agent_config.get('strategy', {}).get('timeframe', '1h')

        # Get current quote
        quote = broker.get_latest_quote(asset)

        if not quote:
            raise ValueError(f"Could not fetch quote for {asset}")

        current_price = float(quote.get('ask') or quote.get('bid'))
        logger.info(f"[{agent_id}] Current price: ${current_price:.2f}")

        # Fetch and save latest bars to database
        try:
            bars = broker.get_bars(asset, timeframe=timeframe, limit=10)

            if bars:
                bars_to_insert = []
                for bar in bars:
                    bars_to_insert.append({
                        'symbol': asset,
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
                    logger.info(f"[{agent_id}] Saved {inserted_count} bars to database (timeframe: {timeframe})")
            else:
                logger.warning(f"[{agent_id}] No bars fetched from broker")

        except Exception as e:
            logger.error(f"[{agent_id}] Error fetching/saving bars: {e}")

        # Push to XCom for next tasks
        context['task_instance'].xcom_push(key='current_price', value=current_price)
        context['task_instance'].xcom_push(key='asset', value=asset)

        return current_price

    return fetch_market_data


def create_analyze_sentiment(agent_id, asset):
    """Create sentiment analysis function for this agent."""
    def analyze_sentiment(**context):
        """Task 2: Analyze multi-source sentiment and save to database."""
        from ztrade.core.logger import get_logger
        from ztrade.core.database import sentiment_data_store
        from datetime import datetime

        logger = get_logger(__name__)
        logger.info(f"[{agent_id}] Analyzing sentiment for {asset}")

        market_provider = get_market_data_provider()
        config = get_config()
        agent_config = config.load_agent_config(agent_id)
        timeframe = agent_config.get('strategy', {}).get('timeframe', '1h')

        # Get market context (includes sentiment)
        market_context = market_provider.get_market_context(asset, timeframe)
        sentiment = market_context.get('sentiment', {})

        logger.info(
            f"[{agent_id}] Sentiment: score={sentiment.get('sentiment_score', 0):.3f}, "
            f"confidence={sentiment.get('confidence', 0):.2%}"
        )

        # Save sentiment data to database
        try:
            timestamp = datetime.now()
            source_breakdown = sentiment.get('source_breakdown', {})

            saved_count = 0
            for source_name, source_data in source_breakdown.items():
                if isinstance(source_data, dict):
                    success = sentiment_data_store.insert_sentiment(
                        symbol=asset,
                        timestamp=timestamp,
                        source=source_name,
                        sentiment=source_data.get('overall_sentiment', 'neutral'),
                        score=source_data.get('sentiment_score', 0.0),
                        confidence=source_data.get('confidence', 0.0),
                        metadata=source_data
                    )
                    if success:
                        saved_count += 1

            if saved_count > 0:
                logger.info(f"[{agent_id}] Saved {saved_count} sentiment records to database")
        except Exception as e:
            logger.error(f"[{agent_id}] Error saving sentiment data: {e}")

        # Push to XCom
        context['task_instance'].xcom_push(key='sentiment_score', value=sentiment.get('sentiment_score', 0.0))
        context['task_instance'].xcom_push(key='sentiment_confidence', value=sentiment.get('confidence', 0.0))
        context['task_instance'].xcom_push(key='sentiment_sources', value=sentiment.get('sources_used', []))

        return sentiment

    return analyze_sentiment


def create_analyze_technical(agent_id, asset):
    """Create technical analysis function for this agent."""
    def analyze_technical(**context):
        """Task 3: Perform technical analysis."""
        from ztrade.core.logger import get_logger

        logger = get_logger(__name__)
        logger.info(f"[{agent_id}] Performing technical analysis for {asset}")

        market_provider = get_market_data_provider()
        config = get_config()
        agent_config = config.load_agent_config(agent_id)
        timeframe = agent_config.get('strategy', {}).get('timeframe', '1h')

        # Get market context (includes technical analysis)
        market_context = market_provider.get_market_context(asset, timeframe)
        technical = market_context.get('technical', {})

        logger.info(
            f"[{agent_id}] Technical: signal={technical.get('signal', 'neutral')}, "
            f"confidence={technical.get('confidence', 0):.2%}"
        )

        # Push to XCom
        context['task_instance'].xcom_push(key='technical_signal', value=technical.get('signal', 'neutral'))
        context['task_instance'].xcom_push(key='technical_confidence', value=technical.get('confidence', 0.0))

        return technical

    return analyze_technical


def create_make_decision(agent_id, asset):
    """Create decision-making function for this agent."""
    def make_decision(**context):
        """Task 4: Make algorithmic trading decision."""
        from ztrade.core.logger import get_logger
        from ztrade.core.database import decision_data_store
        from datetime import datetime

        logger = get_logger(__name__)
        logger.info(f"[{agent_id}] Making algorithmic decision")

        ti = context['task_instance']

        # Pull data from previous tasks
        current_price = ti.xcom_pull(task_ids='fetch_market_data', key='current_price')
        sentiment_score = ti.xcom_pull(task_ids='analyze_sentiment', key='sentiment_score')
        sentiment_confidence = ti.xcom_pull(task_ids='analyze_sentiment', key='sentiment_confidence')
        technical_signal = ti.xcom_pull(task_ids='analyze_technical', key='technical_signal')
        technical_confidence = ti.xcom_pull(task_ids='analyze_technical', key='technical_confidence')

        # Load agent config
        config = get_config()
        agent_config = config.load_agent_config(agent_id)

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
            f"[{agent_id}] Decision: {decision.get('decision', 'hold').upper()} "
            f"(confidence: {decision.get('confidence', 0):.1%})"
        )
        logger.info(f"[{agent_id}] Rationale: {decision.get('rationale', 'N/A')}")

        # Save decision to database
        try:
            sentiment_sources = ti.xcom_pull(task_ids='analyze_sentiment', key='sentiment_sources')

            decision_data_store.insert_decision(
                timestamp=datetime.now(),
                agent_id=agent_id,
                symbol=asset,
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
                trade_approved=False,
                rejection_reason=None,
                trade_executed=False,
                order_id=None
            )
            logger.info(f"[{agent_id}] Decision logged to database")
        except Exception as e:
            logger.error(f"[{agent_id}] Error logging decision to database: {e}")

        # Push to XCom
        context['task_instance'].xcom_push(key='decision', value=decision.get('decision', 'hold'))
        context['task_instance'].xcom_push(key='quantity', value=decision.get('quantity', 0))
        context['task_instance'].xcom_push(key='confidence', value=decision.get('confidence', 0.0))
        context['task_instance'].xcom_push(key='stop_loss', value=decision.get('stop_loss'))
        context['task_instance'].xcom_push(key='rationale', value=decision.get('rationale', ''))

        return decision

    return make_decision


def create_validate_risk(agent_id, asset):
    """Create risk validation function for this agent."""
    def validate_risk(**context):
        """Task 5: Validate decision against risk rules."""
        from ztrade.core.logger import get_logger

        logger = get_logger(__name__)
        logger.info(f"[{agent_id}] Validating against risk rules")

        ti = context['task_instance']

        # Pull decision data
        decision = ti.xcom_pull(task_ids='make_decision', key='decision')
        quantity = ti.xcom_pull(task_ids='make_decision', key='quantity')
        current_price = ti.xcom_pull(task_ids='fetch_market_data', key='current_price')

        # Skip validation if HOLD
        if decision == 'hold':
            logger.info(f"[{agent_id}] Decision is HOLD, skipping risk validation")
            context['task_instance'].xcom_push(key='trade_approved', value=False)
            return False

        # Load agent config
        config = get_config()
        agent_config = config.load_agent_config(agent_id)
        agent_state = config.load_agent_state(agent_id)

        # Validate
        validator = RiskValidator()
        is_valid, reason = validator.validate_trade(
            agent_id=agent_id,
            action=decision,
            asset=asset,
            quantity=quantity,
            price=current_price,
            agent_config=agent_config,
            agent_state=agent_state
        )

        if is_valid:
            logger.info(f"[{agent_id}] ✓ Trade validated")
            context['task_instance'].xcom_push(key='trade_approved', value=True)
        else:
            logger.warning(f"[{agent_id}] ✗ Trade rejected: {reason}")
            context['task_instance'].xcom_push(key='trade_approved', value=False)
            context['task_instance'].xcom_push(key='rejection_reason', value=reason)

        return is_valid

    return validate_risk


def create_execute_trade(agent_id, asset):
    """Create trade execution function for this agent."""
    def execute_trade(**context):
        """Task 6: Execute the trade if approved."""
        from ztrade.core.logger import get_logger

        logger = get_logger(__name__)
        logger.info(f"[{agent_id}] Executing trade")

        ti = context['task_instance']

        # Check if trade was approved
        trade_approved = ti.xcom_pull(task_ids='validate_risk', key='trade_approved')

        if not trade_approved:
            logger.info(f"[{agent_id}] Trade not approved, skipping execution")
            return None

        # Pull trade details
        decision = ti.xcom_pull(task_ids='make_decision', key='decision')
        quantity = ti.xcom_pull(task_ids='make_decision', key='quantity')
        current_price = ti.xcom_pull(task_ids='fetch_market_data', key='current_price')

        # Execute trade
        executor = TradeExecutor()
        broker = get_broker()

        config = get_config()
        agent_config = config.load_agent_config(agent_id)

        result = executor.execute_trade(
            broker=broker,
            action=decision,
            asset=asset,
            quantity=quantity,
            price=current_price,
            agent_id=agent_id,
            agent_config=agent_config,
            dry_run=False
        )

        if result['success']:
            logger.info(f"[{agent_id}] ✓ Trade executed successfully: {result.get('order_id')}")
            context['task_instance'].xcom_push(key='trade_executed', value=True)
            context['task_instance'].xcom_push(key='order_id', value=result.get('order_id'))
        else:
            logger.error(f"[{agent_id}] ✗ Trade execution failed: {result.get('error')}")
            context['task_instance'].xcom_push(key='trade_executed', value=False)
            context['task_instance'].xcom_push(key='error', value=result.get('error'))

        return result

    return execute_trade


def create_log_performance(agent_id, asset):
    """Create performance logging function for this agent."""
    def log_performance(**context):
        """Task 7: Log the trading cycle performance metrics."""
        from ztrade.core.logger import get_logger

        logger = get_logger(__name__)
        logger.info(f"[{agent_id}] Logging performance metrics")

        ti = context['task_instance']

        # Gather all metrics
        metrics = {
            'timestamp': context['ts'],
            'agent_id': agent_id,
            'asset': asset,
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

        logger.info(f"[{agent_id}] Performance metrics: {metrics}")

        # Store metrics in database
        # (Implementation can be added here when performance tracking table is ready)

        return metrics

    return log_performance


def create_trading_dag(
    agent_id: str,
    asset: str,
    interval_minutes: int,
    schedule: str,
    tags: list,
    is_crypto: bool = False,
    description: str = None
):
    """
    Create a trading DAG for an agent.

    Args:
        agent_id: Agent identifier (e.g., 'agent_tsla')
        asset: Trading asset (e.g., 'TSLA' or 'BTC/USD')
        interval_minutes: Trading interval in minutes
        schedule: Airflow cron schedule
        tags: List of DAG tags
        is_crypto: Whether asset is crypto (24/7) or stock (market hours)
        description: Optional DAG description

    Returns:
        Configured Airflow DAG instance
    """
    # Default description if not provided
    if not description:
        market_type = "crypto" if is_crypto else "stock"
        description = f"{asset} sentiment-momentum trading agent - {interval_minutes}-minute cycles ({market_type})"

    # Create DAG
    dag = DAG(
        dag_id=f'{agent_id}_trading',
        default_args=DEFAULT_ARGS,
        description=description,
        schedule_interval=schedule,
        start_date=days_ago(1),
        catchup=False,
        max_active_runs=1,
        tags=tags,
    )

    # Task 0: Check if market is open
    task_check_hours = PythonOperator(
        task_id='check_market_hours',
        python_callable=create_market_hours_check(agent_id, is_crypto),
        dag=dag,
    )

    # Task 1: Fetch market data
    task_fetch_data = PythonOperator(
        task_id='fetch_market_data',
        python_callable=create_fetch_market_data(agent_id, asset),
        dag=dag,
    )

    # Task 2: Analyze sentiment
    task_sentiment = PythonOperator(
        task_id='analyze_sentiment',
        python_callable=create_analyze_sentiment(agent_id, asset),
        dag=dag,
    )

    # Task 3: Analyze technical
    task_technical = PythonOperator(
        task_id='analyze_technical',
        python_callable=create_analyze_technical(agent_id, asset),
        dag=dag,
    )

    # Task 4: Make decision
    task_decision = PythonOperator(
        task_id='make_decision',
        python_callable=create_make_decision(agent_id, asset),
        dag=dag,
    )

    # Task 5: Validate risk
    task_risk = PythonOperator(
        task_id='validate_risk',
        python_callable=create_validate_risk(agent_id, asset),
        dag=dag,
    )

    # Task 6: Execute trade
    task_execute = PythonOperator(
        task_id='execute_trade',
        python_callable=create_execute_trade(agent_id, asset),
        dag=dag,
    )

    # Task 7: Log performance
    task_log = PythonOperator(
        task_id='log_performance',
        python_callable=create_log_performance(agent_id, asset),
        dag=dag,
    )

    # Define task dependencies (pipeline flow)
    task_check_hours >> task_fetch_data
    task_fetch_data >> [task_sentiment, task_technical]
    [task_sentiment, task_technical] >> task_decision
    task_decision >> task_risk >> task_execute >> task_log

    return dag
