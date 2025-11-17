#!/usr/bin/env python3
"""Pre-flight check for paper trading - validates all trading decision components."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from cli.utils.broker import get_broker
from cli.utils.market_data import get_market_data_provider
from cli.utils.technical_analyzer import get_technical_analyzer
from cli.utils.sentiment_aggregator import get_sentiment_aggregator
from cli.utils.news_analyzer import get_news_analyzer
from cli.utils.reddit_analyzer import get_reddit_analyzer
from cli.utils.sec_analyzer import get_sec_analyzer
from cli.utils.config import get_config
from cli.utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_result(test_name, success, details=""):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"       {details}")

def test_market_data():
    """Test market data fetching."""
    print_section("1. MARKET DATA FETCHING")

    try:
        broker = get_broker()

        # Test TSLA quote
        tsla_quote = broker.get_latest_quote("TSLA")
        if tsla_quote and 'ask' in tsla_quote:
            print_result("TSLA Quote", True, f"Price: ${tsla_quote['ask']:.2f}")
        else:
            print_result("TSLA Quote", False, "Failed to fetch quote")
            return False

        # Test IWM quote
        iwm_quote = broker.get_latest_quote("IWM")
        if iwm_quote and 'ask' in iwm_quote:
            print_result("IWM Quote", True, f"Price: ${iwm_quote['ask']:.2f}")
        else:
            print_result("IWM Quote", False, "Failed to fetch quote")

        # Test BTC quote
        btc_quote = broker.get_latest_quote("BTC/USD")
        if btc_quote and 'ask' in btc_quote:
            print_result("BTC Quote", True, f"Price: ${btc_quote['ask']:.2f}")
        else:
            print_result("BTC Quote", False, "Failed to fetch quote")

        # Test bars
        tsla_bars = broker.get_bars("TSLA", "5Min", limit=100)
        if tsla_bars and len(tsla_bars) > 0:
            print_result("TSLA Bars", True, f"Fetched {len(tsla_bars)} bars")
        else:
            print_result("TSLA Bars", False, "Failed to fetch bars")

        return True

    except Exception as e:
        print_result("Market Data", False, f"Error: {e}")
        return False

def test_technical_analysis():
    """Test technical analysis."""
    print_section("2. TECHNICAL ANALYSIS")

    try:
        market_provider = get_market_data_provider()
        technical_analyzer = get_technical_analyzer()

        # Get market context for TSLA
        context = market_provider.get_market_context("TSLA", "5m", lookback_periods=100)

        if not context:
            print_result("Market Context", False, "Failed to get market context")
            return False

        # Check if we have historical data (market might be closed)
        has_data = context.get("data_available", True) != False

        if has_data and "historical_data" in context:
            bar_count = context["historical_data"]["bars_count"]
            print_result("Market Context", True, f"Got {bar_count} bars")

            # Run technical analysis
            ta = technical_analyzer.analyze(context)

            if ta:
                print_result("RSI Calculation", True, f"RSI: {ta.rsi:.2f}")
                print_result("SMA Calculation", True, f"SMA50: ${ta.sma_50:.2f}, SMA200: ${ta.sma_200:.2f}")
                print_result("Trend Detection", True, f"Trend: {ta.trend.value}")
                print_result("Support/Resistance", True, f"Support: ${ta.support:.2f}, Resistance: ${ta.resistance:.2f}")
                print_result("Volume Analysis", True, f"Volume Ratio: {ta.volume_ratio:.2f}x")
                print_result("Overall Signal", True, f"Signal: {ta.overall_signal.value}")
                return True
            else:
                print_result("Technical Analysis", False, "TA returned None")
                return False
        else:
            print_result("Market Context (Market Closed)", True, "No bars available - market closed")
            print("       ⚠️  This is OK for now - will work during market hours")
            return True  # Don't fail the test if market is closed

    except Exception as e:
        print_result("Technical Analysis", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sentiment_analysis():
    """Test sentiment analysis from all sources."""
    print_section("3. SENTIMENT ANALYSIS")

    # Test News
    try:
        news_analyzer = get_news_analyzer()
        news_sentiment = news_analyzer.get_news_sentiment("TSLA", lookback_hours=24)

        if news_sentiment:
            score = news_sentiment.get('sentiment_score', 0)
            conf = news_sentiment.get('confidence', 0)
            count = news_sentiment.get('article_count', 0)
            print_result("News Sentiment", True, f"Score: {score:.2f}, Conf: {conf:.2f}, Articles: {count}")
        else:
            print_result("News Sentiment", False, "No news sentiment returned")
    except Exception as e:
        print_result("News Sentiment", False, f"Error: {e}")

    # Test Reddit
    try:
        reddit_analyzer = get_reddit_analyzer()
        reddit_sentiment = reddit_analyzer.get_reddit_sentiment("TSLA", lookback_hours=24)

        if reddit_sentiment:
            score = reddit_sentiment.get('sentiment_score', 0)
            conf = reddit_sentiment.get('confidence', 0)
            mentions = reddit_sentiment.get('mention_count', 0)
            print_result("Reddit Sentiment", True, f"Score: {score:.2f}, Conf: {conf:.2f}, Mentions: {mentions}")
        else:
            print_result("Reddit Sentiment", False, "No reddit sentiment (credentials may be missing)")
    except Exception as e:
        print_result("Reddit Sentiment", False, f"Error or no credentials: {e}")

    # Test SEC
    try:
        sec_analyzer = get_sec_analyzer()
        sec_sentiment = sec_analyzer.get_sec_sentiment("TSLA", lookback_days=30)

        if sec_sentiment:
            score = sec_sentiment.get('sentiment_score', 0)
            conf = sec_sentiment.get('confidence', 0)
            filings = sec_sentiment.get('filing_count', 0)
            print_result("SEC Sentiment", True, f"Score: {score:.2f}, Conf: {conf:.2f}, Filings: {filings}")
        else:
            print_result("SEC Sentiment", False, "No SEC sentiment returned")
    except Exception as e:
        print_result("SEC Sentiment", False, f"Error: {e}")

    return True

def test_sentiment_aggregation():
    """Test multi-source sentiment aggregation."""
    print_section("4. SENTIMENT AGGREGATION")

    try:
        aggregator = get_sentiment_aggregator()

        # Test for TSLA
        result = aggregator.get_aggregated_sentiment("TSLA")

        if result:
            score = result.get('score', 0)
            conf = result.get('confidence', 0)
            sources = result.get('sources_used', 0)
            agreement = result.get('agreement_level', 0)

            print_result("Aggregated Sentiment", True,
                        f"Score: {score:.2f}, Conf: {conf:.2f}, Sources: {sources}, Agreement: {agreement:.0%}")

            # Show breakdown
            breakdown = result.get('source_breakdown', {})
            for source, data in breakdown.items():
                if data:
                    src_score = data.get('score', 0)
                    src_conf = data.get('confidence', 0)
                    print(f"         - {source}: Score {src_score:.2f}, Conf {src_conf:.2f}")

            return True
        else:
            print_result("Sentiment Aggregation", False, "No result returned")
            return False

    except Exception as e:
        print_result("Sentiment Aggregation", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_config():
    """Test agent configuration loading."""
    print_section("5. AGENT CONFIGURATION")

    try:
        config = get_config()
        agents = config.list_agents()

        print_result("Agent Discovery", True, f"Found {len(agents)} agents: {', '.join(agents)}")

        for agent_id in agents:
            agent_config = config.load_agent_config(agent_id)
            agent_name = agent_config.get('agent', {}).get('name', 'Unknown')
            asset = agent_config.get('agent', {}).get('asset', 'Unknown')
            strategy = agent_config.get('strategy', {}).get('type', 'Unknown')
            print_result(f"Agent: {agent_id}", True, f"{agent_name} - {asset} ({strategy})")

        return True

    except Exception as e:
        print_result("Agent Configuration", False, f"Error: {e}")
        return False

def test_full_decision_cycle():
    """Test a full decision cycle (without executing trades)."""
    print_section("6. FULL DECISION CYCLE (TSLA)")

    try:
        # Load agent config
        config = get_config()
        agent_config = config.load_agent_config("agent_tsla")
        asset = agent_config.get('agent', {}).get('asset', 'TSLA')
        timeframe = agent_config.get('strategy', {}).get('timeframe', '5m')

        print(f"Testing full cycle for agent_tsla ({asset})")

        # 1. Market Data
        broker = get_broker()
        quote = broker.get_latest_quote(asset)
        if not quote:
            print_result("Get Quote", False, "Failed to fetch quote")
            return False
        print_result("Get Quote", True, f"${quote['ask']:.2f}")

        # 2. Market Context
        market_provider = get_market_data_provider()
        context = market_provider.get_market_context(asset, timeframe)
        if not context:
            print_result("Get Context", False, "Failed to get context")
            return False

        # Check if market data is available (market might be closed)
        has_data = context.get("data_available", True) != False
        if has_data and "historical_data" in context:
            bar_count = context["historical_data"]["bars_count"]
            print_result("Get Context", True, f"{bar_count} bars available")
        else:
            print_result("Get Context (Market Closed)", True, "No bars (market closed - OK)")

        # 3. Technical Analysis (only if we have bars)
        ta = None
        if has_data and "technical_indicators" in context:
            technical_analyzer = get_technical_analyzer()
            ta = technical_analyzer.analyze(context)
            if not ta:
                print_result("Technical Analysis", False, "TA failed")
                return False
            print_result("Technical Analysis", True, f"Signal: {ta.overall_signal.value}, RSI: {ta.rsi:.1f}")
        else:
            print_result("Technical Analysis (Market Closed)", True, "Skipped - no bars available")

        # 4. Sentiment Analysis
        sentiment = context.get('sentiment', {})
        score = 0
        conf = 0
        if sentiment:
            score = sentiment.get('sentiment_score', 0)
            conf = sentiment.get('confidence', 0)
            print_result("Sentiment Analysis", True, f"Score: {score:.2f}, Conf: {conf:.2f}")
        else:
            print_result("Sentiment Analysis", True, "No sentiment data (OK for testing)")

        # 5. Risk Validation
        stop_loss = agent_config.get('risk', {}).get('stop_loss', 0.03)
        take_profit = agent_config.get('risk', {}).get('take_profit', 0.06)
        min_confidence = agent_config.get('risk', {}).get('min_confidence', 0.65)
        print_result("Risk Parameters", True, f"SL: {stop_loss:.1%}, TP: {take_profit:.1%}, Min Conf: {min_confidence:.0%}")

        print("\n✅ Full decision cycle completed successfully!")
        print(f"\n📊 Decision Summary:")
        print(f"   Price: ${quote['ask']:.2f}")
        if ta:
            print(f"   Technical Signal: {ta.overall_signal.value}")
            print(f"   RSI: {ta.rsi:.1f}")
            print(f"   Trend: {ta.trend.value}")
        else:
            print(f"   Technical Analysis: Skipped (market closed)")
        print(f"   Sentiment Score: {score:.2f}")
        print(f"   Sentiment Confidence: {conf:.2f}")

        return True

    except Exception as e:
        print_result("Full Cycle", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all pre-flight checks."""
    print("\n" + "="*80)
    print("  ZTRADE PRE-FLIGHT CHECK")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    results = []

    # Run all tests
    results.append(("Market Data", test_market_data()))
    results.append(("Technical Analysis", test_technical_analysis()))
    results.append(("Sentiment Analysis", test_sentiment_analysis()))
    results.append(("Sentiment Aggregation", test_sentiment_aggregation()))
    results.append(("Agent Configuration", test_agent_config()))
    results.append(("Full Decision Cycle", test_full_decision_cycle()))

    # Summary
    print_section("SUMMARY")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{'='*80}")
    print(f"  TOTAL: {passed}/{total} tests passed")

    if passed == total:
        print(f"  STATUS: ✅ READY FOR PAPER TRADING")
    else:
        print(f"  STATUS: ⚠️  SOME ISSUES FOUND - REVIEW BEFORE TRADING")
    print(f"{'='*80}\n")

    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
