# Manual Mode: Using Claude Code for Trading Decisions

If you don't have an Anthropic API key, you can use **Manual Mode** to leverage Claude Code (the AI assistant you're talking to right now) to make trading decisions for your agents.

## How It Works

1. Run an agent with the `--manual` flag
2. The system fetches market data and builds the decision context
3. The context is displayed to you
4. You copy the context and ask Claude Code to analyze it
5. Claude Code provides a JSON trading decision
6. You paste the decision back into the CLI
7. The system validates and executes the trade

## Usage

### Run Agent in Manual Mode

```bash
# Manual mode (uses Claude Code for decisions)
uv run ztrade agent run test_btc --manual

# Manual + dry-run (simulate without executing)
uv run ztrade agent run test_btc --manual --dry-run
```

### Workflow Example

1. **Start the trading cycle:**
   ```bash
   uv run ztrade agent run test_btc --manual --dry-run
   ```

2. **The CLI will display the decision context:**
   ```
   ======================================================================
   DECISION CONTEXT FOR CLAUDE CODE
   ======================================================================
   You are Test BTC Agent, an autonomous trading agent.

   Asset: BTC
   Current Price: $35,420.50
   Strategy: momentum
   Timeframe: 15m

   Your Personality and Approach:
   [Agent personality from personality.md]

   Current State:
   - Positions: 0
   - Daily P&L: $0.00
   - Trades Today: 0/5

   Risk Parameters:
   - Max Position Size: $5,000.00
   - Stop Loss: 2.0%
   - Min Confidence: 60%

   Based on the current market conditions and your trading strategy, make a decision.

   Respond with a JSON object in this format:
   {
       "action": "buy" | "sell" | "hold",
       "quantity": <number of shares, required for buy/sell>,
       "rationale": "<your reasoning>",
       "confidence": <0.0 to 1.0>,
       "stop_loss": <price level, required for buy>
   }
   ======================================================================
   ```

3. **Ask Claude Code to analyze it:**

   In Claude Code chat:
   ```
   Based on this agent context, what trading decision should be made?

   [Paste the entire context here]
   ```

4. **Claude Code will provide a JSON decision:**
   ```json
   {
       "action": "hold",
       "quantity": 0,
       "rationale": "BTC showing sideways consolidation with no clear momentum signal. Volume is declining and we're in the middle of the range. Best to wait for a clearer setup with either a breakout above resistance or support confirmation.",
       "confidence": 0.55
   }
   ```

5. **Paste the decision back into the CLI:**
   ```
   Paste the JSON decision below (or press Enter to cancel):
   Decision JSON: {"action": "hold", "quantity": 0, "rationale": "BTC showing sideways consolidation...", "confidence": 0.55}
   ```

6. **The system validates and executes:**
   ```
      Decision received: HOLD
      Confidence: 55%
   4. Validating against risk rules...
      ✓ Risk validation passed
   5. Simulating trade...

   ✓ DRY RUN: Would hold position
   ```

## Decision Format

Claude Code will provide decisions in this JSON format:

### Hold Decision
```json
{
    "action": "hold",
    "quantity": 0,
    "rationale": "No clear trading signal at current price levels",
    "confidence": 0.6
}
```

### Buy Decision
```json
{
    "action": "buy",
    "quantity": 100,
    "rationale": "Strong momentum breakout above resistance with high volume",
    "confidence": 0.85,
    "stop_loss": 34500.00
}
```

### Sell Decision
```json
{
    "action": "sell",
    "quantity": 100,
    "rationale": "Momentum weakening, taking profits at resistance",
    "confidence": 0.75
}
```

## Risk Validation

All decisions (whether from API or manual mode) go through the same risk validation:

- Agent must be active (or using --manual/--dry-run)
- Trade count must be within daily limit
- Position size must be within max allocation
- Stop loss must be present for buy orders
- Confidence must meet minimum threshold
- Daily P&L must be within loss limits

## Benefits of Manual Mode

1. **No API costs** - Use Claude Code instead of paying for Anthropic API
2. **Learning** - See exactly how trading decisions are made
3. **Oversight** - Full control over every trade
4. **Testing** - Perfect for testing strategies before automation
5. **Flexibility** - Can override or adjust decisions in real-time

## Combining with Dry-Run

For maximum safety while learning:

```bash
uv run ztrade agent run test_btc --manual --dry-run
```

This allows you to:
- Practice the workflow
- Test different strategies
- Validate risk rules
- See decision logging
- All without executing real trades or using API credits

## Transition to Automated Mode

Once you're comfortable and have an API key:

```bash
# Fully automated (requires ANTHROPIC_API_KEY)
uv run ztrade agent run test_btc

# Automated with safety net
uv run ztrade agent run test_btc --dry-run
```

## Tips

- **Start with dry-run**: Always test in dry-run mode first
- **Review personality**: Make sure `agents/<agent_id>/personality.md` reflects your strategy
- **Monitor risk**: Use `ztrade risk status` to check risk metrics
- **Check logs**: Use `ztrade monitor decisions <agent_id>` to review past decisions
- **Ask Claude Code**: You can ask me to explain the reasoning behind any decision

## Example Session

```bash
# 1. Check agent status
uv run ztrade agent status test_btc

# 2. Run manual trading cycle
uv run ztrade agent run test_btc --manual --dry-run

# 3. [Copy context, ask Claude Code, paste decision]

# 4. Review the decision log
uv run ztrade monitor decisions test_btc

# 5. Check risk status
uv run ztrade risk status
```

## Questions?

Just ask me (Claude Code) if you need help with:
- Analyzing market context
- Making trading decisions
- Understanding risk parameters
- Troubleshooting the workflow
