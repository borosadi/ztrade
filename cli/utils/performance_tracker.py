"""Performance tracking for sentiment analysis accuracy and predictiveness."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
from collections import defaultdict
from cli.utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceTracker:
    """Tracks sentiment prediction accuracy and source effectiveness."""

    def __init__(self, logs_dir: str = "oversight/sentiment_performance"):
        """
        Initialize performance tracker.

        Args:
            logs_dir: Directory to store performance logs
        """
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.trades_file = self.logs_dir / "trades.jsonl"
        self.summary_file = self.logs_dir / "summary.json"

    def log_trade_with_sentiment(
        self,
        agent_id: str,
        symbol: str,
        action: str,  # 'buy', 'sell', 'hold'
        sentiment_data: Dict[str, Any],
        entry_price: float,
        quantity: int = 0,
        confidence: float = 0.0,
        rationale: str = ""
    ) -> None:
        """
        Log a trade with associated sentiment data.

        Args:
            agent_id: ID of trading agent
            symbol: Stock symbol
            action: Trade action (buy/sell/hold)
            sentiment_data: Multi-source sentiment dict from aggregator
            entry_price: Entry price at time of trade
            quantity: Number of shares
            confidence: Trade confidence (0-1)
            rationale: Trading rationale
        """
        try:
            trade_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": agent_id,
                "symbol": symbol,
                "action": action,
                "entry_price": entry_price,
                "quantity": quantity,
                "confidence": confidence,
                "rationale": rationale,
                "sentiment": {
                    "overall_sentiment": sentiment_data.get("overall_sentiment"),
                    "aggregated_score": sentiment_data.get("sentiment_score", 0),
                    "sources_used": sentiment_data.get("sources_used", []),
                    "agreement_level": sentiment_data.get("agreement_level", 0),
                    "source_breakdown": self._extract_source_scores(sentiment_data),
                },
                "outcome": None,  # Will be filled in when trade closes
            }

            # Append to JSONL file
            with open(self.trades_file, "a") as f:
                f.write(json.dumps(trade_record) + "\n")

            logger.info(
                f"Logged trade: {agent_id} {action} {quantity} {symbol} "
                f"@ ${entry_price:.2f} (sentiment: {sentiment_data.get('overall_sentiment')})"
            )

        except Exception as e:
            logger.error(f"Error logging trade with sentiment: {e}")

    def log_trade_outcome(
        self,
        trade_id: int,
        exit_price: Optional[float] = None,
        exit_quantity: Optional[int] = None,
        pnl: Optional[float] = None,
        pnl_pct: Optional[float] = None,
        exit_reason: str = ""
    ) -> None:
        """
        Update a trade record with outcome data.

        Args:
            trade_id: Index of trade in JSONL file
            exit_price: Exit price
            exit_quantity: Shares exited
            pnl: Profit/loss in dollars
            pnl_pct: Profit/loss percentage
            exit_reason: Why trade was closed
        """
        try:
            # Read all trades
            trades = []
            with open(self.trades_file, "r") as f:
                for line in f:
                    if line.strip():
                        trades.append(json.loads(line))

            # Update specific trade
            if 0 <= trade_id < len(trades):
                trades[trade_id]["outcome"] = {
                    "exit_timestamp": datetime.utcnow().isoformat(),
                    "exit_price": exit_price,
                    "exit_quantity": exit_quantity or trades[trade_id]["quantity"],
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "exit_reason": exit_reason,
                }

                # Rewrite file
                with open(self.trades_file, "w") as f:
                    for trade in trades:
                        f.write(json.dumps(trade) + "\n")

                logger.info(
                    f"Updated trade {trade_id} outcome: "
                    f"${pnl:.2f} ({pnl_pct:+.2f}%)"
                )

        except Exception as e:
            logger.error(f"Error updating trade outcome: {e}")

    def get_sentiment_accuracy(
        self,
        lookback_days: int = 30,
        min_trades: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze sentiment prediction accuracy.

        Args:
            lookback_days: How many days back to analyze
            min_trades: Minimum trades per sentiment for meaningful analysis

        Returns:
            Dict with accuracy metrics by sentiment source
        """
        try:
            trades = self._load_trades(lookback_days)

            if not trades:
                return {
                    "error": "No trades found",
                    "lookback_days": lookback_days
                }

            # Collect trades by sentiment
            bullish_trades = []  # sentiment >= 0.05
            bearish_trades = []  # sentiment <= -0.05
            neutral_trades = []  # -0.05 < sentiment < 0.05

            for trade in trades:
                if not trade.get("outcome"):
                    continue  # Skip incomplete trades

                score = trade["sentiment"]["aggregated_score"]
                pnl_pct = trade["outcome"].get("pnl_pct", 0)

                if score >= 0.05:
                    bullish_trades.append(pnl_pct)
                elif score <= -0.05:
                    bearish_trades.append(pnl_pct)
                else:
                    neutral_trades.append(pnl_pct)

            # Calculate accuracy metrics
            results = {
                "lookback_days": lookback_days,
                "total_trades_analyzed": len([t for t in trades if t.get("outcome")]),
                "bullish_sentiment": self._calculate_group_metrics(bullish_trades, "bullish"),
                "bearish_sentiment": self._calculate_group_metrics(bearish_trades, "bearish"),
                "neutral_sentiment": self._calculate_group_metrics(neutral_trades, "neutral"),
            }

            # Overall accuracy
            all_wins = sum(1 for t in trades if t.get("outcome", {}).get("pnl_pct", 0) > 0)
            results["overall_win_rate"] = all_wins / len([t for t in trades if t.get("outcome")]) if trades else 0

            logger.info(
                f"Sentiment accuracy: {results['overall_win_rate']:.0%} win rate "
                f"({len([t for t in trades if t.get('outcome')])} trades analyzed)"
            )

            return results

        except Exception as e:
            logger.error(f"Error calculating sentiment accuracy: {e}")
            return {"error": str(e)}

    def get_source_effectiveness(
        self,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Measure effectiveness of each sentiment source.

        Args:
            lookback_days: How many days back to analyze

        Returns:
            Dict with effectiveness metrics per source
        """
        try:
            trades = self._load_trades(lookback_days)

            if not trades:
                return {
                    "error": "No trades found",
                    "lookback_days": lookback_days
                }

            # Collect trades by source
            source_trades = defaultdict(list)

            for trade in trades:
                if not trade.get("outcome"):
                    continue

                sources = trade["sentiment"].get("sources_used", [])
                pnl_pct = trade["outcome"].get("pnl_pct", 0)

                for source in sources:
                    source_trades[source].append(pnl_pct)

            # Calculate metrics per source
            results = {
                "lookback_days": lookback_days,
                "total_trades_analyzed": len([t for t in trades if t.get("outcome")]),
                "source_metrics": {}
            }

            for source, returns in source_trades.items():
                metrics = self._calculate_group_metrics(returns, source)
                results["source_metrics"][source] = metrics

            # Rank sources by Sharpe ratio (return/risk)
            source_rankings = sorted(
                results["source_metrics"].items(),
                key=lambda x: x[1].get("sharpe_ratio", 0),
                reverse=True
            )
            results["source_ranking"] = [source for source, _ in source_rankings]

            logger.info(
                f"Source effectiveness (top): {results['source_ranking']}"
            )

            return results

        except Exception as e:
            logger.error(f"Error calculating source effectiveness: {e}")
            return {"error": str(e)}

    def get_agreement_impact(
        self,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Measure how agreement level impacts prediction accuracy.

        Args:
            lookback_days: How many days back to analyze

        Returns:
            Dict with metrics on agreement level vs accuracy
        """
        try:
            trades = self._load_trades(lookback_days)

            if not trades:
                return {
                    "error": "No trades found",
                    "lookback_days": lookback_days
                }

            # Bucket trades by agreement level
            high_agreement = []  # >= 80%
            medium_agreement = []  # 50-80%
            low_agreement = []  # < 50%

            for trade in trades:
                if not trade.get("outcome"):
                    continue

                agreement = trade["sentiment"].get("agreement_level", 0)
                pnl_pct = trade["outcome"].get("pnl_pct", 0)

                if agreement >= 0.8:
                    high_agreement.append(pnl_pct)
                elif agreement >= 0.5:
                    medium_agreement.append(pnl_pct)
                else:
                    low_agreement.append(pnl_pct)

            results = {
                "lookback_days": lookback_days,
                "total_trades_analyzed": len([t for t in trades if t.get("outcome")]),
                "high_agreement": self._calculate_group_metrics(high_agreement, "high (>=80%)"),
                "medium_agreement": self._calculate_group_metrics(medium_agreement, "medium (50-80%)"),
                "low_agreement": self._calculate_group_metrics(low_agreement, "low (<50%)"),
            }

            logger.info(
                f"Agreement impact: High={results['high_agreement'].get('win_rate', 0):.0%}, "
                f"Med={results['medium_agreement'].get('win_rate', 0):.0%}, "
                f"Low={results['low_agreement'].get('win_rate', 0):.0%}"
            )

            return results

        except Exception as e:
            logger.error(f"Error calculating agreement impact: {e}")
            return {"error": str(e)}

    def generate_report(self, lookback_days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.

        Args:
            lookback_days: Analysis period

        Returns:
            Complete performance report
        """
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "lookback_days": lookback_days,
            "sentiment_accuracy": self.get_sentiment_accuracy(lookback_days),
            "source_effectiveness": self.get_source_effectiveness(lookback_days),
            "agreement_impact": self.get_agreement_impact(lookback_days),
        }

        # Save report
        with open(self.summary_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Performance report saved to {self.summary_file}")
        return report

    # ==================== Private Methods ====================

    def _load_trades(self, lookback_days: int) -> List[Dict[str, Any]]:
        """Load trades from the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)

        trades = []
        if not self.trades_file.exists():
            return trades

        with open(self.trades_file, "r") as f:
            for line in f:
                if line.strip():
                    trade = json.loads(line)
                    trade_time = datetime.fromisoformat(trade["timestamp"])
                    if trade_time > cutoff:
                        trades.append(trade)

        return trades

    def _extract_source_scores(self, sentiment_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract individual source sentiment scores."""
        breakdown = sentiment_data.get("source_breakdown", {})
        return {
            source: data.get("sentiment_score", 0)
            for source, data in breakdown.items()
        }

    def _calculate_group_metrics(
        self,
        returns: List[float],
        group_name: str = ""
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics for a group of trades.

        Args:
            returns: List of P&L percentages
            group_name: Name of group for logging

        Returns:
            Dict with mean, stddev, win_rate, sharpe_ratio, etc.
        """
        if not returns:
            return {
                "count": 0,
                "mean_return": 0,
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "sharpe_ratio": 0,
                "max_loss": 0
            }

        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r < 0]

        mean_return = sum(returns) / len(returns)
        std_dev = (sum((r - mean_return) ** 2 for r in returns) / len(returns)) ** 0.5

        # Sharpe ratio (return per unit of risk)
        sharpe = mean_return / std_dev if std_dev > 0 else 0

        metrics = {
            "count": len(returns),
            "mean_return": round(mean_return, 2),
            "std_dev": round(std_dev, 2),
            "win_rate": round(len(wins) / len(returns), 2) if returns else 0,
            "avg_win": round(sum(wins) / len(wins), 2) if wins else 0,
            "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0,
            "sharpe_ratio": round(sharpe, 2),
            "max_loss": round(min(returns), 2) if returns else 0,
            "max_win": round(max(returns), 2) if returns else 0,
        }

        return metrics


def get_performance_tracker(
    logs_dir: str = "oversight/sentiment_performance"
) -> PerformanceTracker:
    """Factory function to get performance tracker instance."""
    return PerformanceTracker(logs_dir)
