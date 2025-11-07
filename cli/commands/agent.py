"""Agent management commands."""
import click
import json
from datetime import datetime
from pathlib import Path
from cli.utils.config import get_config
from cli.utils.llm import get_agent_llm
from cli.utils.broker import get_broker
from cli.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def agent():
    """Commands for managing trading agents."""
    pass


@agent.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
def list(verbose):
    """Lists all available agents."""
    config = get_config()
    agents = config.list_agents()

    if not agents:
        click.echo("No agents found.")
        return

    click.echo(f"\n{'='*60}")
    click.echo(f"Found {len(agents)} agent(s):\n")

    for agent_id in sorted(agents):
        agent_config = config.load_agent_config(agent_id)
        agent_state = config.load_agent_state(agent_id)

        # Basic info
        agent_info = agent_config.get('agent', {})
        name = agent_info.get('name', agent_id)
        asset = agent_info.get('asset', 'N/A')
        status = agent_info.get('status', 'unknown')

        click.echo(f"  [{agent_id}]")
        click.echo(f"    Name: {name}")
        click.echo(f"    Asset: {asset}")
        click.echo(f"    Status: {status}")

        if verbose and agent_state:
            pnl = agent_state.get('pnl_today', 0)
            trades = agent_state.get('trades_today', 0)
            positions = len(agent_state.get('positions', []))
            click.echo(f"    Positions: {positions}")
            click.echo(f"    Daily P&L: ${pnl:.2f}")
            click.echo(f"    Trades Today: {trades}")

        click.echo()

    click.echo(f"{'='*60}\n")


@agent.command()
@click.argument('agent_id')
@click.option('--asset', prompt='Asset symbol', help='Asset to trade (e.g., BTC/USD, SPY)')
@click.option('--name', prompt='Agent name', help='Descriptive name for the agent')
@click.option('--strategy', type=click.Choice(['momentum', 'mean_reversion', 'breakout']),
              prompt='Strategy type', help='Trading strategy')
@click.option('--risk-tolerance', type=click.Choice(['conservative', 'moderate', 'aggressive']),
              prompt='Risk tolerance', help='Risk profile')
@click.option('--capital', type=float, default=10000, help='Allocated capital')
def create(agent_id, asset, name, strategy, risk_tolerance, capital):
    """Creates a new agent."""
    config = get_config()

    # Check if agent already exists
    if config.agent_exists(agent_id):
        click.echo(f"Error: Agent '{agent_id}' already exists!", err=True)
        return

    # Create agent directory
    agent_dir = config.get_agent_dir(agent_id)
    agent_dir.mkdir(parents=True, exist_ok=True)

    # Create context.yaml
    context = {
        'agent': {
            'id': agent_id,
            'name': name,
            'asset': asset,
            'status': 'active',
            'created': datetime.now().isoformat(),
        },
        'strategy': {
            'type': strategy,
            'timeframe': '15m',
        },
        'risk': {
            'max_position_size': capital * 0.5,
            'stop_loss': 0.02,
            'take_profit': 0.04,
            'max_daily_trades': 5,
        },
        'personality': {
            'risk_tolerance': risk_tolerance,
        },
        'performance': {
            'allocated_capital': capital,
        }
    }
    config.save_yaml(context, str(agent_dir / 'context.yaml'))

    # Create initial state.json
    state = {
        'positions': [],
        'trades_today': 0,
        'pnl_today': 0.0,
        'last_update': datetime.now().isoformat(),
    }
    config.save_json(state, str(agent_dir / 'state.json'))

    # Create initial performance.json
    performance = {
        'total_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'total_pnl': 0.0,
    }
    config.save_json(performance, str(agent_dir / 'performance.json'))

    # Create initial learning.json
    learning = {
        'patterns_learned': {},
        'market_regimes': {},
    }
    config.save_json(learning, str(agent_dir / 'learning.json'))

    # Create personality.md template
    personality = f"""# {name} Trading Philosophy

## Identity
I am a {risk_tolerance} {strategy} trader specializing in {asset}.

## Core Strategy
- **Strategy Type**: {strategy}
- **Risk Tolerance**: {risk_tolerance}
- **Timeframe**: 15-minute charts

## Trading Rules
- Maximum position size: ${capital * 0.5:.2f}
- Stop loss: 2%
- Take profit: 4%
- Maximum 5 trades per day

## Market Conditions
**Best Performance In:**
- Clear trending markets
- High volume periods

**Avoid Trading During:**
- Low volume periods
- High uncertainty events
"""
    with open(agent_dir / 'personality.md', 'w') as f:
        f.write(personality)

    click.echo(f"\n✓ Agent '{agent_id}' created successfully!")
    click.echo(f"  Name: {name}")
    click.echo(f"  Asset: {asset}")
    click.echo(f"  Strategy: {strategy}")
    click.echo(f"  Capital: ${capital:.2f}\n")


