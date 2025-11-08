# ADR-001: Asset-Based vs Task-Based Agent Architecture

**Date**: 2025-11-07
**Status**: Decided - Keeping asset-based architecture with hybrid optimization

## Context

After reviewing a comprehensive ChatGPT analysis of the system (comparing AI-powered vs traditional trading approaches), a proposal was made to reorganize agents by task (sentiment analysis, technical analysis, execution) instead of by asset (SPY, TSLA, AAPL).

## Proposal Evaluated

```
Task-Based Architecture:
- Agent #1: Sentiment analysis from financial news
- Agent #2: Technical analysis using traditional methods
- Agent #3: Execution/synthesis agent
```

## Analysis & Decision

The task-based architecture was **rejected** for the following reasons:

### 1. Increases Coordination Complexity
- Current: Zero inter-agent coordination, fully autonomous agents
- Proposed: Sequential pipeline (Sentiment → Technical → Execution)
- Creates single points of failure and complex state management
- **ChatGPT specifically warned**: "The complexity of orchestration and communication is a major challenge in agentic trading systems"

### 2. Worse Latency, Not Better
- Current: ~10 seconds (Data fetch + LLM decision)
- Proposed: ~15-20 seconds (Sentiment LLM + Technical + Execution LLM)
- Serial chains are slower than parallel operations
- Doesn't address the core concern about AI system speed

### 3. Loses Agent Specialization
- agent_aapl: Conservative, mean reversion, 1-hour timeframe
- agent_tsla: Aggressive, momentum, 15-minute timeframe
- Task-based dilutes personality and strategy specialization (a core strength)

### 4. State Management Nightmare
- Current: Clean per-agent ownership of positions and state
- Proposed: Shared state across multiple agents, unclear ownership
- Risk limits become ambiguous (who owns which positions?)

### 5. Doesn't Address Real Concerns from ChatGPT Analysis
- Latency: Task-based makes it worse (more sequential steps)
- Complexity: Task-based makes it worse (coordination overhead)
- Explainability: Only partially helps (TA transparent, but fusion still opaque)
- Cost: Marginal savings (fewer LLM calls but not significant)

## Adopted Solution: Hybrid Optimization Within Asset-Based Architecture

Instead of reorganizing, we implemented **internal optimizations** to each agent:

### 1. Created `cli/utils/technical_analyzer.py`
- Fast, deterministic TA calculations (RSI, SMA, trend, volume, support/resistance)
- Returns structured signals with confidence scores and reasoning
- Computation time: <10ms (vs seconds for LLM)
- Fully transparent and auditable

### 2. Updated agent execution flow (cli/commands/agent.py)
- Market data fetch → **Traditional TA signals** → LLM synthesis
- LLM receives pre-digested signals instead of raw numbers
- Smaller context, faster decisions, clearer reasoning

### 3. Added performance metrics
- Timing for: data fetch, TA computation, LLM decision
- Logged and displayed for every trade cycle
- Enables data-driven optimization

## Hybrid Pattern (Recommended Approach)

```python
# Traditional analysis (fast, deterministic)
technical_signals = {
    "rsi_oversold": rsi < 30,
    "macd_bullish": macd > signal,
    "above_sma": price > sma_20
}

# LLM only for synthesis and final decision
decision = llm_call({
    "technical_signals": technical_signals,  # Pre-computed
    "agent_personality": personality,
    "current_positions": positions
})
```

## Benefits of This Approach

- ✅ Speed: TA is instant (<10ms)
- ✅ Transparency: TA is deterministic and logged
- ✅ Lower cost: Smaller LLM prompts
- ✅ Still uses LLM for complex synthesis
- ✅ **No architectural changes needed**
- ✅ Preserves agent autonomy and specialization

## Focus Strategy: Single-Agent Mastery

Additionally, decided to **focus exclusively on agent_spy** before scaling:

1. **Rationale**: Running 3 agents simultaneously is premature
2. **Approach**: Perfect one agent (SPY) with proven performance before cloning
3. **Benefits**:
   - Better debugging and iteration
   - Clear performance attribution
   - Simpler mental model
   - SPY is liquid, well-understood, diversified (ETF)

## References

- ChatGPT analysis emphasized: "Day trading thrives on speed, simplicity, and predictability"
- This is an **AI research platform** exploring autonomous trading, not an HFT execution system
- Lean into research/learning aspects, don't try to compete on speed with traditional HFT

## Implementation Status

✅ Complete (2025-11-07)
- technical_analyzer.py created
- agent.py updated with hybrid approach
- Performance metrics added
- Ready to test with agent_spy
