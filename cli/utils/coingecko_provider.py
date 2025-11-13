"""CoinGecko market data provider for crypto assets."""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import pandas as pd

from cli.utils.logger import get_logger

logger = get_logger(__name__)


class CoinGeckoProvider:
    """CoinGecko market data provider for crypto."""

    BASE_URL = "https://api.coingecko.com/api/v3"

    # Free tier limits (Demo API key)
    CALLS_PER_MINUTE_FREE = 30
    CALLS_PER_MONTH_FREE = 10000

    # Symbol to CoinGecko ID mapping
    SYMBOL_TO_ID = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'ADA': 'cardano',
        'DOT': 'polkadot',
        'DOGE': 'dogecoin',
        'AVAX': 'avalanche-2',
        'MATIC': 'matic-network',
        'LINK': 'chainlink',
        'UNI': 'uniswap',
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize CoinGecko provider.

        Args:
            api_key: CoinGecko API key (optional, uses COINGECKO_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('COINGECKO_API_KEY')

        if not self.api_key:
            raise ValueError(
                "CoinGecko API key required. Set COINGECKO_API_KEY environment "
                "variable or pass api_key parameter."
            )

        self.session = requests.Session()
        self.last_request_time = 0
        self.requests_this_minute = 0
        self.minute_start = time.time()

        logger.info("CoinGecko provider initialized")

    def _rate_limit(self):
        """Enforce rate limits (30 calls/min for free tier)."""
        current_time = time.time()

        # Reset counter every minute
        if current_time - self.minute_start >= 60:
            self.requests_this_minute = 0
            self.minute_start = current_time

        # Check if we've hit the rate limit
        if self.requests_this_minute >= self.CALLS_PER_MINUTE_FREE:
            wait_time = 60 - (current_time - self.minute_start)
            if wait_time > 0:
                logger.warning(
                    f"Rate limit reached, waiting {wait_time:.1f}s "
                    f"({self.requests_this_minute}/{self.CALLS_PER_MINUTE_FREE} calls/min)"
                )
                time.sleep(wait_time)
                self.requests_this_minute = 0
                self.minute_start = time.time()

        # Minimum 2-second delay between requests (30 calls/min = 1 call every 2s)
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < 2:
            time.sleep(2 - time_since_last_request)

        self.last_request_time = time.time()
        self.requests_this_minute += 1

        logger.debug(
            f"API call {self.requests_this_minute}/{self.CALLS_PER_MINUTE_FREE} this minute"
        )

    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make API request with error handling.

        Args:
            endpoint: API endpoint path (e.g., '/coins/bitcoin/market_chart')
            params: Query parameters

        Returns:
            JSON response
        """
        self._rate_limit()

        url = f"{self.BASE_URL}{endpoint}"

        headers = {
            'accept': 'application/json',
            'x-cg-demo-api-key': self.api_key
        }

        try:
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if isinstance(data, dict) and 'status' in data and 'error_message' in data['status']:
                error_msg = data['status']['error_message']
                error_code = data['status'].get('error_code', 'unknown')
                raise ValueError(f"CoinGecko error {error_code}: {error_msg}")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API request failed: {e}")
            raise

    def _symbol_to_coin_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko coin ID.

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')

        Returns:
            CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
        """
        coin_id = self.SYMBOL_TO_ID.get(symbol.upper())
        if not coin_id:
            raise ValueError(
                f"Unknown crypto symbol: {symbol}. "
                f"Supported: {list(self.SYMBOL_TO_ID.keys())}"
            )
        return coin_id

    def get_market_chart(
        self,
        symbol: str,
        market: str = 'USD',
        days: int = 60
    ) -> pd.DataFrame:
        """Fetch market chart data (price points with volume).

        Note:
            - For 1-90 days: Returns ~hourly price points
            - For 90+ days: Returns daily price points
            - Returns price POINTS (not OHLC candles)

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            market: Market currency ('USD', 'EUR', etc.)
            days: Number of days of history (1-365)

        Returns:
            DataFrame with columns: timestamp, close, volume
        """
        coin_id = self._symbol_to_coin_id(symbol)

        logger.info(
            f"Fetching {symbol}/{market} market chart data ({days} days)"
        )

        params = {
            'vs_currency': market.lower(),
            'days': str(days),
            'precision': 'full'
        }

        endpoint = f'/coins/{coin_id}/market_chart'
        data = self._make_request(endpoint, params)

        prices = data.get('prices', [])
        volumes = data.get('total_volumes', [])

        if not prices:
            raise ValueError(f"No market chart data for {symbol}/{market}")

        rows = []
        for i, (timestamp_ms, price) in enumerate(prices):
            # Match price timestamp with volume timestamp
            volume = 0
            if i < len(volumes) and volumes[i][0] == timestamp_ms:
                volume = volumes[i][1]

            rows.append({
                'timestamp': pd.to_datetime(timestamp_ms, unit='ms'),
                'close': float(price),
                'volume': float(volume)
            })

        df = pd.DataFrame(rows)
        df = df.sort_values('timestamp')

        logger.info(f"Fetched {len(df)} price points for {symbol}/{market}")

        return df

    def get_hourly_bars(
        self,
        symbol: str,
        market: str = 'USD',
        days: int = 60
    ) -> pd.DataFrame:
        """Fetch hourly bars (approximated from price points).

        Note:
            This constructs hourly OHLCV bars from price points where:
            - Open, High, Low, Close all equal the price point
            - Volume is the total volume for that hour
            - This is an approximation - not true OHLC candles

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            market: Market currency ('USD', 'EUR', etc.)
            days: Number of days of history (1-90)

        Returns:
            DataFrame with OHLCV data
        """
        # Get market chart data (price points)
        df = self.get_market_chart(symbol, market, days)

        # Approximate OHLC from price points
        # For each point, O=H=L=C=price
        df['open'] = df['close']
        df['high'] = df['close']
        df['low'] = df['close']

        # Reorder columns to match standard OHLCV format
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        logger.info(
            f"Constructed {len(df)} hourly bars for {symbol}/{market} "
            "(approximated from price points)"
        )

        return df

    def get_bars_for_timeframe(
        self,
        symbol: str,
        timeframe: str,
        days: int = 60
    ) -> pd.DataFrame:
        """Fetch bars for a specific timeframe (convenience method).

        Args:
            symbol: Symbol to fetch (format: 'BTC/USD', 'ETH/USD')
            timeframe: Timeframe ('1h', '4h', '1d')
            days: Number of days of history

        Returns:
            DataFrame with OHLCV data
        """
        # Parse crypto/market from symbol (e.g., 'BTC/USD')
        if '/' not in symbol:
            raise ValueError(f"Symbol must be in format 'CRYPTO/MARKET', got: {symbol}")

        crypto_symbol, market = symbol.split('/')

        if timeframe not in ['1h', '4h', '1d']:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}. "
                "CoinGecko supports: 1h (hourly), 4h (4-hour), 1d (daily)"
            )

        # For 1h: use market chart (hourly price points)
        # For 4h/1d: would need additional aggregation logic
        if timeframe == '1h':
            df = self.get_hourly_bars(crypto_symbol, market, days)
        else:
            # TODO: Implement 4h/1d aggregation if needed
            raise NotImplementedError(
                f"Timeframe {timeframe} not yet implemented. "
                "Currently only '1h' is supported via CoinGecko free tier."
            )

        # Filter to requested date range
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df['timestamp'] >= cutoff_date]

        logger.info(
            f"Filtered to {len(df)} bars within last {days} days for {symbol}"
        )

        return df


# Singleton instance
_coingecko_provider = None


def get_coingecko_provider() -> CoinGeckoProvider:
    """Get singleton CoinGecko provider instance.

    Returns:
        CoinGeckoProvider instance
    """
    global _coingecko_provider

    if _coingecko_provider is None:
        _coingecko_provider = CoinGeckoProvider()

    return _coingecko_provider
