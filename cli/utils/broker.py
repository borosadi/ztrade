import os
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

load_dotenv()

class Broker:
    def __init__(self):
        self.api = tradeapi.REST(
            os.getenv("ALPACA_API_KEY"),
            os.getenv("ALPACA_SECRET_KEY"),
            os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        )

    def get_account_info(self):
        return self.api.get_account()

    def submit_order(self, symbol, qty, side, order_type, time_in_force):
        return self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force=time_in_force
        )
