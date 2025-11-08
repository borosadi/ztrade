# ADR-002: Multi-Source Sentiment Analysis Integration

**Date**: 2025-11-07
**Status**: Implemented

## Decision

Integrate multi-source sentiment analysis using weighted aggregation from News, Reddit, and SEC filings to provide comprehensive market sentiment for trading decisions.

## Rationale

- Single-source sentiment (news only) provides limited perspective
- Retail sentiment (Reddit) offers early signals and contrarian indicators
- Official filings (SEC) provide fundamental event detection
- Weighted aggregation reduces bias from any single source
- Graceful degradation when sources are unavailable

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Multi-Source Sentiment Engine           │
└─────────────────────────────────────────────────┘
                      │
          ┌───────────┼───────────┬───────────┐
          │           │           │           │
     ┌────▼───┐  ┌───▼────┐  ┌──▼─────┐  ┌──▼─────┐
     │ News   │  │Reddit  │  │ SEC    │  │StockTwits│
     │(Alpaca)│  │(PRAW)  │  │(EDGAR) │  │(Future) │
     └────┬───┘  └───┬────┘  └──┬─────┘  └──┬─────┘
          │          │          │           │
     Weight: 40%  Weight: 25% Weight: 25% Weight: 10%
          │          │          │           │
          └──────────┴──────────┴───────────┘
                      │
            ┌─────────▼──────────┐
            │  Aggregate Score   │
            │  Confidence Level  │
            │  Source Breakdown  │
            └────────────────────┘
```

## Components Created

### 1. `cli/utils/news_analyzer.py` (289 lines)
- Fetches news via Alpaca News API (Benzinga)
- VADER sentiment on full article content (up to 5000 chars)
- Parameters: `include_content=True`, `exclude_contentless=True`, 25 articles max
- Returns: sentiment score, confidence, article count, top headlines
- API call: line 218 (`news_client.get_news(request)`)

### 2. `cli/utils/reddit_analyzer.py` (285 lines)
- Scrapes r/wallstreetbets, r/stocks, r/investing via PRAW
- Analyzes posts + top 10 comments per post
- VADER sentiment on combined text
- Returns: mention count, trending score (mentions/hour), top posts
- Requires credentials: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`
- Gracefully falls back if credentials missing

### 3. `cli/utils/sec_analyzer.py` (316 lines)
- Fetches SEC EDGAR filings (10-K, 10-Q, 8-K)
- CIK lookup via `company_tickers.json`
- Material event detection (8-K filings)
- Keyword-based sentiment (positive: "beat", "growth"; negative: "miss", "decline")
- Returns: filing count, material events, sentiment by filing type
- Currently limited by SEC API access policies (403 errors)

### 4. `cli/utils/sentiment_aggregator.py` (272 lines)
- Orchestrates all sentiment sources
- Weighted aggregation (configurable weights)
- Agreement level calculation (how much sources agree)
- Source breakdown in output
- Graceful handling of missing sources

## Weighting Strategy

- **News (40%)**: Most reliable, professional journalism, verified sources
- **Reddit (25%)**: Retail sentiment, early signals, high volume discussions
- **SEC (25%)**: Official filings, fundamental events, regulatory data
- **StockTwits (10%)**: Reserved for future implementation

## Integration Points

- `cli/utils/market_data.py:90-108`: Calls sentiment aggregator instead of news analyzer
- `cli/commands/agent.py:367-409`: Displays source breakdown in trading context
- Changed key from `news_sentiment` to `sentiment` in market context

## Example Output

```
Multi-Source Sentiment Analysis:
- Overall Sentiment: POSITIVE
- Sentiment Score: 0.95 (range: -1 to +1)
- Confidence: 100%
- Sources Used: news, reddit
- Agreement Level: 100%

News (Alpaca/Benzinga):
  Sentiment: POSITIVE (0.95)
  Articles: 19
  Top Headlines:
    1. Tesla Stock Surges on Strong Earnings Beat...
    2. Analysts Upgrade TSLA Price Target to $500...

Reddit (r/wallstreetbets, r/stocks):
  Sentiment: POSITIVE (0.82)
  Mentions: 147 (23 posts, 124 comments)
  Trending: 6.1 mentions/hour
  Top Post: "TSLA earnings call was fire 🚀🚀🚀" (1247 upvotes)

SEC Filings (EDGAR):
  Sentiment: POSITIVE (0.30)
  Recent Filings: 3 in last 30 days
  Material Events (8-K): 1
    - 2025-10-25: Material Event (sentiment: 0.40)
```

## Test Results (2025-11-07)

```bash
TSLA Multi-Source Sentiment:
- Overall: POSITIVE
- Score: 0.947
- Confidence: 100%
- Sources: news (19 articles)
- Agreement: 100%
```

## Configuration

To enable Reddit sentiment, add to `.env`:
```bash
# Get credentials at: https://www.reddit.com/prefs/apps
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT="Ztrade:v1.0 (by /u/your_username)"
```

## Dependencies Added

- `alpaca-py>=0.9.0`: Alpaca News API client
- `vaderSentiment>=3.3.2`: Sentiment analysis
- `praw>=7.7.1`: Reddit API wrapper (Python Reddit API Wrapper)

## Known Limitations

- SEC EDGAR API has strict access policies (currently returning 403 errors)
- Reddit requires free API credentials (system gracefully falls back)
- VADER is general-purpose (FinBERT would be more finance-specific)

## Future Enhancements

- FinBERT model for financial-specific sentiment (more accurate than VADER)
- StockTwits integration (finance-focused social media)
- Sentiment trend analysis (tracking changes over time)
- Entity extraction (identifying mentioned companies, Fed officials)
- Source credibility weighting (weight by historical accuracy)
- Cross-asset correlation detection (SPY sentiment affects TSLA, etc.)
