# Archived Agents

This directory contains trading agents that have been removed from active trading but preserved for historical reference and analysis.

## Archived Agents

### agent_spy (SPY - S&P 500 ETF)
**Archived**: 2025-11-13
**Reason**: No sentiment edge in mega-cap HFT-dominated markets

**Analysis**:
- HFT firms dominate 50-70% of SPY volume
- Sentiment priced in <1 second (our 5-minute analysis too slow)
- Competing against Renaissance, Citadel, Two Sigma with microsecond latency
- Academic research shows sentiment alpha ~0% for large-caps

**Replaced By**: agent_iwm (Russell 2000 small-caps with 20-30% sentiment alpha)

**Reference**: See ADR-009 for detailed analysis

---

### agent_aapl (Apple)
**Archived**: 2025-11-13
**Reason**: Limited sentiment edge in mega-cap market

**Analysis**:
- $3T market cap - most efficient stock market
- 50+ analysts covering every move
- Any news instantly priced by institutional algorithms
- Limited edge except on quarterly earnings (4x per year)

**Potential Future Use**: Earnings-only strategy (event-driven)

**Replaced By**: Focus on TSLA (proven), IWM (small-cap edge), BTC (crypto sentiment)

**Reference**: See ADR-009 for detailed analysis

---

## Why These Agents Were Removed

### Core Insight: Sentiment Alpha Inversely Correlates with Market Cap

| Market Cap | Example | Sentiment Edge | HFT Dominance | Our Competitive Position |
|------------|---------|---------------|---------------|------------------------|
| Mega-cap | SPY, AAPL | 0% | 70%+ | ❌ No edge |
| Large-cap | TSLA | 10-15% | 40-50% | ✅ Some edge (proven) |
| Small-cap | IWM | 20-30% | 10-20% | ✅ Strong edge |
| Crypto | BTC | 40-60% | 30% | ✅ Highest edge |

### Academic Support

**Tetlock (2007)**: "Media sentiment predicts returns in **small stocks** where arbitrage is costly."

**Da et al. (2015)**: "Investor attention strongly predicts **small-cap returns** but has little effect on large-caps."

**Market Microstructure**: Large-cap sentiment-to-price lag <1 second vs small-cap 15-60 minutes.

---

## Current Active Agents (Post-Archive)

1. **agent_tsla** - TSLA (proven winner, 91.2% win rate)
2. **agent_iwm** - IWM (small-cap sentiment edge)
3. **agent_btc** - BTC/USD (crypto sentiment edge, 24/7 trading)

**Strategy**: Trade where sentiment creates edge, avoid HFT-dominated markets.

---

## Restoring Archived Agents

If you want to restore an archived agent:

```bash
# Move back to active directory
mv agents/_archived/agent_spy agents/

# Update status in context.yaml
# status: archived → status: active

# Test in paper trading before live deployment
```

**Note**: Only restore if market microstructure changes or new edge identified.

---

**See Also**:
- ADR-009: Sentiment-Driven Asset Selection Strategy
- ADR-008: FinBERT for Financial Sentiment Analysis