@agent.command()
@click.argument('agent_id')
def status(agent_id):
    """Shows the status of a specific agent."""
    config = get_config()

    if not config.agent_exists(agent_id):
        click.echo(f"Error: Agent '{agent_id}' not found!", err=True)
        return

    # Load agent data
    agent_config = config.load_agent_config(agent_id)
    agent_state = config.load_agent_state(agent_id)

    agent_info = agent_config.get('agent', {})
    risk_info = agent_config.get('risk', {})
    performance = agent_config.get('performance', {})

    # Display status
    click.echo(f"\n{'='*60}")
    click.echo(f"Agent Status: {agent_id}")
    click.echo(f"{'='*60}\n")

    click.echo(f"Name: {agent_info.get('name', 'N/A')}")
    click.echo(f"Asset: {agent_info.get('asset', 'N/A')}")
    click.echo(f"Status: {agent_info.get('status', 'unknown')}")
    click.echo(f"Created: {agent_info.get('created', 'N/A')}\n")

    click.echo(f"Strategy:")
    strategy = agent_config.get('strategy', {})
    click.echo(f"  Type: {strategy.get('type', 'N/A')}")
    click.echo(f"  Timeframe: {strategy.get('timeframe', 'N/A')}\n")

    click.echo(f"Current State:")
    click.echo(f"  Positions: {len(agent_state.get('positions', []))}")
    click.echo(f"  Daily P&L: ${agent_state.get('pnl_today', 0):.2f}")
    click.echo(f"  Trades Today: {agent_state.get('trades_today', 0)}/{risk_info.get('max_daily_trades', 'N/A')}")
    click.echo(f"  Last Update: {agent_state.get('last_update', 'N/A')}\n")

    click.echo(f"Risk Parameters:")
    click.echo(f"  Allocated Capital: ${performance.get('allocated_capital', 0):.2f}")
    click.echo(f"  Max Position Size: ${risk_info.get('max_position_size', 0):.2f}")
    click.echo(f"  Stop Loss: {risk_info.get('stop_loss', 0)*100:.1f}%")
    click.echo(f"  Take Profit: {risk_info.get('take_profit', 0)*100:.1f}%\n")

    # Show positions if any
    positions = agent_state.get('positions', [])
    if positions:
        click.echo(f"Open Positions:")
        for pos in positions:
            click.echo(f"  {pos.get('symbol', 'N/A')}: {pos.get('quantity', 0)} @ ${pos.get('entry_price', 0):.2f}")
            click.echo(f"    P&L: ${pos.get('unrealized_pnl', 0):.2f}\n")

    click.echo(f"{'='*60}\n")


