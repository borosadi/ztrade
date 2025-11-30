"""Database utilities for historical data storage (SQLite)."""
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from pathlib import Path

from ztrade.core.logger import get_logger

logger = get_logger(__name__)


def get_database_path() -> str:
    """Get SQLite database file path."""
    # Check environment variable first
    db_path = os.getenv('DATABASE_PATH')
    if db_path:
        return db_path

    # Default to data/ztrade.db in project root
    project_root = Path(__file__).parent.parent.parent
    db_dir = project_root / 'data'
    db_dir.mkdir(exist_ok=True)

    return str(db_dir / 'ztrade.db')


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = None
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Return rows as dictionaries
        conn.row_factory = sqlite3.Row

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
                conn.execute("""
                    INSERT INTO market_bars
                    (symbol, timestamp, timeframe, open, high, low, close, volume, vwap, trade_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (symbol, timestamp, timeframe) DO UPDATE SET
                        open = excluded.open,
                        high = excluded.high,
                        low = excluded.low,
                        close = excluded.close,
                        volume = excluded.volume,
                        vwap = excluded.vwap,
                        trade_count = excluded.trade_count
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
                conn.executemany(
                    """
                    INSERT INTO market_bars
                    (symbol, timestamp, timeframe, open, high, low, close, volume, vwap, trade_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                cursor = conn.execute("""
                    SELECT symbol, timestamp, timeframe, open, high, low, close, volume, vwap, trade_count
                    FROM market_bars
                    WHERE symbol = ? AND timeframe = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (symbol, timeframe, limit))

                return [dict(row) for row in cursor.fetchall()]

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
                # Convert metadata dict to JSON string
                metadata_json = json.dumps(metadata or {})

                conn.execute("""
                    INSERT INTO sentiment_history
                    (symbol, timestamp, source, sentiment, score, confidence, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (symbol, timestamp, source) DO UPDATE SET
                        sentiment = excluded.sentiment,
                        score = excluded.score,
                        confidence = excluded.confidence,
                        metadata = excluded.metadata
                """, (
                    symbol, timestamp, source, sentiment,
                    score, confidence, metadata_json
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
                values = [
                    (
                        s['symbol'],
                        s['timestamp'],
                        s['source'],
                        s['sentiment'],
                        s['score'],
                        s['confidence'],
                        json.dumps(s.get('metadata', {}))
                    )
                    for s in sentiments
                ]

                conn.executemany(
                    """
                    INSERT INTO sentiment_history
                    (symbol, timestamp, source, sentiment, score, confidence, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
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
                if source:
                    cursor = conn.execute("""
                        SELECT symbol, timestamp, source, sentiment, score, confidence, metadata
                        FROM sentiment_history
                        WHERE symbol = ? AND source = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (symbol, source, limit))
                else:
                    cursor = conn.execute("""
                        SELECT symbol, timestamp, source, sentiment, score, confidence, metadata
                        FROM sentiment_history
                        WHERE symbol = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (symbol, limit))

                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    # Parse JSON metadata
                    if row_dict.get('metadata'):
                        try:
                            row_dict['metadata'] = json.loads(row_dict['metadata'])
                        except json.JSONDecodeError:
                            row_dict['metadata'] = {}
                    results.append(row_dict)

                return results

        except Exception as e:
            logger.error(f"Error fetching sentiment for {symbol}: {e}")
            return []


class DecisionDataStore:
    """Store for live trading decision history."""

    @staticmethod
    def insert_decision(
        timestamp: datetime,
        agent_id: str,
        symbol: str,
        decision: str,
        confidence: float,
        sentiment_score: Optional[float] = None,
        sentiment_confidence: Optional[float] = None,
        sentiment_sources: Optional[List[str]] = None,
        technical_signal: Optional[str] = None,
        technical_confidence: Optional[float] = None,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        rationale: Optional[str] = None,
        trade_approved: bool = False,
        rejection_reason: Optional[str] = None,
        trade_executed: bool = False,
        order_id: Optional[str] = None
    ) -> bool:
        """Insert a single decision record."""
        try:
            with get_db_connection() as conn:
                # Convert sentiment sources list to JSON string
                sources_json = json.dumps(sentiment_sources or [])

                conn.execute("""
                    INSERT INTO decision_history
                    (timestamp, agent_id, symbol, decision, confidence,
                     sentiment_score, sentiment_confidence, sentiment_sources,
                     technical_signal, technical_confidence,
                     quantity, price, stop_loss, rationale,
                     trade_approved, rejection_reason, trade_executed, order_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, agent_id, symbol, decision, confidence,
                    sentiment_score, sentiment_confidence, sources_json,
                    technical_signal, technical_confidence,
                    quantity, price, stop_loss, rationale,
                    1 if trade_approved else 0,
                    rejection_reason,
                    1 if trade_executed else 0,
                    order_id
                ))
            return True
        except Exception as e:
            logger.error(f"Error inserting decision for {agent_id}/{symbol}: {e}")
            return False

    @staticmethod
    def get_latest_decisions(
        agent_id: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get latest decisions with optional filters."""
        try:
            with get_db_connection() as conn:
                query = """
                    SELECT timestamp, agent_id, symbol, decision, confidence,
                           sentiment_score, sentiment_confidence, sentiment_sources,
                           technical_signal, technical_confidence,
                           quantity, price, stop_loss, rationale,
                           trade_approved, rejection_reason, trade_executed, order_id,
                           created_at
                    FROM decision_history
                    WHERE 1=1
                """
                params = []

                if agent_id:
                    query += " AND agent_id = ?"
                    params.append(agent_id)

                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor = conn.execute(query, params)

                results = []
                for row in cursor.fetchall():
                    row_dict = dict(row)
                    # Parse JSON sentiment sources
                    if row_dict.get('sentiment_sources'):
                        try:
                            row_dict['sentiment_sources'] = json.loads(row_dict['sentiment_sources'])
                        except json.JSONDecodeError:
                            row_dict['sentiment_sources'] = []
                    # Convert boolean integers to booleans
                    row_dict['trade_approved'] = bool(row_dict.get('trade_approved'))
                    row_dict['trade_executed'] = bool(row_dict.get('trade_executed'))
                    results.append(row_dict)

                return results

        except Exception as e:
            logger.error(f"Error fetching decisions: {e}")
            return []


# Singleton instances
market_data_store = MarketDataStore()
sentiment_data_store = SentimentDataStore()
decision_data_store = DecisionDataStore()
