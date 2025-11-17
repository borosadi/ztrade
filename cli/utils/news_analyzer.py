"""Financial news fetching and sentiment analysis for trading decisions."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from cli.utils.logger import get_logger

logger = get_logger(__name__)


class NewsAnalyzer:
    """Analyzes financial news sentiment for trading symbols."""

    def __init__(self):
        """Initialize the news analyzer with Alpaca API and sentiment analyzer."""
        self.sentiment_analyzer = None
        self._init_sentiment_analyzer()

    def _init_sentiment_analyzer(self):
        """Initialize sentiment analysis using FinBERT."""
        try:
            from cli.utils.finbert_analyzer import get_finbert_analyzer
            self.sentiment_analyzer = get_finbert_analyzer()
            logger.info("FinBERT sentiment analyzer initialized")
        except ImportError as e:
            logger.warning(f"FinBERT not available ({e}). Install with: pip install transformers torch")
            self.sentiment_analyzer = None
        except Exception as e:
            logger.error(f"Failed to initialize FinBERT: {e}")
            self.sentiment_analyzer = None

    def get_news_sentiment(
        self,
        symbol: str,
        lookback_hours: int = 24,
        max_articles: int = 25
    ) -> Dict[str, Any]:
        """
        Fetch recent news and analyze sentiment for a symbol.

        Args:
            symbol: Stock symbol (e.g., 'TSLA', 'IWM') or crypto (e.g., 'BTC/USD')
            lookback_hours: How many hours back to fetch news
            max_articles: Maximum number of articles to analyze

        Returns:
            Dict containing:
            - overall_sentiment: 'positive', 'negative', or 'neutral'
            - sentiment_score: Aggregate score (-1 to 1)
            - confidence: Confidence in the sentiment (0 to 1)
            - article_count: Number of articles analyzed
            - top_headlines: List of recent headlines
        """
        if not self.sentiment_analyzer:
            return {
                "error": "Sentiment analyzer not available",
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "article_count": 0
            }

        try:
            # Fetch news from Alpaca
            news_articles = self._fetch_alpaca_news(symbol, lookback_hours, max_articles)

            if not news_articles:
                logger.info(f"No news found for {symbol} in the last {lookback_hours} hours")
                return {
                    "overall_sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "confidence": 0.0,
                    "article_count": 0,
                    "top_headlines": []
                }

            # Analyze sentiment for each article
            sentiments = []
            headlines = []

            content_count = 0
            for article in news_articles:
                # Use full content if available, otherwise fallback to headline + summary
                content = article.get("content", "")
                if content:
                    # Limit content to first 5000 chars for performance
                    # FinBERT uses 512 token window, but we chunk longer texts
                    text = content[:5000]
                    content_count += 1
                else:
                    # Fallback to headline + summary if no content
                    text = article.get("headline", "")
                    summary = article.get("summary", "")
                    if summary:
                        text += " " + summary

                if text.strip():  # Check for non-empty text
                    scores = self.sentiment_analyzer.polarity_scores(text)
                    sentiments.append(scores)
                    headlines.append(article.get("headline", ""))

            if content_count > 0:
                logger.info(f"Analyzed full content for {content_count}/{len(news_articles)} articles")

            if not sentiments:
                return {
                    "overall_sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "confidence": 0.0,
                    "article_count": 0,
                    "top_headlines": []
                }

            # Aggregate sentiment scores
            avg_compound = sum(s["compound"] for s in sentiments) / len(sentiments)
            avg_pos = sum(s["pos"] for s in sentiments) / len(sentiments)
            avg_neg = sum(s["neg"] for s in sentiments) / len(sentiments)
            avg_neu = sum(s["neu"] for s in sentiments) / len(sentiments)

            # Determine overall sentiment
            if avg_compound >= 0.05:
                overall = "positive"
            elif avg_compound <= -0.05:
                overall = "negative"
            else:
                overall = "neutral"

            # Calculate confidence based on consistency
            # High confidence if most articles agree
            positive_count = sum(1 for s in sentiments if s["compound"] > 0.05)
            negative_count = sum(1 for s in sentiments if s["compound"] < -0.05)
            neutral_count = len(sentiments) - positive_count - negative_count

            max_agreement = max(positive_count, negative_count, neutral_count)
            confidence = max_agreement / len(sentiments) if len(sentiments) > 0 else 0

            result = {
                "overall_sentiment": overall,
                "sentiment_score": round(avg_compound, 3),
                "confidence": round(confidence, 2),
                "article_count": len(sentiments),
                "top_headlines": headlines[:5],  # Top 5 headlines
                "details": {
                    "positive": round(avg_pos, 2),
                    "negative": round(avg_neg, 2),
                    "neutral": round(avg_neu, 2),
                    "positive_articles": positive_count,
                    "negative_articles": negative_count,
                    "neutral_articles": neutral_count
                }
            }

            logger.info(
                f"News sentiment for {symbol}: {overall} "
                f"(score: {avg_compound:.2f}, confidence: {confidence:.2f}, "
                f"articles: {len(sentiments)})"
            )

            return result

        except Exception as e:
            logger.error(f"Error analyzing news sentiment for {symbol}: {e}")
            return {
                "error": str(e),
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "article_count": 0
            }

    def _fetch_alpaca_news(
        self,
        symbol: str,
        lookback_hours: int,
        max_articles: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch news articles from Alpaca News API.

        Args:
            symbol: Stock symbol
            lookback_hours: Hours to look back
            max_articles: Maximum articles to fetch

        Returns:
            List of news article dicts
        """
        try:
            from alpaca.data.historical import NewsClient
            from alpaca.data.requests import NewsRequest
            import os
            from dotenv import load_dotenv

            load_dotenv()

            # Initialize Alpaca News client
            api_key = os.getenv("ALPACA_API_KEY")
            secret_key = os.getenv("ALPACA_SECRET_KEY")

            if not api_key or not secret_key:
                logger.warning("Alpaca API keys not found. Cannot fetch news.")
                return []

            news_client = NewsClient(api_key, secret_key)

            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=lookback_hours)

            # Create news request
            request = NewsRequest(
                symbols=symbol,  # Single symbol as string, not list
                start=start_time,
                end=end_time,
                limit=max_articles,
                sort="desc",  # Most recent first
                include_content=True,  # Fetch full article content
                exclude_contentless=True  # Only articles with content
            )

            # Fetch news
            news_response = news_client.get_news(request)

            # Convert to list of dicts
            articles = []

            # Handle different response formats
            if hasattr(news_response, '__iter__'):
                for idx, article in enumerate(news_response):
                    # Handle tuple format (symbol, news_item)
                    if isinstance(article, tuple):
                        # The tuple is (symbol_str, dict_with_news)
                        article = article[1] if len(article) > 1 else article[0]

                        # If it's a dict with 'news' key, extract the actual news object
                        if isinstance(article, dict) and 'news' in article:
                            article = article['news']

                    # Handle if article is a list of news items
                    if isinstance(article, list):
                        news_items = article
                    else:
                        news_items = [article]

                    # Process each news item
                    for news_item in news_items:
                        if news_item is None:
                            continue

                        try:
                            # Check if it's a dict or object
                            if isinstance(news_item, dict):
                                article_dict = {
                                    "headline": news_item.get('headline', ''),
                                    "summary": news_item.get('summary', ''),
                                    "content": news_item.get('content', ''),
                                    "author": news_item.get('author', ''),
                                    "created_at": str(news_item.get('created_at', '')),
                                    "url": news_item.get('url', ''),
                                    "source": news_item.get('source', '')
                                }
                            else:
                                # It's an object with attributes
                                article_dict = {
                                    "headline": getattr(news_item, 'headline', ''),
                                    "summary": getattr(news_item, 'summary', ''),
                                    "content": getattr(news_item, 'content', ''),
                                    "author": getattr(news_item, 'author', ''),
                                    "created_at": str(getattr(news_item, 'created_at', '')),
                                    "url": getattr(news_item, 'url', ''),
                                    "source": getattr(news_item, 'source', '')
                                }

                            articles.append(article_dict)
                        except Exception as e:
                            logger.warning(f"Could not parse news item: {e}")
                            continue

            logger.info(f"Fetched {len(articles)} news articles for {symbol}")
            return articles

        except ImportError:
            logger.warning("alpaca-py library not installed. Install with: pip install alpaca-py")
            return []
        except Exception as e:
            logger.error(f"Error fetching news from Alpaca: {e}")
            return []


def get_news_analyzer() -> NewsAnalyzer:
    """Factory function to get news analyzer instance."""
    return NewsAnalyzer()
