"""Multi-source sentiment aggregator for trading decisions."""

from typing import Dict, Any, Optional
from ztrade.sentiment.news import get_news_analyzer
from ztrade.sentiment.reddit import get_reddit_analyzer
from ztrade.sentiment.sec import get_sec_analyzer
from ztrade.core.logger import get_logger

logger = get_logger(__name__)


class SentimentAggregator:
    """Aggregates sentiment from multiple sources with weighted scoring."""

    # Default weights for each source (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        "news": 0.40,      # Professional financial news (most reliable)
        "reddit": 0.25,    # Retail sentiment (early signals)
        "sec": 0.25,       # Official filings (fundamental events)
        "stocktwits": 0.10  # Reserved for future use
    }

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        enable_news: bool = True,
        enable_reddit: bool = True,
        enable_sec: bool = True
    ):
        """
        Initialize sentiment aggregator.

        Args:
            weights: Custom weights for each source (default: DEFAULT_WEIGHTS)
            enable_news: Enable news sentiment analysis
            enable_reddit: Enable Reddit sentiment analysis
            enable_sec: Enable SEC filings analysis
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.enable_news = enable_news
        self.enable_reddit = enable_reddit
        self.enable_sec = enable_sec

        # Initialize analyzers
        self.news_analyzer = get_news_analyzer() if enable_news else None
        self.reddit_analyzer = get_reddit_analyzer() if enable_reddit else None
        self.sec_analyzer = get_sec_analyzer() if enable_sec else None

        logger.info(
            f"Sentiment aggregator initialized with weights: "
            f"news={self.weights['news']:.0%}, "
            f"reddit={self.weights['reddit']:.0%}, "
            f"sec={self.weights['sec']:.0%}"
        )

    def get_aggregated_sentiment(
        self,
        symbol: str,
        news_lookback_hours: int = 24,
        reddit_lookback_hours: int = 24,
        sec_lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get aggregated sentiment from all enabled sources.

        Args:
            symbol: Stock symbol (e.g., 'TSLA', 'IWM') or crypto (e.g., 'BTC/USD')
            news_lookback_hours: Hours to look back for news
            reddit_lookback_hours: Hours to look back for Reddit
            sec_lookback_days: Days to look back for SEC filings

        Returns:
            Dict containing:
            - overall_sentiment: 'positive', 'negative', or 'neutral'
            - sentiment_score: Aggregated weighted score (-1 to 1)
            - confidence: Overall confidence (0 to 1)
            - source_breakdown: Individual sentiment from each source
            - sources_used: List of sources that contributed data
            - agreement_level: How much sources agree (0 to 1)
        """
        logger.info(f"Aggregating sentiment for {symbol} from all sources...")

        # Collect sentiment from each source
        sources = {}
        weighted_scores = []
        confidences = []
        sources_used = []

        # 1. News Sentiment (Alpaca News API)
        if self.enable_news and self.news_analyzer:
            try:
                news_sentiment = self.news_analyzer.get_news_sentiment(
                    symbol,
                    lookback_hours=news_lookback_hours,
                    max_articles=25
                )

                if "error" not in news_sentiment and news_sentiment.get("article_count", 0) > 0:
                    sources["news"] = news_sentiment
                    weighted_scores.append(
                        news_sentiment["sentiment_score"] * self.weights["news"]
                    )
                    confidences.append(news_sentiment["confidence"] * self.weights["news"])
                    sources_used.append("news")
                    logger.info(f"News sentiment: {news_sentiment['overall_sentiment']} ({news_sentiment['sentiment_score']:.2f})")
                else:
                    logger.info("News sentiment not available or no articles found")
            except Exception as e:
                logger.warning(f"Could not fetch news sentiment: {e}")

        # 2. Reddit Sentiment (PRAW)
        if self.enable_reddit and self.reddit_analyzer:
            try:
                reddit_sentiment = self.reddit_analyzer.get_reddit_sentiment(
                    symbol,
                    lookback_hours=reddit_lookback_hours,
                    max_posts=50
                )

                if "error" not in reddit_sentiment and reddit_sentiment.get("mention_count", 0) > 0:
                    sources["reddit"] = reddit_sentiment
                    weighted_scores.append(
                        reddit_sentiment["sentiment_score"] * self.weights["reddit"]
                    )
                    confidences.append(reddit_sentiment["confidence"] * self.weights["reddit"])
                    sources_used.append("reddit")
                    logger.info(
                        f"Reddit sentiment: {reddit_sentiment['overall_sentiment']} "
                        f"({reddit_sentiment['sentiment_score']:.2f}, "
                        f"{reddit_sentiment['mention_count']} mentions)"
                    )
                else:
                    logger.info("Reddit sentiment not available or no mentions found")
            except Exception as e:
                logger.warning(f"Could not fetch Reddit sentiment: {e}")

        # 3. SEC Filings Sentiment
        if self.enable_sec and self.sec_analyzer:
            try:
                sec_sentiment = self.sec_analyzer.get_sec_sentiment(
                    symbol,
                    lookback_days=sec_lookback_days,
                    max_filings=10
                )

                if "error" not in sec_sentiment and sec_sentiment.get("filing_count", 0) > 0:
                    sources["sec"] = sec_sentiment
                    weighted_scores.append(
                        sec_sentiment["sentiment_score"] * self.weights["sec"]
                    )
                    confidences.append(sec_sentiment["confidence"] * self.weights["sec"])
                    sources_used.append("sec")
                    logger.info(
                        f"SEC sentiment: {sec_sentiment['overall_sentiment']} "
                        f"({sec_sentiment['sentiment_score']:.2f}, "
                        f"{sec_sentiment['filing_count']} filings)"
                    )
                else:
                    logger.info("SEC sentiment not available or no filings found")
            except Exception as e:
                logger.warning(f"Could not fetch SEC sentiment: {e}")

        # If no sources available, return neutral
        if not sources_used:
            logger.warning(f"No sentiment sources available for {symbol}")
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "source_breakdown": {},
                "sources_used": [],
                "agreement_level": 0.0,
                "error": "No sentiment sources available"
            }

        # Calculate aggregated score
        # Normalize by the total weight of sources that contributed
        total_weight_used = sum(self.weights[src] for src in sources_used)

        if total_weight_used > 0:
            aggregated_score = sum(weighted_scores) / total_weight_used
            aggregated_confidence = sum(confidences) / total_weight_used
        else:
            aggregated_score = 0.0
            aggregated_confidence = 0.0

        # Determine overall sentiment
        if aggregated_score >= 0.05:
            overall_sentiment = "positive"
        elif aggregated_score <= -0.05:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"

        # Calculate agreement level (how much sources agree)
        # Compare each source's sentiment classification
        sentiments_list = [
            sources[src]["overall_sentiment"] for src in sources_used
        ]

        if len(sentiments_list) > 0:
            # Count how many agree with the majority
            from collections import Counter
            sentiment_counts = Counter(sentiments_list)
            most_common_sentiment, count = sentiment_counts.most_common(1)[0]
            agreement_level = count / len(sentiments_list)
        else:
            agreement_level = 0.0

        result = {
            "overall_sentiment": overall_sentiment,
            "sentiment_score": round(aggregated_score, 3),
            "confidence": round(aggregated_confidence, 2),
            "source_breakdown": sources,
            "sources_used": sources_used,
            "agreement_level": round(agreement_level, 2),
            "weights_applied": {src: self.weights[src] for src in sources_used}
        }

        logger.info(
            f"Aggregated sentiment for {symbol}: {overall_sentiment} "
            f"(score: {aggregated_score:.3f}, confidence: {aggregated_confidence:.2f}, "
            f"sources: {len(sources_used)}, agreement: {agreement_level:.0%})"
        )

        return result


def get_sentiment_aggregator(
    weights: Optional[Dict[str, float]] = None,
    enable_news: bool = True,
    enable_reddit: bool = True,
    enable_sec: bool = True
) -> SentimentAggregator:
    """
    Factory function to get sentiment aggregator instance.

    Args:
        weights: Custom weights for each source
        enable_news: Enable news sentiment
        enable_reddit: Enable Reddit sentiment
        enable_sec: Enable SEC sentiment

    Returns:
        SentimentAggregator instance
    """
    return SentimentAggregator(
        weights=weights,
        enable_news=enable_news,
        enable_reddit=enable_reddit,
        enable_sec=enable_sec
    )
