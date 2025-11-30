# Airflow DAG Inventory

**Last Updated**: 2025-11-30

This document provides a comprehensive inventory of all Airflow DAGs in the Ztrade system.

---

## Overview

- **Total DAGs**: 13
- **Stock DAGs**: 7 (market hours only)
- **Crypto DAGs**: 6 (24/7 trading)
- **All DAGs**: Sentiment-Momentum strategy with algorithmic decision-making

---

## Stock DAGs (7)

Trade during market hours only: **Monday-Friday, 9:30 AM - 4:00 PM EST**

### 1. agent_tsla_trading
- **Asset**: TSLA (Tesla)
- **Timeframe**: 5 minutes
- **Schedule**: Every 5 minutes during market hours
- **Cron**: `*/5 14-20 * * 1-5` (9 AM-4 PM EST = 14-21 UTC)
- **Status**: ✅ Validated (91.2% win rate in backtest)
- **Sentiment Focus**: EV sector, Elon Musk narratives, tech innovation
- **DAG File**: `airflow/dags/agent_tsla_dag.py`

### 2. agent_iwm_trading
- **Asset**: IWM (Russell 2000 ETF)
- **Timeframe**: 15 minutes
- **Schedule**: Every 15 minutes during market hours
- **Cron**: `*/15 14-20 * * 1-5`
- **Status**: 🆕 Ready for backtesting
- **Sentiment Focus**: Small-cap sentiment, economic narratives, retail trading
- **DAG File**: `airflow/dags/agent_iwm_dag.py`

### 3. agent_pltr_trading
- **Asset**: PLTR (Palantir)
- **Timeframe**: 15 minutes
- **Schedule**: Every 15 minutes during market hours
- **Cron**: `*/15 14-20 * * 1-5`
- **Status**: 🆕 Ready for backtesting
- **Sentiment Focus**: AI narratives, defense contracts, data analytics
- **DAG File**: `airflow/dags/agent_pltr_dag.py`

### 4. agent_roku_trading
- **Asset**: ROKU (Roku)
- **Timeframe**: 15 minutes
- **Schedule**: Every 15 minutes during market hours
- **Cron**: `*/15 14-20 * * 1-5`
- **Status**: 🆕 Ready for backtesting
- **Sentiment Focus**: Streaming sector, cord-cutting trends, content deals
- **DAG File**: `airflow/dags/agent_roku_dag.py`

### 5. agent_net_trading
- **Asset**: NET (Cloudflare)
- **Timeframe**: 15 minutes
- **Schedule**: Every 15 minutes during market hours
- **Cron**: `*/15 14-20 * * 1-5`
- **Status**: 🆕 Ready for backtesting
- **Sentiment Focus**: Cloud infrastructure, cybersecurity, edge computing
- **DAG File**: `airflow/dags/agent_net_dag.py`

### 6. agent_snap_trading
- **Asset**: SNAP (Snapchat)
- **Timeframe**: 15 minutes
- **Schedule**: Every 15 minutes during market hours
- **Cron**: `*/15 14-20 * * 1-5`
- **Status**: 🆕 Ready for backtesting
- **Sentiment Focus**: Social media trends, AR/VR narratives, youth demographics
- **DAG File**: `airflow/dags/agent_snap_dag.py`

### 7. agent_ddog_trading
- **Asset**: DDOG (Datadog)
- **Timeframe**: 15 minutes
- **Schedule**: Every 15 minutes during market hours
- **Cron**: `*/15 14-20 * * 1-5`
- **Status**: 🆕 Ready for backtesting
- **Sentiment Focus**: DevOps, observability, cloud monitoring, SaaS growth
- **DAG File**: `airflow/dags/agent_ddog_dag.py`

---

## Crypto DAGs (6)

Trade 24/7: **Every hour, all day, every day**

### 8. agent_btc_trading
- **Asset**: BTC/USD (Bitcoin)
- **Timeframe**: 1 hour
- **Schedule**: Every hour, 24/7
- **Cron**: `0 */60 * * *`
- **Status**: 🆕 Ready for backtesting
- **Sentiment Focus**: Flagship crypto, institutional adoption, macro trends
- **Expected Sentiment Alpha**: 40-60%
- **DAG File**: `airflow/dags/agent_btc_dag.py`

### 9. agent_eth_trading
- **Asset**: ETH/USD (Ethereum)
- **Timeframe**: 1 hour
- **Schedule**: Every hour, 24/7
- **Cron**: `0 */60 * * *`
- **Status**: 🆕 Ready for backtesting
- **Sentiment Focus**: DeFi ecosystem, ETH 2.0, smart contracts, gas fees
- **DAG File**: `airflow/dags/agent_eth_dag.py`

### 10. agent_sol_trading
- **Asset**: SOL/USD (Solana)
- **Timeframe**: 1 hour
- **Schedule**: Every hour, 24/7
- **Cron**: `0 */60 * * *`
- **Status**: 🆕 Ready for backtesting
- **Sentiment Focus**: NFT ecosystem, high-speed blockchain, ecosystem growth
- **DAG File**: `airflow/dags/agent_sol_dag.py`