@agent.command()
@click.argument('agent_id')
@click.argument('question')
def ask(agent_id, question):
    """Asks an agent for analysis."""
    config = get_config()

    if not config.agent_exists(agent_id):
        click.echo(f"Error: Agent '{agent_id}' not found!", err=True)
        return

    # Load agent personality
    personality = config.load_agent_personality(agent_id)
    agent_config = config.load_agent_config(agent_id)

    click.echo(f"\nAsking {agent_id}: {question}\n")

    try:
        llm = get_agent_llm()
        response = llm.ask(
            prompt=question,
            system_prompt=f"You are a trading agent. {personality}"
        )
        click.echo(f"Response:\n{response}\n")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@agent.command()
@click.argument('agent_id')
@click.option('--dry-run', is_flag=True, help='Simulate without executing trades')
@click.option('--manual', is_flag=True, help='Manual mode: use Claude Code for decisions instead of API')
@click.option('--subagent', is_flag=True, help='Subagent mode: automatically use Claude Code subagent for decisions')
def run(agent_id, dry_run, manual, subagent):
    """Runs an agent's trading cycle."""
    from cli.utils.broker import get_broker
    from cli.utils.risk import RiskValidator
    from cli.utils.trade_executor import TradeExecutor
    import json
    import re

    config = get_config()

    if not config.agent_exists(agent_id):
        click.echo(f"Error: Agent '{agent_id}' not found!", err=True)
        return

    # Load agent configuration
    agent_config = config.load_agent_config(agent_id)
    agent_state = config.load_agent_state(agent_id)

    asset = agent_config.get('agent', {}).get('asset', 'UNKNOWN')
    status = agent_config.get('agent', {}).get('status', 'paused')

    if dry_run:
        click.echo(f"\n🔍 DRY RUN MODE - No trades will be executed\n")

    if manual:
        click.echo(f"\n🤖 MANUAL MODE - Using Claude Code for decisions\n")

    if subagent:
        click.echo(f"\n🤖 SUBAGENT MODE - Automatically using Claude Code subagent for decisions\n")

    click.echo(f"Running trading cycle for {agent_id} ({asset})...")

    # Check if agent is active
    if status != 'active' and not dry_run and not manual and not subagent:
        click.echo(f"Agent is {status}, not active. Skipping.", err=True)
        return

    try:
        # Step 1: Get current market data
        click.echo("1. Fetching market data...")

        broker = get_broker()

        try:
            # Get latest price from Alpaca
            quote = broker.get_latest_quote(asset)

            if not quote:
                click.echo("Could not fetch current price. Aborting.", err=True)
                return

            current_price = quote.get('ask', 0)

            if current_price == 0:
                click.echo("Could not fetch current price. Aborting.", err=True)
                return

            click.echo(f"   Current price for {asset}: ${current_price:.2f}")
        except Exception as e:
            click.echo(f"Error fetching market data: {e}", err=True)
            return

        # Step 2: Get market analysis
        click.echo("2. Analyzing market data...")

        # Get comprehensive market context
        from cli.utils.market_data import get_market_data_provider
        from cli.utils.technical_analyzer import get_technical_analyzer
        import time

        performance_metrics = {}

        try:
            # Fetch market data
            start_time = time.time()
            market_provider = get_market_data_provider()
            timeframe = agent_config.get('strategy', {}).get('timeframe', '15m')
            market_context = market_provider.get_market_context(asset, timeframe)
            performance_metrics['data_fetch_ms'] = (time.time() - start_time) * 1000

            # Run technical analysis (hybrid approach: traditional methods)
            start_time = time.time()
            technical_analyzer = get_technical_analyzer()
            technical_analysis = technical_analyzer.analyze(market_context)
            performance_metrics['technical_analysis_ms'] = technical_analysis.computation_time_ms

            # Log TA performance
            click.echo(f"   Technical analysis completed in {technical_analysis.computation_time_ms:.1f}ms")
            click.echo(f"   Overall signal: {technical_analysis.overall_signal.value} (confidence: {technical_analysis.overall_confidence:.2f})")

            # Build market analysis summary using structured signals
            market_summary = f"""
Market Analysis for {asset}:
- Current Price: ${current_price:.2f}

Technical Analysis Summary:
- Overall Signal: {technical_analysis.overall_signal.value.upper()}
- Overall Confidence: {technical_analysis.overall_confidence:.2%}
- Analysis Time: {technical_analysis.computation_time_ms:.1f}ms

Individual Technical Signals:
"""
            for signal in technical_analysis.signals:
                market_summary += f"  [{signal.signal.value.upper()}] {signal.indicator}: {signal.reasoning} (confidence: {signal.confidence:.2f})\n"

            # Add multi-source sentiment if available
            if 'sentiment' in market_context:
                sentiment = market_context['sentiment']
                market_summary += f"""
Multi-Source Sentiment Analysis:
- Overall Sentiment: {sentiment.get('overall_sentiment', 'neutral').upper()}
- Sentiment Score: {sentiment.get('sentiment_score', 0):.2f} (range: -1 to +1)
- Confidence: {sentiment.get('confidence', 0):.2%}
- Sources Used: {', '.join(sentiment.get('sources_used', []))}
- Agreement Level: {sentiment.get('agreement_level', 0):.0%}
"""
                # Add breakdown by source
                source_breakdown = sentiment.get('source_breakdown', {})

                if 'news' in source_breakdown:
                    news = source_breakdown['news']
                    market_summary += f"\nNews (Alpaca/Benzinga):\n"
                    market_summary += f"  Sentiment: {news.get('overall_sentiment', 'neutral').upper()} ({news.get('sentiment_score', 0):.2f})\n"
                    market_summary += f"  Articles: {news.get('article_count', 0)}\n"
                    if news.get('top_headlines'):
                        market_summary += f"  Top Headlines:\n"
                        for i, headline in enumerate(news.get('top_headlines', [])[:2], 1):
                            market_summary += f"    {i}. {headline}\n"

                if 'reddit' in source_breakdown:
                    reddit = source_breakdown['reddit']
                    market_summary += f"\nReddit (r/wallstreetbets, r/stocks):\n"
                    market_summary += f"  Sentiment: {reddit.get('overall_sentiment', 'neutral').upper()} ({reddit.get('sentiment_score', 0):.2f})\n"
                    market_summary += f"  Mentions: {reddit.get('mention_count', 0)} ({reddit.get('post_count', 0)} posts, {reddit.get('comment_count', 0)} comments)\n"
                    market_summary += f"  Trending: {reddit.get('trending_score', 0):.1f} mentions/hour\n"
                    if reddit.get('top_posts'):
                        top_post = reddit['top_posts'][0]
                        market_summary += f"  Top Post: \"{top_post.get('title', 'N/A')[:80]}...\" ({top_post.get('score', 0)} upvotes)\n"

                if 'sec' in source_breakdown:
                    sec = source_breakdown['sec']
                    market_summary += f"\nSEC Filings (EDGAR):\n"
                    market_summary += f"  Sentiment: {sec.get('overall_sentiment', 'neutral').upper()} ({sec.get('sentiment_score', 0):.2f})\n"
                    market_summary += f"  Recent Filings: {sec.get('filing_count', 0)} in last {sec.get('lookback_days', 30)} days\n"
                    if sec.get('material_events'):
                        market_summary += f"  Material Events (8-K): {len(sec['material_events'])}\n"
                        for event in sec['material_events'][:2]:
                            market_summary += f"    - {event.get('date')}: {event.get('description')} (sentiment: {event.get('sentiment', 0):.2f})\n"

            if not market_context.get('historical_data'):
                market_summary += "\nNote: Limited historical data available. Analysis based on current price only.\n"

        except Exception as e:
            logger.warning(f"Could not fetch market analysis: {e}")
            market_summary = f"Current Price: ${current_price:.2f}\n(Market analysis unavailable)"
            performance_metrics['error'] = str(e)

        # Step 3: Build context for AI decision
        click.echo("3. Building decision context...")

        # Read personality file if it exists
        personality_file = config.get_agent_dir(agent_id) / 'personality.md'
        personality = ""
        if personality_file.exists():
            with open(personality_file, 'r') as f:
                personality = f.read()

        context = f"""You are {agent_config.get('agent', {}).get('name', agent_id)}, an autonomous trading agent.

Asset: {asset}
Strategy: {agent_config.get('strategy', {}).get('type', 'N/A')}
Timeframe: {agent_config.get('strategy', {}).get('timeframe', 'N/A')}

{market_summary}

Your Personality and Approach:
{personality}

Current State:
- Positions: {len(agent_state.get('positions', []))}
- Daily P&L: ${agent_state.get('pnl_today', 0):.2f}
- Trades Today: {agent_state.get('trades_today', 0)}/{agent_config.get('risk', {}).get('max_daily_trades', 10)}

Risk Parameters:
- Max Position Size: ${agent_config.get('risk', {}).get('max_position_size', 5000):.2f}
- Stop Loss: {agent_config.get('risk', {}).get('stop_loss', 0.02)*100:.1f}%
- Min Confidence: {agent_config.get('risk', {}).get('min_confidence', 0.6)*100:.0f}%

Based on the current market conditions and your trading strategy, make a decision.

Respond with a JSON object in this format:
{{
    "action": "buy" | "sell" | "hold",
    "quantity": <number of shares, required for buy/sell>,
    "rationale": "<your reasoning>",
    "confidence": <0.0 to 1.0>,
    "stop_loss": <price level, required for buy>
}}
"""

        # Step 4: Get AI decision
        if subagent:
            click.echo("4. Launching Claude Code subagent for decision...")

            from cli.utils.subagent import get_subagent_communicator

            # Create a prompt for the subagent
            subagent_prompt = f"""You are a trading decision subagent. Analyze the following trading context and provide a JSON trading decision.

{context}

CRITICAL: You must respond with ONLY a valid JSON object in this exact format (no other text):

{{
    "action": "buy" | "sell" | "hold",
    "quantity": <number>,
    "rationale": "<your reasoning>",
    "confidence": <0.0 to 1.0>,
    "stop_loss": <price level, required for buy>
}}

Examples:
- Hold: {{"action": "hold", "quantity": 0, "rationale": "Waiting for clearer signal", "confidence": 0.6}}
- Buy: {{"action": "buy", "quantity": 100, "rationale": "Strong momentum breakout", "confidence": 0.85, "stop_loss": 34500.00}}
- Sell: {{"action": "sell", "quantity": 100, "rationale": "Taking profits at resistance", "confidence": 0.75}}

Respond with ONLY the JSON object, nothing else."""

            try:
                start_time = time.time()
                communicator = get_subagent_communicator()
                decision = communicator.request_decision(agent_id, subagent_prompt, timeout=60)
                performance_metrics['llm_decision_ms'] = (time.time() - start_time) * 1000

                click.echo(f"   Decision received: {decision.get('action', 'unknown').upper()}")
                click.echo(f"   Confidence: {decision.get('confidence', 0)*100:.0f}%")
                click.echo(f"   LLM response time: {performance_metrics['llm_decision_ms']:.1f}ms")

            except TimeoutError as e:
                click.echo(f"\n✗ Timeout: {e}", err=True)
                click.echo("No response from Claude Code subagent. Cancelling trade cycle.")
                return
            except json.JSONDecodeError as e:
                click.echo(f"Error: Invalid JSON format: {e}", err=True)
                return
            except Exception as e:
                click.echo(f"Error in subagent mode: {e}", err=True)
                return

        elif manual:
            click.echo("4. Manual decision required...")
            click.echo("\n" + "="*70)
            click.echo("DECISION CONTEXT FOR CLAUDE CODE")
            click.echo("="*70)
            click.echo(context)
            click.echo("="*70)
            click.echo("\nCopy the context above and ask Claude Code to analyze it.")
            click.echo("Claude Code will provide a JSON decision in this format:")
            click.echo('{"action": "buy/sell/hold", "quantity": N, "rationale": "...", "confidence": 0.0-1.0, "stop_loss": price}')
            click.echo("\nPaste the JSON decision below (or press Enter to cancel):")

            decision_input = click.prompt("Decision JSON", default="", show_default=False)

            if not decision_input or decision_input.strip() == "":
                click.echo("No decision provided. Cancelling trade cycle.")
                return

            try:
                # Try to parse JSON from input
                json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', decision_input, re.DOTALL)
                if json_match:
                    decision = json.loads(json_match.group())
                else:
                    decision = json.loads(decision_input)

                click.echo(f"   Decision received: {decision.get('action', 'unknown').upper()}")
                click.echo(f"   Confidence: {decision.get('confidence', 0)*100:.0f}%")

            except json.JSONDecodeError as e:
                click.echo(f"Error: Invalid JSON format: {e}", err=True)
                return
        else:
            click.echo("4. Requesting AI decision...")

            # Check if API key is available
            import os
            api_key = os.getenv('ANTHROPIC_API_KEY', '')
            if not api_key or api_key == 'YOUR_API_KEY':
                click.echo("\n" + "="*70)
                click.secho("ERROR: No valid ANTHROPIC_API_KEY found!", fg='red', bold=True)
                click.echo("="*70)
                click.echo("\nYou have two options:")
                click.echo("1. Set a valid API key in your .env file")
                click.echo("2. Use manual mode: ztrade agent run {} --manual".format(agent_id))
                click.echo("\nManual mode lets you use Claude Code for trading decisions")
                click.echo("without needing an API key.\n")
                return

            from cli.utils.llm import get_llm
            llm = get_llm()

            try:
                response = llm.ask(context)
                click.echo(f"   Raw response length: {len(response)} characters")

                # Try to parse JSON from response
                json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', response, re.DOTALL)

                if json_match:
                    decision = json.loads(json_match.group())
                else:
                    click.echo(f"Could not parse decision from AI response", err=True)
                    click.echo(f"Response: {response[:200]}...")
                    return

                click.echo(f"   Decision: {decision.get('action', 'unknown').upper()}")
                click.echo(f"   Confidence: {decision.get('confidence', 0)*100:.0f}%")

            except Exception as e:
                click.echo(f"Error getting AI decision: {e}", err=True)
                return

        # Step 5: Validate against risk rules
        click.echo("5. Validating against risk rules...")
        validator = RiskValidator()

        is_valid, reason = validator.validate_trade(agent_id, decision, current_price)

        if not is_valid:
            click.secho(f"   ✗ Trade rejected: {reason}", fg='red')
            return

        click.secho(f"   ✓ Risk validation passed", fg='green')

        # Step 6: Execute or simulate trade
        click.echo(f"6. {'Simulating' if dry_run else 'Executing'} trade...")
        executor = TradeExecutor()

        result = executor.execute_trade(agent_id, decision, current_price, dry_run=dry_run)

        if result.get('success'):
            click.secho(f"\n✓ {result.get('message')}", fg='green')
        else:
            click.secho(f"\n✗ {result.get('message', 'Trade failed')}", fg='red')

        # Log performance metrics
        if performance_metrics:
            total_time = sum(v for k, v in performance_metrics.items() if k.endswith('_ms'))
            click.echo(f"\nPerformance Metrics:")
            click.echo(f"  Data fetch: {performance_metrics.get('data_fetch_ms', 0):.1f}ms")
            click.echo(f"  Technical analysis: {performance_metrics.get('technical_analysis_ms', 0):.1f}ms")
            click.echo(f"  LLM decision: {performance_metrics.get('llm_decision_ms', 0):.1f}ms")
            click.echo(f"  Total: {total_time:.1f}ms ({total_time/1000:.2f}s)")
            logger.info(f"Performance metrics for {agent_id}: {performance_metrics}")

    except Exception as e:
        click.echo(f"\nError during trading cycle: {e}", err=True)
        logger.error(f"Trading cycle error for {agent_id}: {e}")

    click.echo()


