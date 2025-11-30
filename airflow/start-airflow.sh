#!/bin/bash
# Quick start script for Ztrade Airflow orchestration

set -e

echo "============================================"
echo "Ztrade Airflow Trading System"
echo "============================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo "Copying .env.airflow to .env..."
    cp .env.airflow .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys before starting!"
    echo ""
    echo "Required keys:"
    echo "  - ALPACA_API_KEY"
    echo "  - ALPACA_SECRET_KEY"
    echo "  - ALPHAVANTAGE_API_KEY"
    echo "  - COINGECKO_API_KEY"
    echo "  - REDDIT_CLIENT_ID"
    echo "  - REDDIT_CLIENT_SECRET"
    echo ""
    exit 1
fi

# Set AIRFLOW_UID
export AIRFLOW_UID=$(id -u)

echo "Starting Ztrade Airflow services..."
echo ""

# Start services
docker-compose -f docker-compose.airflow.yml up -d

echo ""
echo "✅ Airflow services starting..."
echo ""
echo "Waiting for initialization (this may take 60-90 seconds)..."
sleep 10

# Wait for webserver to be healthy
echo "Checking service health..."
for i in {1..30}; do
    if docker-compose -f docker-compose.airflow.yml ps | grep -q "airflow-webserver.*Up"; then
        echo "✅ Airflow webserver is up!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 3
done

echo ""
echo "============================================"
echo "Airflow UI Access"
echo "============================================"
echo "URL: http://localhost:8080"
echo "Username: admin"
echo "Password: admin"
echo ""
echo "============================================"
echo "Active Trading DAGs"
echo "============================================"
echo "1. agent_tsla_trading (TSLA, every 5 min)"
echo "2. agent_iwm_trading (IWM, every 15 min)"
echo "3. agent_btc_trading (BTC, every 1 hour, 24/7)"
echo ""
echo "Enable DAGs in the Airflow UI to start trading!"
echo ""
echo "============================================"
echo "Useful Commands"
echo "============================================"
echo "View logs:"
echo "  docker-compose -f docker-compose.airflow.yml logs -f"
echo ""
echo "Stop services:"
echo "  docker-compose -f docker-compose.airflow.yml down"
echo ""
echo "Restart services:"
echo "  docker-compose -f docker-compose.airflow.yml restart"
echo ""
echo "Access Airflow CLI:"
echo "  docker-compose -f docker-compose.airflow.yml exec airflow-webserver airflow"
echo ""
echo "============================================"
echo ""
