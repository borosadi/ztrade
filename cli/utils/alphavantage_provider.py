"""Alpha Vantage data provider for historical market data.

This module provides access to Alpha Vantage's comprehensive market data API,
serving as an alternative to Alpaca's limited paper trading data access.

Features:
- Intraday bars (1min, 5min, 15min, 30min, 60min)
- Daily, weekly, monthly bars
- Extended history (20+ years for stocks)
- Crypto data (BTC, ETH, etc.)
- Free tier: 25 API calls/day (or premium with higher limits)

Integration:
- MCP server for Claude Code interactions
- Direct API client for programmatic access
- Compatible with existing backfill_historical_data.py script
"""

import os
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd

from cli.utils.logger import get_logger

logger = get_logger(__name__)


class AlphaVantageProvider:
    """Alpha Vantage market data provider."""

    BASE_URL = "https://www.alphavantage.co/query"

    # API rate limits
    CALLS_PER_MINUTE_FREE = 5
    CALLS_PER_DAY_FREE = 25

    # Timeframe mapping
    INTRADAY_INTERVALS = {
        '1m': '1min',
        '5m': '5min',
        '15m': '15min',
        '30m': '30min',
        '1h': '60min'
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Alpha Vantage provider.

        Args:
            api_key: Alpha Vantage API key. If not provided, reads from env.
        """
        self.api_key = api_key or os.getenv('ALPHAVANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Alpha Vantage API key required. Set ALPHAVANTAGE_API_KEY "
                "environment variable or pass api_key parameter."
            )

        self.last_request_time = 0
        self.requests_today = 0
        self.daily_limit_reset = datetime.now().date()

        logger.info(f"Alpha Vantage provider initialized")

    def _rate_limit(self):
        """Enforce rate limits (5 calls/min for free tier)."""
        now = time.time()

        # Reset daily counter if new day
        if datetime.now().date() > self.daily_limit_reset:
            self.requests_today = 0
            self.daily_limit_reset = datetime.now().date()

        # Check daily limit
        if self.requests_today >= self.CALLS_PER_DAY_FREE:
            logger.warning(
                f"Daily API limit reached ({self.CALLS_PER_DAY_FREE} calls). "
                f"Consider upgrading or waiting until tomorrow."
            )
            raise RuntimeError("Alpha Vantage daily API limit reached")

        # Enforce 12-second delay between calls (5 calls/min)
        elapsed = now - self.last_request_time
        if elapsed < 12:
            sleep_time = 12 - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        self.requests_today += 1
        logger.debug(
            f"API call {self.requests_today}/{self.CALLS_PER_DAY_FREE} today"
        )

    def _make_request(self, params: Dict) -> Dict:
        """Make API request with error handling.

        Args:
            params: Query parameters

        Returns:
            JSON response
        """
        self._rate_limit()

        params['apikey'] = self.api_key

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage error: {data['Error Message']}")

            if "Note" in data:
                # Rate limit message
                logger.warning(f"Alpha Vantage: {data['Note']}")
                raise RuntimeError("Alpha Vantage rate limit exceeded")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Alpha Vantage API request failed: {e}")
            raise

    def get_intraday_bars(
        self,
        symbol: str,
        interval: str = '5m',
        outputsize: str = 'full'
    ) -> pd.DataFrame:
        """Fetch intraday bars.

        Args:
            symbol: Stock symbol (e.g., 'TSLA')
            interval: Timeframe ('1m', '5m', '15m', '30m', '1h')
            outputsize: 'compact' (100 bars) or 'full' (multiple days)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if interval not in self.INTRADAY_INTERVALS:
            raise ValueError(
                f"Invalid interval: {interval}. "
                f"Must be one of {list(self.INTRADAY_INTERVALS.keys())}"
            )

        av_interval = self.INTRADAY_INTERVALS[interval]

        logger.info(
            f"Fetching {symbol} intraday data (interval={interval}, "
            f"outputsize={outputsize})"
        )

        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': av_interval,
            'outputsize': outputsize,
            'datatype': 'json'
        }

        data = self._make_request(params)

        # Parse time series data
        time_series_key = f'Time Series ({av_interval})'
        if time_series_key not in data:
            raise ValueError(f"No time series data in response for {symbol}")

        time_series = data[time_series_key]

        # Convert to DataFrame
        rows = []
        for timestamp_str, values in time_series.items():
            rows.append({
                'timestamp': pd.to_datetime(timestamp_str),
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': int(values['5. volume'])
            })

        df = pd.DataFrame(rows)
        df = df.sort_values('timestamp')

        logger.info(f"Fetched {len(df)} bars for {symbol}")

        return df

    def get_daily_bars(
        self,
        symbol: str,
        outputsize: str = 'full'
    ) -> pd.DataFrame:
        """Fetch daily bars.

        Args:
            symbol: Stock symbol
            outputsize: 'compact' (100 days) or 'full' (20+ years)

        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Fetching {symbol} daily data (outputsize={outputsize})")

        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': outputsize,
            'datatype': 'json'
        }

        data = self._make_request(params)

        time_series = data.get('Time Series (Daily)', {})
        if not time_series:
            raise ValueError(f"No daily data in response for {symbol}")

        rows = []
        for timestamp_str, values in time_series.items():
            rows.append({
                'timestamp': pd.to_datetime(timestamp_str),
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': int(values['5. volume'])
            })

        df = pd.DataFrame(rows)
        df = df.sort_values('timestamp')

        logger.info(f"Fetched {len(df)} daily bars for {symbol}")

        return df

    def get_crypto_intraday(
        self,
        symbol: str,
        market: str = 'USD',
        interval: str = '1h'
    ) -> pd.DataFrame:
        """Fetch crypto intraday bars.

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            market: Market currency ('USD', 'EUR', etc.)
            interval: Timeframe ('1m', '5m', '15m', '30m', '1h')

        Returns:
            DataFrame with OHLCV data
        """
        if interval not in self.INTRADAY_INTERVALS:
            raise ValueError(f"Invalid interval: {interval}")

        av_interval = self.INTRADAY_INTERVALS[interval]

        logger.info(
            f"Fetching {symbol}/{market} crypto data (interval={interval})"
        )

        params = {
            'function': 'CRYPTO_INTRADAY',
            'symbol': symbol,
            'market': market,
            'interval': av_interval,
            'outputsize': 'full',
            'datatype': 'json'
        }

        data = self._make_request(params)

        time_series_key = f'Time Series Crypto ({av_interval})'
        time_series = data.get(time_series_key, {})
        if not time_series:
            raise ValueError(f"No crypto data in response for {symbol}/{market}")

        rows = []
        for timestamp_str, values in time_series.items():
            rows.append({
                'timestamp': pd.to_datetime(timestamp_str),
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': float(values['5. volume'])
            })

        df = pd.DataFrame(rows)
        df = df.sort_values('timestamp')

        logger.info(f"Fetched {len(df)} crypto bars for {symbol}/{market}")

        return df

    def get_crypto_daily(
        self,
        symbol: str,
        market: str = 'USD'
    ) -> pd.DataFrame:
        """Fetch crypto daily bars.

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            market: Market currency ('USD', 'EUR', etc.)

        Returns:
            DataFrame with OHLCV data

        Note:
            This endpoint is available on the FREE tier (unlike crypto intraday).
            Returns approximately 350+ days of daily data.
        """
        logger.info(
            f"Fetching {symbol}/{market} daily crypto data"
        )

        params = {
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': symbol,
            'market': market
        }

        data = self._make_request(params)

        time_series_key = 'Time Series (Digital Currency Daily)'
        time_series = data.get(time_series_key, {})
        if not time_series:
            raise ValueError(f"No daily crypto data in response for {symbol}/{market}")

        rows = []
        for timestamp_str, values in time_series.items():
            rows.append({
                'timestamp': pd.to_datetime(timestamp_str),
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': float(values['5. volume'])
            })

        df = pd.DataFrame(rows)
        df = df.sort_values('timestamp')

        logger.info(f"Fetched {len(df)} daily crypto bars for {symbol}/{market}")

        return df

    def get_bars_for_timeframe(
        self,
        symbol: str,
        timeframe: str,
        days: int = 60
    ) -> pd.DataFrame:
        """Fetch bars for a specific timeframe (convenience method).

        This method intelligently chooses the right API endpoint based on
        the requested timeframe and filters to the requested date range.

        Args:
            symbol: Symbol to fetch (stocks: 'TSLA', crypto: 'BTC/USD')
            timeframe: Timeframe ('5m', '15m', '1h', '1d')
            days: Number of days of history to fetch

        Returns:
            DataFrame with OHLCV data
        """
        # Parse crypto symbols
        is_crypto = '/' in symbol
        if is_crypto:
            crypto_symbol, market = symbol.split('/')

            if timeframe == '1d':
                # Use daily crypto endpoint (FREE tier)
                df = self.get_crypto_daily(crypto_symbol, market)
            else:
                # Intraday crypto data requires PREMIUM subscription
                df = self.get_crypto_intraday(
                    crypto_symbol,
                    market,
                    interval=timeframe
                )
        else:
            # Stock symbol
            if timeframe == '1d':
                df = self.get_daily_bars(symbol, outputsize='full')
            elif timeframe in self.INTRADAY_INTERVALS:
                df = self.get_intraday_bars(symbol, interval=timeframe)
            else:
                raise ValueError(f"Unsupported timeframe: {timeframe}")

        # Filter to requested date range
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df['timestamp'] >= cutoff_date]

        logger.info(
            f"Filtered to {len(df)} bars within last {days} days for {symbol}"
        )

        return df


# Singleton instance
_alphavantage_provider = None


def get_alphavantage_provider() -> AlphaVantageProvider:
    """Get singleton Alpha Vantage provider instance.

    Returns:
        AlphaVantageProvider instance
    """
    global _alphavantage_provider

    if _alphavantage_provider is None:
        _alphavantage_provider = AlphaVantageProvider()

    return _alphavantage_provider