@agent.command()
@click.argument('agent_id')
def pause(agent_id):
    """Pauses an agent."""
    config = get_config()

    if not config.agent_exists(agent_id):
        click.echo(f"Error: Agent '{agent_id}' not found!", err=True)
        return

    agent_config = config.load_agent_config(agent_id)
    agent_config['agent']['status'] = 'paused'
    config.save_yaml(agent_config, str(config.get_agent_dir(agent_id) / 'context.yaml'))

    click.echo(f"✓ Agent '{agent_id}' paused.")


@agent.command()
@click.argument('agent_id')
def resume(agent_id):
    """Resumes an agent."""
    config = get_config()

    if not config.agent_exists(agent_id):
        click.echo(f"Error: Agent '{agent_id}' not found!", err=True)
        return

    agent_config = config.load_agent_config(agent_id)
    agent_config['agent']['status'] = 'active'
    config.save_yaml(agent_config, str(config.get_agent_dir(agent_id) / 'context.yaml'))

    click.echo(f"✓ Agent '{agent_id}' resumed.")


@agent.command()
@click.argument('agent_id')
@click.option('--capital', type=float, help='Update allocated capital')
def config(agent_id, capital):
    """Updates an agent's configuration."""
    cfg = get_config()

    if not cfg.agent_exists(agent_id):
        click.echo(f"Error: Agent '{agent_id}' not found!", err=True)
        return

    agent_config = cfg.load_agent_config(agent_id)

    if capital:
        agent_config['performance']['allocated_capital'] = capital
        agent_config['risk']['max_position_size'] = capital * 0.5
        cfg.save_yaml(agent_config, str(cfg.get_agent_dir(agent_id) / 'context.yaml'))
        click.echo(f"✓ Updated capital to ${capital:.2f}")


