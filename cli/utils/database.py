"""Database utilities for historical data storage."""
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from contextlib import contextmanager

from cli.utils.logger import get_logger

logger = get_logger(__name__)


def get_database_url() -> str:
    """Get database URL from environment."""
    return os.getenv(
        'DATABASE_URL',
        'postgresql://ztrade:ztrade_dev_password@localhost:5432/ztrade'
    )


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = psycopg2.connect(get_database_url())
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


class MarketDataStore:
    """Store for historical market data."""

    @staticmethod
    def insert_bar(
        symbol: str,
        timestamp: datetime,
        timeframe: str,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: int,
        vwap: Optional[float] = None,
        trade_count: Optional[int] = None
    ) -> bool:
        """Insert a single market bar."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO market_bars
                        (symbol, timestamp, timeframe, open, high, low, close, volume, vwap, trade_count)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timestamp, timeframe) DO UPDATE SET
                            open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume,
                            vwap = EXCLUDED.vwap,
                            trade_count = EXCLUDED.trade_count
                    """, (
                        symbol, timestamp, timeframe,
                        open_price, high, low, close,
                        volume, vwap, trade_count
                    ))
            return True
        except Exception as e:
            logger.error(f"Error inserting bar for {symbol}: {e}")
            return False

    @staticmethod
    def insert_bars_bulk(bars: List[Dict[str, Any]]) -> int:
        """
        Insert multiple bars in bulk.

        Args:
            bars: List of bar dictionaries with keys:
                  symbol, timestamp, timeframe, open, high, low, close, volume, vwap, trade_count

        Returns:
            Number of bars inserted
        """
        if not bars:
            return 0

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Prepare values for bulk insert
                    values = [
                        (
                            bar['symbol'],
                            bar['timestamp'],
                            bar['timeframe'],
                            bar.get('open'),
                            bar.get('high'),
                            bar.get('low'),
                            bar.get('close'),
                            bar.get('volume'),
                            bar.get('vwap'),
                            bar.get('trade_count')
                        )
                        for bar in bars
                    ]

                    # Bulk insert with ON CONFLICT
                    execute_values(
                        cur,
                        """
                        INSERT INTO market_bars
                        (symbol, timestamp, timeframe, open, high, low, close, volume, vwap, trade_count)
                        VALUES %s
                        ON CONFLICT (symbol, timestamp, timeframe) DO NOTHING
                        """,
                        values
                    )

            logger.info(f"Inserted {len(bars)} bars")
            return len(bars)

        except Exception as e:
            logger.error(f"Error bulk inserting bars: {e}")
            return 0

    @staticmethod
    def get_latest_bars(
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get latest bars for a symbol."""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT symbol, timestamp, timeframe, open, high, low, close, volume, vwap, trade_count
                        FROM market_bars
                        WHERE symbol = %s AND timeframe = %s
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """, (symbol, timeframe, limit))

                    return [dict(row) for row in cur.fetchall()]

        except Exception as e:
            logger.error(f"Error fetching bars for {symbol}: {e}")
            return []


class SentimentDataStore:
    """Store for historical sentiment data."""

    @staticmethod
    def insert_sentiment(
        symbol: str,
        timestamp: datetime,
        source: str,
        sentiment: str,
        score: float,
        confidence: float,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Insert a single sentiment record."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO sentiment_history
                        (symbol, timestamp, source, sentiment, score, confidence, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timestamp, source) DO UPDATE SET
                            sentiment = EXCLUDED.sentiment,
                            score = EXCLUDED.score,
                            confidence = EXCLUDED.confidence,
                            metadata = EXCLUDED.metadata
                    """, (
                        symbol, timestamp, source, sentiment,
                        score, confidence, psycopg2.extras.Json(metadata or {})
                    ))
            return True
        except Exception as e:
            logger.error(f"Error inserting sentiment for {symbol}/{source}: {e}")
            return False

    @staticmethod
    def insert_sentiments_bulk(sentiments: List[Dict[str, Any]]) -> int:
        """
        Insert multiple sentiment records in bulk.

        Args:
            sentiments: List of sentiment dictionaries

        Returns:
            Number of records inserted
        """
        if not sentiments:
            return 0

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    values = [
                        (
                            s['symbol'],
                            s['timestamp'],
                            s['source'],
                            s['sentiment'],
                            s['score'],
                            s['confidence'],
                            psycopg2.extras.Json(s.get('metadata', {}))
                        )
                        for s in sentiments
                    ]

                    execute_values(
                        cur,
                        """
                        INSERT INTO sentiment_history
                        (symbol, timestamp, source, sentiment, score, confidence, metadata)
                        VALUES %s
                        ON CONFLICT (symbol, timestamp, source) DO NOTHING
                        """,
                        values
                    )

            logger.info(f"Inserted {len(sentiments)} sentiment records")
            return len(sentiments)

        except Exception as e:
            logger.error(f"Error bulk inserting sentiments: {e}")
            return 0

    @staticmethod
    def get_latest_sentiment(
        symbol: str,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get latest sentiment for a symbol."""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if source:
                        cur.execute("""
                            SELECT symbol, timestamp, source, sentiment, score, confidence, metadata
                            FROM sentiment_history
                            WHERE symbol = %s AND source = %s
                            ORDER BY timestamp DESC
                            LIMIT %s
                        """, (symbol, source, limit))
                    else:
                        cur.execute("""
                            SELECT symbol, timestamp, source, sentiment, score, confidence, metadata
                            FROM sentiment_history
                            WHERE symbol = %s
                            ORDER BY timestamp DESC
                            LIMIT %s
                        """, (symbol, limit))

                    return [dict(row) for row in cur.fetchall()]

        except Exception as e:
            logger.error(f"Error fetching sentiment for {symbol}: {e}")
            return []


# Singleton instances
market_data_store = MarketDataStore()
sentiment_data_store = SentimentDataStore()