### 11. agent_doge_trading
- **Asset**: DOGE/USD (Dogecoin)
- **Timeframe**: 1 hour
- **Schedule**: Every hour, 24/7
- **Cron**: `0 */60 * * *`
- **Status**: 🆕 Ready for backtesting
- **Sentiment Focus**: Meme coin, Elon Musk tweets, community sentiment
- **DAG File**: `airflow/dags/agent_doge_dag.py`

### 12. agent_shib_trading
- **Asset**: SHIB/USD (Shiba Inu)
- **Timeframe**: 1 hour
- **Schedule**: Every hour, 24/7
- **Cron**: `0 */60 * * *`
- **Status**: 🆕 Ready for backtesting
- **Sentiment Focus**: Meme coin, Shib Army community, burn events, ecosystem
- **DAG File**: `airflow/dags/agent_shib_dag.py`

### 13. agent_xrp_trading
- **Asset**: XRP/USD (Ripple)
- **Timeframe**: 1 hour
- **Schedule**: Every hour, 24/7
- **Cron**: `0 */60 * * *`
- **Status**: 🆕 Ready for backtesting
- **Sentiment Focus**: Regulatory developments, SEC lawsuit, banking partnerships
- **DAG File**: `airflow/dags/agent_xrp_dag.py`

---

## DAG Architecture

All DAGs follow the same 7-task pipeline:

1. **check_market_hours** - Verify market is open (stocks only; crypto always open)
2. **fetch_market_data** - Fetch current quote and bars, save to database
3. **analyze_sentiment** - Multi-source sentiment analysis (News + Reddit + SEC)
4. **analyze_technical** - Technical analysis (RSI, SMA, trend, volume)
5. **make_decision** - Algorithmic decision (60% sentiment + 40% technical)
6. **validate_risk** - Validate against risk rules
7. **execute_trade** - Execute trade if approved (or skip if HOLD)
8. **log_performance** - Log metrics to database

### Task Dependencies
```
check_market_hours >> fetch_market_data
fetch_market_data >> [analyze_sentiment, analyze_technical]
[analyze_sentiment, analyze_technical] >> make_decision
make_decision >> validate_risk >> execute_trade >> log_performance
```

---

## DAG Configuration

### Common Settings (All DAGs)

```python
default_args = {
    'owner': 'ztrade',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(seconds=30),
}

# DAG settings
catchup=False          # Don't backfill missed runs
max_active_runs=1      # Only one instance at a time
```

### Decision Algorithm

All agents use the same algorithmic decision maker:
- **Sentiment Weight**: 60%
- **Technical Weight**: 40%
- **Threshold**: Minimum 50% confidence to act

### Risk Management

All trades validated against:
- Position size limits
- Daily loss limits
- Stop loss requirements
- Capital allocation limits
- Correlation limits

---

## Portfolio Allocation

**Target Portfolio**: $130,000 total
- **Per Agent**: $10,000
- **Stock Agents**: 7 × $10,000 = $70,000
- **Crypto Agents**: 6 × $10,000 = $60,000

**Diversification**:
- Sector diversification (tech, streaming, cloud, social, DeFi, meme)
- Market-hours vs 24/7 trading split
- Mix of volatility profiles (stable vs volatile)

---

## Management Commands

### List All DAGs
```bash
docker exec airflow-airflow-scheduler-1 airflow dags list
```

### Trigger Specific DAG
```bash
docker exec airflow-airflow-scheduler-1 airflow dags trigger agent_tsla_trading
```

### Pause/Unpause All DAGs
```bash
# Pause all
docker exec airflow-airflow-scheduler-1 airflow dags pause agent_tsla_trading
docker exec airflow-airflow-scheduler-1 airflow dags pause agent_iwm_trading
# ... (repeat for all 13 DAGs)

# Unpause all
docker exec airflow-airflow-scheduler-1 airflow dags unpause agent_tsla_trading
# ... (repeat for all 13 DAGs)
```

### Check DAG Status
```bash
docker exec airflow-airflow-scheduler-1 airflow dags list-runs -d agent_tsla_trading
```

### Check for Import Errors
```bash
docker exec airflow-airflow-scheduler-1 airflow dags list-import-errors
```

---

## Next Steps

1. **Backfill Historical Data**:
   - Stocks: 60 days of 5-min and 15-min bars
   - Crypto: 90 days of 1-hour bars

2. **Backtest All Agents**:
   - Validate sentiment alpha hypothesis for each agent
   - Compare performance across asset classes

3. **Monitor in Production**:
   - Track all 13 DAGs in Airflow UI
   - Monitor sentiment performance
   - Analyze correlation between agents

4. **Optimize**:
   - Tune sentiment/technical weights per agent
   - Adjust position sizing based on volatility
   - Implement dynamic capital allocation

---

## References

- [CLAUDE.md](../CLAUDE.md) - Main project documentation
- [Airflow Operations Guide](guides/airflow-operations.md) - Detailed Airflow guide
- [ADR-010: Airflow Orchestration](adr/ADR-010-airflow-orchestration.md) - Architecture decision