@agent.command()
@click.argument('agent_id')
@click.option('--days', default=30, help='Number of days to show')
def performance(agent_id, days):
    """Views an agent's performance."""
    config = get_config()

    if not config.agent_exists(agent_id):
        click.echo(f"Error: Agent '{agent_id}' not found!", err=True)
        return

    perf_data = config.load_json(str(config.get_agent_dir(agent_id) / 'performance.json'))

    click.echo(f"\n{'='*60}")
    click.echo(f"Performance: {agent_id}")
    click.echo(f"{'='*60}\n")

    click.echo(f"Total Trades: {perf_data.get('total_trades', 0)}")
    click.echo(f"Winning Trades: {perf_data.get('winning_trades', 0)}")
    click.echo(f"Losing Trades: {perf_data.get('losing_trades', 0)}")

    total = perf_data.get('total_trades', 0)
    if total > 0:
        win_rate = perf_data.get('winning_trades', 0) / total * 100
        click.echo(f"Win Rate: {win_rate:.1f}%")

    click.echo(f"Total P&L: ${perf_data.get('total_pnl', 0):.2f}\n")


@agent.command()
@click.argument('agent_id')
@click.confirmation_option(prompt='Are you sure you want to delete this agent?')
def delete(agent_id):
    """Deletes an agent."""
    config = get_config()

    if not config.agent_exists(agent_id):
        click.echo(f"Error: Agent '{agent_id}' not found!", err=True)
        return

    # Delete agent directory
    import shutil
    agent_dir = config.get_agent_dir(agent_id)
    shutil.rmtree(agent_dir)

    click.echo(f"✓ Agent '{agent_id}' deleted.")
