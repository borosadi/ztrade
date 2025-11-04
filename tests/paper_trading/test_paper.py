import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from cli.utils.logger import get_logger
from cli.utils.broker import Broker

logger = get_logger(__name__)

def test_broker_connection():
    broker = Broker()
    account_info = broker.get_account_info()
    assert account_info.status == 'ACTIVE'
    logger.info("Broker connection successful!")
    logger.info(f"Account status: {account_info.status}")

if __name__ == "__main__":
    test_broker_connection()
    broker = Broker()
    try:
        order = broker.submit_order(
            symbol="SPY",
            qty=1,
            side='buy',
            order_type='market',
            time_in_force='day'
        )
        logger.info("Test trade submitted successfully!")
        logger.info(f"Order ID: {order.id}")
    except Exception as e:
        logger.error(f"Error submitting test trade: {e}")
