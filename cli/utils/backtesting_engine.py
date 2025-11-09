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
    """Represents a simulated position in backtesting."""
    symbol: str
    quantity: int
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

    def can_buy(self, price: float, quantity: int) -> bool:
        """Check if portfolio has enough cash for purchase."""
        cost = price * quantity
        return self.cash >= cost

    def buy(self, symbol: str, price: float, quantity: int, timestamp: datetime) -> bool:
        """Execute buy order."""
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

        logger.info(f"BUY: {quantity} {symbol} @ ${price:.2f} (cost: ${cost:.2f}, cash: ${self.cash:.2f})")
        return True

    def sell(self, symbol: str, price: float, quantity: int, timestamp: datetime) -> bool:
        """Execute sell order."""
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

        logger.info(f"SELL: {quantity} {symbol} @ ${price:.2f} (P&L: ${pnl:.2f}, cash: ${self.cash:.2f})")
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

    def calculate_position_size(self, price: float) -> int:
        """Calculate position size based on risk management rules."""
        max_position_pct = self.agent_config.get('risk', {}).get('max_position_size', 0.05)
        max_position_value = self.portfolio.total_value * max_position_pct

        quantity = int(max_position_value / price)
        return max(1, quantity)  # At least 1 share

    def should_trade(self, signal: TechnicalAnalysis, current_position: int) -> Tuple[str, int]:
        """
        Determine if a trade should be made based on signal and current position.

        Returns:
            Tuple of (action, quantity) where action is 'buy', 'sell', or 'hold'
        """
        # Only trade on high confidence signals
        if signal.overall_confidence < 0.6:
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

            # Build market context
            recent_bars = bars[max(0, i-100):i+1]
            market_context = {
                'symbol': self.symbol,
                'current_price': price,
                'bars': recent_bars,
                'timestamp': timestamp
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
