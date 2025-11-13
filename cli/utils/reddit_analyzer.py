"""Reddit sentiment analysis for trading symbols."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from cli.utils.logger import get_logger

logger = get_logger(__name__)


class RedditAnalyzer:
    """Analyzes Reddit sentiment for trading symbols."""

    def __init__(self):
        """Initialize the Reddit analyzer with PRAW."""
        self.reddit = None
        self.sentiment_analyzer = None
        self._init_reddit()
        self._init_sentiment_analyzer()

    def _init_reddit(self):
        """Initialize Reddit API connection using PRAW."""
        try:
            import praw

            load_dotenv()

            client_id = os.getenv("REDDIT_CLIENT_ID")
            client_secret = os.getenv("REDDIT_CLIENT_SECRET")
            user_agent = os.getenv("REDDIT_USER_AGENT", "Ztrade:v1.0 (by /u/ztrade_bot)")

            if not client_id or not client_secret:
                logger.warning(
                    "Reddit API credentials not found in .env file. "
                    "Add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to enable Reddit sentiment. "
                    "Get credentials at: https://www.reddit.com/prefs/apps"
                )
                self.reddit = None
                return

            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )

            # Test connection
            self.reddit.user.me()
            logger.info("Reddit API connected successfully")

        except ImportError:
            logger.warning("praw not installed. Install with: pip install praw")
            self.reddit = None
        except Exception as e:
            logger.warning(f"Could not connect to Reddit API: {e}")
            self.reddit = None

    def _init_sentiment_analyzer(self):
        """Initialize sentiment analysis using FinBERT."""
        try:
            from cli.utils.finbert_analyzer import get_finbert_analyzer
            self.sentiment_analyzer = get_finbert_analyzer()
            logger.info("FinBERT sentiment analyzer initialized for Reddit")
        except ImportError as e:
            logger.warning(f"FinBERT not available ({e}). Install with: pip install transformers torch")
            self.sentiment_analyzer = None
        except Exception as e:
            logger.error(f"Failed to initialize FinBERT for Reddit: {e}")
            self.sentiment_analyzer = None

    def get_reddit_sentiment(
        self,
        symbol: str,
        lookback_hours: int = 24,
        max_posts: int = 50,
        subreddits: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze Reddit sentiment for a trading symbol.

        Args:
            symbol: Stock symbol (e.g., 'SPY', 'TSLA', 'AAPL')
            lookback_hours: How many hours back to search
            max_posts: Maximum number of posts to analyze per subreddit
            subreddits: List of subreddits to search (default: wallstreetbets, stocks, investing)

        Returns:
            Dict containing:
            - overall_sentiment: 'positive', 'negative', or 'neutral'
            - sentiment_score: Aggregate score (-1 to 1)
            - confidence: Confidence in the sentiment (0 to 1)
            - mention_count: Number of mentions found
            - post_count: Number of posts mentioning the symbol
            - comment_count: Number of comments analyzed
            - trending_score: Trending metric (mentions per hour)
            - top_posts: List of top posts
        """
        if not self.reddit:
            return {
                "error": "Reddit API not available",
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "mention_count": 0
            }

        if not self.sentiment_analyzer:
            return {
                "error": "Sentiment analyzer not available",
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "mention_count": 0
            }

        # Default subreddits
        if subreddits is None:
            subreddits = ["wallstreetbets", "stocks", "investing"]

        try:
            # Calculate time threshold
            cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
            cutoff_timestamp = cutoff_time.timestamp()

            # Collect mentions across subreddits
            all_mentions = []
            post_count = 0
            comment_count = 0

            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)

                    # Search for posts mentioning the symbol
                    for post in subreddit.search(
                        f"${symbol} OR {symbol}",
                        time_filter="day",
                        limit=max_posts
                    ):
                        # Check if post is within time window
                        if post.created_utc < cutoff_timestamp:
                            continue

                        post_count += 1

                        # Analyze post title and body
                        text = f"{post.title} {post.selftext}".strip()
                        if text and len(text) > 10:
                            scores = self.sentiment_analyzer.polarity_scores(text)
                            all_mentions.append({
                                "type": "post",
                                "subreddit": subreddit_name,
                                "text": text[:500],  # Limit for storage
                                "title": post.title,
                                "score": post.score,
                                "upvote_ratio": post.upvote_ratio,
                                "num_comments": post.num_comments,
                                "sentiment": scores,
                                "created_utc": post.created_utc,
                                "url": post.url
                            })

                        # Analyze top comments (first 10)
                        try:
                            post.comments.replace_more(limit=0)  # Don't expand "load more comments"
                            for comment in post.comments[:10]:
                                if not hasattr(comment, 'body'):
                                    continue

                                comment_text = comment.body.strip()
                                if comment_text and len(comment_text) > 10:
                                    comment_count += 1
                                    scores = self.sentiment_analyzer.polarity_scores(comment_text)
                                    all_mentions.append({
                                        "type": "comment",
                                        "subreddit": subreddit_name,
                                        "text": comment_text[:500],
                                        "score": comment.score,
                                        "sentiment": scores,
                                        "created_utc": comment.created_utc
                                    })
                        except Exception as e:
                            logger.debug(f"Could not fetch comments for post: {e}")
                            continue

                except Exception as e:
                    logger.warning(f"Error searching subreddit {subreddit_name}: {e}")
                    continue

            if not all_mentions:
                logger.info(f"No Reddit mentions found for {symbol} in the last {lookback_hours} hours")
                return {
                    "overall_sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "confidence": 0.0,
                    "mention_count": 0,
                    "post_count": 0,
                    "comment_count": 0,
                    "trending_score": 0.0,
                    "top_posts": []
                }

            # Aggregate sentiment scores
            sentiments = [m["sentiment"] for m in all_mentions]
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
            positive_count = sum(1 for s in sentiments if s["compound"] > 0.05)
            negative_count = sum(1 for s in sentiments if s["compound"] < -0.05)
            neutral_count = len(sentiments) - positive_count - negative_count

            max_agreement = max(positive_count, negative_count, neutral_count)
            confidence = max_agreement / len(sentiments) if len(sentiments) > 0 else 0

            # Calculate trending score (mentions per hour)
            trending_score = len(all_mentions) / lookback_hours if lookback_hours > 0 else 0

            # Get top posts by score
            posts_only = [m for m in all_mentions if m["type"] == "post"]
            top_posts = sorted(posts_only, key=lambda x: x.get("score", 0), reverse=True)[:5]
            top_post_titles = [
                {
                    "title": p["title"],
                    "score": p["score"],
                    "upvote_ratio": p.get("upvote_ratio", 0),
                    "num_comments": p.get("num_comments", 0),
                    "subreddit": p["subreddit"],
                    "sentiment": p["sentiment"]["compound"]
                }
                for p in top_posts
            ]

            result = {
                "overall_sentiment": overall,
                "sentiment_score": round(avg_compound, 3),
                "confidence": round(confidence, 2),
                "mention_count": len(all_mentions),
                "post_count": post_count,
                "comment_count": comment_count,
                "trending_score": round(trending_score, 2),
                "top_posts": top_post_titles,
                "details": {
                    "positive": round(avg_pos, 2),
                    "negative": round(avg_neg, 2),
                    "neutral": round(avg_neu, 2),
                    "positive_mentions": positive_count,
                    "negative_mentions": negative_count,
                    "neutral_mentions": neutral_count
                },
                "subreddits_searched": subreddits
            }

            logger.info(
                f"Reddit sentiment for {symbol}: {overall} "
                f"(score: {avg_compound:.2f}, confidence: {confidence:.2f}, "
                f"mentions: {len(all_mentions)}, posts: {post_count}, "
                f"comments: {comment_count}, trending: {trending_score:.2f}/hr)"
            )

            return result

        except Exception as e:
            logger.error(f"Error analyzing Reddit sentiment for {symbol}: {e}")
            return {
                "error": str(e),
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "mention_count": 0
            }


def get_reddit_analyzer() -> RedditAnalyzer:
    """Factory function to get Reddit analyzer instance."""
    return RedditAnalyzer()
