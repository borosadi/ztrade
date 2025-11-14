"""Backtesting engine for validating trading strategies against historical data."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json

from cli.utils.database import get_db_connection, market_data_store, sentiment_data_store
from cli.utils.logger import get_logger
from cli.utils.config import get_config
from cli.utils.technical_analyzer import get_technical_analyzer, TechnicalSignal, TechnicalAnalysis, SignalType

logger = get_logger(__name__)


@dataclass
class BacktestPosition:
    """Represents a simulated position in backtesting.

    Supports fractional quantities for crypto assets (e.g., 0.05 BTC).
    """
    symbol: str
    quantity: float  # Changed from int to support fractional shares
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0

    @property
    def value(self) -> float:
        """Current position value."""
        return self.quantity * self.current_price

    @property
    def pnl(self) -> float:
        """Unrealized P&L."""
        return (self.current_price - self.entry_price) * self.quantity

    @property
    def pnl_pct(self) -> float:
        """Unrealized P&L percentage."""
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price * 100


@dataclass
class BacktestPortfolio:
    """Simulated portfolio for backtesting."""
    initial_capital: float
    cash: float
    positions: Dict[str, BacktestPosition] = field(default_factory=dict)
    trade_history: List[Dict] = field(default_factory=list)
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)

    @property
    def positions_value(self) -> float:
        """Total value of all positions."""
        return sum(pos.value for pos in self.positions.values())

    @property
    def total_value(self) -> float:
        """Total portfolio value (cash + positions)."""
        return self.cash + self.positions_value

    @property
    def total_pnl(self) -> float:
        """Total profit/loss."""
        return self.total_value - self.initial_capital

    @property
    def total_return_pct(self) -> float:
        """Total return percentage."""
        if self.initial_capital == 0:
            return 0.0
        return (self.total_value - self.initial_capital) / self.initial_capital * 100

    def can_buy(self, price: float, quantity: float) -> bool:
        """Check if portfolio has enough cash for purchase."""
        cost = price * quantity
        return self.cash >= cost

    def buy(self, symbol: str, price: float, quantity: float, timestamp: datetime) -> bool:
        """Execute buy order (supports fractional shares for crypto)."""
        cost = price * quantity

        if not self.can_buy(price, quantity):
            logger.warning(f"Insufficient cash for {quantity} shares of {symbol} at ${price}")
            return False

        # Deduct cash
        self.cash -= cost

        # Add or update position
        if symbol in self.positions:
            # Average up
            pos = self.positions[symbol]
            total_quantity = pos.quantity + quantity
            total_cost = (pos.entry_price * pos.quantity) + cost
            pos.quantity = total_quantity
            pos.entry_price = total_cost / total_quantity
            pos.current_price = price
        else:
            self.positions[symbol] = BacktestPosition(
                symbol=symbol,
                quantity=quantity,
                entry_price=price,
                entry_time=timestamp,
                current_price=price
            )

        # Record trade
        self.trade_history.append({
            'timestamp': timestamp,
            'action': 'buy',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'cost': cost,
            'cash_after': self.cash,
            'portfolio_value': self.total_value
        })

        # Format quantity display (show decimals for fractional, integer for whole)
        qty_display = f"{quantity:.8f}".rstrip('0').rstrip('.') if quantity < 1 else f"{quantity:.2f}".rstrip('0').rstrip('.')
        logger.info(f"BUY: {qty_display} {symbol} @ ${price:.2f} (cost: ${cost:.2f}, cash: ${self.cash:.2f})")
        return True

    def sell(self, symbol: str, price: float, quantity: float, timestamp: datetime) -> bool:
        """Execute sell order (supports fractional shares for crypto)."""
        if symbol not in self.positions:
            logger.warning(f"Cannot sell {symbol}: no position")
            return False

        pos = self.positions[symbol]

        if pos.quantity < quantity:
            logger.warning(f"Cannot sell {quantity} {symbol}: only have {pos.quantity}")
            return False

        # Calculate proceeds and P&L
        proceeds = price * quantity
        pnl = (price - pos.entry_price) * quantity

        # Add to cash
        self.cash += proceeds

        # Update or close position
        if pos.quantity == quantity:
            # Close position
            del self.positions[symbol]
        else:
            # Reduce position
            pos.quantity -= quantity
            pos.current_price = price

        # Record trade
        self.trade_history.append({
            'timestamp': timestamp,
            'action': 'sell',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'proceeds': proceeds,
            'pnl': pnl,
            'cash_after': self.cash,
            'portfolio_value': self.total_value
        })

        # Format quantity display (show decimals for fractional, integer for whole)
        qty_display = f"{quantity:.8f}".rstrip('0').rstrip('.') if quantity < 1 else f"{quantity:.2f}".rstrip('0').rstrip('.')
        logger.info(f"SELL: {qty_display} {symbol} @ ${price:.2f} (P&L: ${pnl:.2f}, cash: ${self.cash:.2f})")
        return True

    def update_prices(self, prices: Dict[str, float], timestamp: datetime):
        """Update current prices for all positions."""
        for symbol, pos in self.positions.items():
            if symbol in prices:
                pos.current_price = prices[symbol]

        # Record equity curve point
        self.equity_curve.append((timestamp, self.total_value))

    def get_position_size(self, symbol: str) -> int:
        """Get current position size for symbol."""
        return self.positions.get(symbol, BacktestPosition(symbol, 0, 0, datetime.now())).quantity


class BacktestEngine:
    """Engine for running backtests on historical data."""

    def __init__(self, agent_id: str, start_date: datetime, end_date: datetime):
        """
        Initialize backtesting engine.

        Args:
            agent_id: ID of agent to backtest
            start_date: Backtest start date
            end_date: Backtest end date
        """
        self.agent_id = agent_id
        self.start_date = start_date
        self.end_date = end_date

        # Load agent config
        config = get_config()
        if not config.agent_exists(agent_id):
            raise ValueError(f"Agent {agent_id} not found")

        self.agent_config = config.load_agent_config(agent_id)
        self.symbol = self.agent_config.get('agent', {}).get('asset')
        self.timeframe = self.agent_config.get('strategy', {}).get('timeframe', '15m')

        # Initialize portfolio
        initial_capital = self.agent_config.get('capital', {}).get('allocated', 10000.0)
        self.portfolio = BacktestPortfolio(
            initial_capital=initial_capital,
            cash=initial_capital
        )

        # Technical analyzer
        self.technical_analyzer = get_technical_analyzer()

        # Backtest run ID (set when saved to database)
        self.run_id: Optional[int] = None

        logger.info(
            f"Initialized backtest for {agent_id} ({self.symbol}) "
            f"from {start_date} to {end_date}"
        )

    def load_historical_data(self) -> List[Dict]:
        """Load historical market bars from database."""
        logger.info(f"Loading historical data for {self.symbol} ({self.timeframe})")

        bars = []
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT timestamp, open, high, low, close, volume, vwap
                        FROM market_bars
                        WHERE symbol = %s
                          AND timeframe = %s
                          AND timestamp BETWEEN %s AND %s
                        ORDER BY timestamp ASC
                    """, (self.symbol, self.timeframe, self.start_date, self.end_date))

                    for row in cur.fetchall():
                        bars.append({
                            'timestamp': row[0],
                            'open': float(row[1]),
                            'high': float(row[2]),
                            'low': float(row[3]),
                            'close': float(row[4]),
                            'volume': int(row[5]),
                            'vwap': float(row[6]) if row[6] else None
                        })

        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            raise

        logger.info(f"Loaded {len(bars)} bars")
        return bars

    def load_sentiment_data(self) -> Dict[datetime, Dict]:
        """Load historical sentiment data from database."""
        logger.info(f"Loading sentiment data for {self.symbol}")

        sentiment_by_time = {}
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT timestamp, source, sentiment, score, confidence
                        FROM sentiment_history
                        WHERE symbol = %s
                          AND timestamp BETWEEN %s AND %s
                        ORDER BY timestamp ASC
                    """, (self.symbol, self.start_date, self.end_date))

                    for row in cur.fetchall():
                        timestamp = row[0]
                        if timestamp not in sentiment_by_time:
                            sentiment_by_time[timestamp] = {}

                        sentiment_by_time[timestamp][row[1]] = {
                            'sentiment': row[2],
                            'score': float(row[3]),
                            'confidence': float(row[4])
                        }

        except Exception as e:
            logger.error(f"Error loading sentiment data: {e}")

        logger.info(f"Loaded sentiment for {len(sentiment_by_time)} timestamps")
        return sentiment_by_time

    def calculate_position_size(self, price: float) -> float:
        """Calculate position size based on risk management rules.

        Supports fractional shares for crypto assets (e.g., 0.05 BTC).
        """
        max_position_config = self.agent_config.get('risk', {}).get('max_position_size', 0.05)

        # Check if config is percentage (<=1) or absolute dollars (>1)
        if max_position_config <= 1:
            max_position_value = self.portfolio.total_value * max_position_config
        else:
            max_position_value = max_position_config

        quantity = max_position_value / price

        # For crypto (detected by '/' in symbol like 'BTC/USD'), allow fractional shares
        # For stocks, round to integers
        is_crypto = '/' in self.symbol

        if is_crypto:
            # Round to 8 decimal places for crypto (standard precision)
            return round(quantity, 8)
        else:
            # Stocks: use integer shares, minimum 1
            return max(1.0, float(int(quantity)))

    def should_trade(self, signal: TechnicalAnalysis, current_position: float) -> Tuple[str, float]:
        """
        Determine if a trade should be made based on signal and current position.

        Returns:
            Tuple of (action, quantity) where action is 'buy', 'sell', or 'hold'
            Quantity is float to support fractional shares for crypto.
        """
        # Get min confidence from agent config
        min_confidence = self.agent_config.get('risk', {}).get('min_confidence', 0.6)

        # Only trade on high confidence signals
        if signal.overall_confidence < min_confidence:
            return 'hold', 0

        if signal.overall_signal == SignalType.BULLISH and current_position == 0:
            # Open new position
            return 'buy', 1

        elif signal.overall_signal == SignalType.BEARISH and current_position > 0:
            # Close position
            return 'sell', current_position

        return 'hold', 0

    def run(self) -> Dict[str, Any]:
        """
        Run the backtest.

        Returns:
            Dict with backtest results and metrics
        """
        logger.info(f"Starting backtest for {self.agent_id}")

        # Load data
        bars = self.load_historical_data()
        if len(bars) < 50:
            raise ValueError(f"Insufficient data: only {len(bars)} bars")

        sentiment_data = self.load_sentiment_data()

        # Run backtest
        for i, bar in enumerate(bars):
            timestamp = bar['timestamp']
            price = bar['close']

            # Update portfolio prices
            self.portfolio.update_prices({self.symbol: price}, timestamp)

            # Need at least 50 bars for technical analysis
            if i < 50:
                continue

            # Build market context with calculated indicators
            recent_bars = bars[max(0, i-100):i+1]

            # Calculate technical indicators from bars
            market_context = {
                'symbol': self.symbol,
                'current_price': price,
                'timestamp': timestamp,
                'bars': recent_bars,
                'technical_indicators': self._calculate_indicators(recent_bars),
                'trend_analysis': self._analyze_trend(recent_bars),
                'levels': self._find_support_resistance(recent_bars),
                'volume_analysis': self._analyze_volume(recent_bars),
                'price_action': self._analyze_price_action(recent_bars)
            }

            # Get sentiment if available
            if timestamp in sentiment_data:
                market_context['sentiment'] = sentiment_data[timestamp]

            # Run technical analysis
            try:
                signal = self.technical_analyzer.analyze(market_context)
            except Exception as e:
                logger.warning(f"Technical analysis failed at {timestamp}: {e}")
                continue

            # Determine trade action
            current_position = self.portfolio.get_position_size(self.symbol)
            action, quantity = self.should_trade(signal, current_position)

            # Execute trade
            if action == 'buy':
                quantity = self.calculate_position_size(price)
                self.portfolio.buy(self.symbol, price, quantity, timestamp)

            elif action == 'sell':
                self.portfolio.sell(self.symbol, price, quantity, timestamp)

        # Calculate metrics
        metrics = self.calculate_metrics()

        logger.info(f"Backtest complete: {metrics['total_trades']} trades, {metrics['total_return_pct']:.2f}% return")

        return {
            'agent_id': self.agent_id,
            'symbol': self.symbol,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'metrics': metrics,
            'trades': self.portfolio.trade_history,
            'equity_curve': self.portfolio.equity_curve
        }

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics."""
        trades = self.portfolio.trade_history
        sells = [t for t in trades if t['action'] == 'sell']

        total_trades = len(sells)
        winning_trades = len([t for t in sells if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in sells if t.get('pnl', 0) < 0])

        total_pnl = sum(t.get('pnl', 0) for t in sells)
        avg_trade_pnl = total_pnl / total_trades if total_trades > 0 else 0

        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # Calculate max drawdown
        max_drawdown = self.calculate_max_drawdown()

        # Calculate Sharpe ratio (simplified)
        sharpe_ratio = self.calculate_sharpe_ratio()

        return {
            'initial_capital': self.portfolio.initial_capital,
            'final_capital': self.portfolio.total_value,
            'total_return_pct': self.portfolio.total_return_pct,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_trade_pnl': avg_trade_pnl,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio
        }

    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve."""
        if not self.portfolio.equity_curve:
            return 0.0

        peak = self.portfolio.equity_curve[0][1]
        max_dd = 0.0

        for _, value in self.portfolio.equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)

        return max_dd * 100  # Return as percentage

    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio (simplified daily returns)."""
        if len(self.portfolio.equity_curve) < 2:
            return 0.0

        # Calculate daily returns
        returns = []
        for i in range(1, len(self.portfolio.equity_curve)):
            prev_value = self.portfolio.equity_curve[i-1][1]
            curr_value = self.portfolio.equity_curve[i][1]
            if prev_value > 0:
                returns.append((curr_value - prev_value) / prev_value)

        if not returns:
            return 0.0

        # Calculate mean and std
        import numpy as np
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        # Annualized Sharpe ratio
        sharpe = (mean_return - risk_free_rate/252) / std_return * np.sqrt(252)
        return float(sharpe)

    def save_to_database(self, metrics: Dict, trades: List[Dict]) -> int:
        """Save backtest results to database."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Insert backtest run
                    cur.execute("""
                        INSERT INTO backtest_runs (
                            agent_id, start_date, end_date,
                            initial_capital, final_capital, total_return_pct,
                            total_trades, winning_trades, losing_trades,
                            max_drawdown, sharpe_ratio, win_rate, avg_trade_pnl,
                            config, status
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                    """, (
                        self.agent_id, self.start_date, self.end_date,
                        metrics['initial_capital'], metrics['final_capital'],
                        metrics['total_return_pct'], metrics['total_trades'],
                        metrics['winning_trades'], metrics['losing_trades'],
                        metrics['max_drawdown'], metrics['sharpe_ratio'],
                        metrics['win_rate'], metrics['avg_trade_pnl'],
                        json.dumps(self.agent_config), 'completed'
                    ))

                    run_id = cur.fetchone()[0]

                    # Insert trades
                    for trade in trades:
                        if trade['action'] in ['buy', 'sell']:
                            cur.execute("""
                                INSERT INTO backtest_trades (
                                    run_id, timestamp, action, symbol,
                                    quantity, price, pnl,
                                    portfolio_value, cash_balance
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                run_id, trade['timestamp'], trade['action'],
                                trade['symbol'], trade['quantity'], trade['price'],
                                trade.get('pnl'), trade.get('portfolio_value'),
                                trade.get('cash_after')
                            ))

            logger.info(f"Saved backtest run #{run_id} to database")
            self.run_id = run_id
            return run_id

        except Exception as e:
            logger.error(f"Error saving backtest to database: {e}")
            raise

    def _calculate_indicators(self, bars: List[Dict]) -> Dict:
        """Calculate technical indicators from price bars."""
        if not bars or len(bars) < 20:
            return {}

        # Convert to float to avoid Decimal type issues from database
        closes = [float(bar['close']) for bar in bars]
        indicators = {}

        # Simple Moving Averages
        if len(closes) >= 20:
            indicators['sma_20'] = sum(closes[-20:]) / 20

        if len(closes) >= 50:
            indicators['sma_50'] = sum(closes[-50:]) / 50

        # RSI (simplified)
        if len(closes) >= 14:
            indicators['rsi_14'] = self._calculate_rsi(closes, 14)

        # Current vs SMA (momentum)
        if 'sma_20' in indicators:
            current = closes[-1]
            indicators['price_vs_sma20'] = ((current - indicators['sma_20']) / indicators['sma_20']) * 100

        return indicators

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return 50.0  # Neutral

        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    def _analyze_trend(self, bars: List[Dict]) -> Dict:
        """Analyze price trend using longer lookback period."""
        if len(bars) < 20:
            return {'trend': 'unknown', 'strength': 0}

        # Convert to float to avoid Decimal type issues
        closes = [float(bar['close']) for bar in bars]

        # Use longer lookback for trend - at least 100 bars or all available
        # On 5m timeframe: 100 bars = ~8 hours of trading
        # On 15m timeframe: 100 bars = ~25 hours (2 days)
        lookback = min(len(closes), 100)
        recent_closes = closes[-lookback:]

        # Compare first quarter vs last quarter to detect trend
        quarter_size = lookback // 4
        first_quarter_avg = sum(recent_closes[:quarter_size]) / quarter_size
        last_quarter_avg = sum(recent_closes[-quarter_size:]) / quarter_size

        change_pct = ((last_quarter_avg - first_quarter_avg) / first_quarter_avg) * 100

        # More lenient thresholds for trend detection
        if change_pct > 1:  # Was 2%, now 1%
            trend = 'bullish'
            strength = min(abs(change_pct) / 5, 1.0)
        elif change_pct < -1:  # Was -2%, now -1%
            trend = 'bearish'
            strength = min(abs(change_pct) / 5, 1.0)
        else:
            trend = 'sideways'
            strength = 0.5

        return {
            'trend': trend,
            'strength': round(strength, 2),
            'change_pct': round(change_pct, 2)
        }

    def _find_support_resistance(self, bars: List[Dict]) -> Dict:
        """Find support and resistance levels."""
        if len(bars) < 20:
            return {}

        # Convert to float to avoid Decimal type issues
        highs = [float(bar['high']) for bar in bars[-20:]]
        lows = [float(bar['low']) for bar in bars[-20:]]

        resistance = max(highs)
        support = min(lows)
        current = float(bars[-1]['close'])

        return {
            'support': round(support, 2),
            'resistance': round(resistance, 2),
            'distance_to_support_pct': round(((current - support) / support) * 100, 2),
            'distance_to_resistance_pct': round(((resistance - current) / current) * 100, 2)
        }

    def _analyze_volume(self, bars: List[Dict]) -> Dict:
        """Analyze volume patterns."""
        if len(bars) < 20:
            return {'volume_trend': 'unknown'}

        # Convert to float to avoid Decimal type issues
        volumes = [float(bar.get('volume', 0)) for bar in bars]
        avg_volume = sum(volumes[-20:]) / 20
        recent_volume = volumes[-1]

        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1

        if volume_ratio > 1.5:
            volume_trend = 'high'
        elif volume_ratio < 0.5:
            volume_trend = 'low'
        else:
            volume_trend = 'normal'

        return {
            'volume_trend': volume_trend,
            'volume_ratio': round(volume_ratio, 2),
            'avg_volume': round(avg_volume, 2),
            'current_volume': round(recent_volume, 2)
        }

    def _analyze_price_action(self, bars: List[Dict]) -> Dict:
        """Analyze recent price action."""
        if len(bars) < 5:
            return {}

        recent_bars = bars[-5:]

        # Check for higher highs / lower lows (convert to float)
        highs = [float(bar['high']) for bar in recent_bars]
        lows = [float(bar['low']) for bar in recent_bars]

        higher_highs = all(highs[i] >= highs[i-1] for i in range(1, len(highs)))
        higher_lows = all(lows[i] >= lows[i-1] for i in range(1, len(lows)))
        lower_highs = all(highs[i] <= highs[i-1] for i in range(1, len(highs)))
        lower_lows = all(lows[i] <= lows[i-1] for i in range(1, len(lows)))

        if higher_highs and higher_lows:
            pattern = 'strong_uptrend'
        elif lower_highs and lower_lows:
            pattern = 'strong_downtrend'
        elif higher_lows and not lower_highs:
            pattern = 'bullish_consolidation'
        elif lower_highs and not higher_lows:
            pattern = 'bearish_consolidation'
        else:
            pattern = 'choppy'

        return {'pattern': pattern, 'bars_analyzed': len(recent_bars)}


def run_backtest(
    agent_id: str,
    start_date: datetime,
    end_date: datetime,
    save: bool = True
) -> Dict[str, Any]:
    """
    Run a backtest for an agent.

    Args:
        agent_id: Agent ID to backtest
        start_date: Backtest start date
        end_date: Backtest end date
        save: Whether to save results to database

    Returns:
        Dict with backtest results
    """
    engine = BacktestEngine(agent_id, start_date, end_date)
    results = engine.run()

    if save:
        run_id = engine.save_to_database(results['metrics'], results['trades'])
        results['run_id'] = run_id

    return results
