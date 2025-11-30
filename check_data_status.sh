#!/bin/bash
# Daily Data Accumulation Monitor
# Run this script daily to check paper trading data progress

echo "================================================================"
echo "📊 ZTRADE DATA ACCUMULATION STATUS"
echo "================================================================"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# Check if Airflow is running
echo "🔍 Airflow Status:"
docker-compose -f airflow/docker-compose.airflow.yml ps airflow-scheduler | grep -q "Up" && echo "  ✅ Scheduler: Running" || echo "  ❌ Scheduler: Stopped"
docker-compose -f airflow/docker-compose.airflow.yml ps airflow-webserver | grep -q "Up" && echo "  ✅ Webserver: Running" || echo "  ❌ Webserver: Stopped"
echo ""

# Check DAG runs in last 24 hours
echo "📈 DAG Activity (Last 24 Hours):"
docker exec airflow-airflow-scheduler-1 bash -c "
  tsla=\$(airflow dags list-runs -d agent_tsla_trading --no-backfill 2>/dev/null | grep success | wc -l)
  iwm=\$(airflow dags list-runs -d agent_iwm_trading --no-backfill 2>/dev/null | grep success | wc -l)
  btc=\$(airflow dags list-runs -d agent_btc_trading --no-backfill 2>/dev/null | grep success | wc -l)
  echo \"  TSLA: \$tsla successful runs\"
  echo \"  IWM:  \$iwm successful runs\"
  echo \"  BTC:  \$btc successful runs\"
" 2>/dev/null
echo ""

# Check database statistics
echo "💾 Database Statistics:"
docker exec airflow-airflow-scheduler-1 python -c "
from ztrade.core.database import get_db_connection
from datetime import datetime, timedelta

with get_db_connection() as conn:
    # Market bars
    cursor = conn.execute('''
        SELECT symbol, timeframe, COUNT(*) as bars,
               MIN(timestamp) as oldest, MAX(timestamp) as newest
        FROM market_bars
        GROUP BY symbol, timeframe
        ORDER BY symbol, timeframe
    ''')
    rows = cursor.fetchall()

    if rows:
        print('  Market Data:')
        total_bars = 0
        for row in rows:
            print(f'    {row[0]:6} {row[1]:4} {row[2]:5} bars  ({row[3][:10]} to {row[4][:10]})')
            total_bars += row[2]
        print(f'    Total: {total_bars:5} bars')
    else:
        print('  Market Data: No bars yet - will accumulate as DAGs run')

    print()

    # Sentiment history
    cursor = conn.execute('SELECT COUNT(*) FROM sentiment_history')
    sentiment_count = cursor.fetchone()[0]
    print(f'  Sentiment Records: {sentiment_count}')

    print()

    # Decision history
    cursor = conn.execute('''
        SELECT COUNT(*) as total,
               SUM(CASE WHEN decision = 'hold' THEN 1 ELSE 0 END) as holds,
               SUM(CASE WHEN decision = 'buy' THEN 1 ELSE 0 END) as buys,
               SUM(CASE WHEN decision = 'sell' THEN 1 ELSE 0 END) as sells
        FROM decision_history
    ''')
    dec_row = cursor.fetchone()
    print(f'  Decision History: {dec_row[0]} total decisions')
    if dec_row[0] > 0:
        print(f'    - HOLD: {dec_row[1]} ({dec_row[1]/dec_row[0]*100:.0f}%)')
        print(f'    - BUY:  {dec_row[2]} ({dec_row[2]/dec_row[0]*100:.0f}%)')
        print(f'    - SELL: {dec_row[3]} ({dec_row[3]/dec_row[0]*100:.0f}%)')

    print()

    # Calculate days of data and ETA
    if rows:
        print('  📊 Progress to Technical Analysis Activation:')
        for row in rows:
            symbol, timeframe, bars = row[0], row[1], row[2]

            # Calculate bars needed for technical analysis
            bars_needed = 100

            # Estimate bars per day
            bars_per_day = {
                '5m': 78,   # 6.5 hours * 12 bars/hour
                '15m': 26,  # 6.5 hours * 4 bars/hour
                '1h': 24    # 24/7 for crypto
            }.get(timeframe, 78)

            if bars >= bars_needed:
                print(f'    {symbol} {timeframe}: ✅ READY ({bars}/{bars_needed} bars)')
            else:
                days_of_data = bars / bars_per_day
                days_remaining = (bars_needed - bars) / bars_per_day
                pct_complete = (bars / bars_needed) * 100
                print(f'    {symbol} {timeframe}: {pct_complete:5.1f}% ({bars}/{bars_needed} bars) - {days_remaining:.1f} days to activation')
" 2>/dev/null
echo ""

# Show recent errors if any
echo "⚠️  Recent Issues (if any):"
docker exec airflow-airflow-scheduler-1 bash -c "
  failed_count=\$(airflow dags list-runs --state failed --no-backfill 2>/dev/null | wc -l)
  if [ \$failed_count -gt 1 ]; then
    echo \"  Found \$((failed_count - 1)) failed DAG run(s) in recent history\"
    echo \"  Check Airflow UI at http://localhost:8080 for details\"
  else
    echo \"  ✅ No recent failures\"
  fi
" 2>/dev/null
echo ""

echo "================================================================"
echo "💡 Quick Commands:"
echo "  View Airflow UI:  http://localhost:8080  (admin/admin)"
echo "  Check database:   docker exec airflow-airflow-scheduler-1 python -c 'from ztrade.core.database import get_db_connection; ...'"
echo "  Restart Airflow:  cd airflow && docker-compose -f docker-compose.airflow.yml restart"
echo "================================================================"
