#!/bin/bash
# Celery + Flower control script for Ztrade

set -e

WORKER_LOG="/tmp/celery_worker.log"
BEAT_LOG="/tmp/celery_beat.log"
FLOWER_LOG="/tmp/flower.log"

case "$1" in
    start)
        echo "🚀 Starting Celery infrastructure..."

        # Check if Redis is running
        if ! redis-cli ping > /dev/null 2>&1; then
            echo "📦 Starting Redis..."
            brew services start redis
            sleep 2
        else
            echo "✅ Redis already running"
        fi

        # Start Celery worker
        echo "👷 Starting Celery worker..."
        uv run celery -A celery_app worker --loglevel=info > "$WORKER_LOG" 2>&1 &
        WORKER_PID=$!
        echo "   Worker PID: $WORKER_PID (logs: $WORKER_LOG)"

        # Start Celery Beat (scheduler)
        echo "⏰ Starting Celery Beat (scheduler)..."
        uv run celery -A celery_app beat --loglevel=info > "$BEAT_LOG" 2>&1 &
        BEAT_PID=$!
        echo "   Beat PID: $BEAT_PID (logs: $BEAT_LOG)"

        # Start Flower (web UI)
        echo "🌸 Starting Flower web UI..."
        uv run celery -A celery_app flower --port=5555 > "$FLOWER_LOG" 2>&1 &
        FLOWER_PID=$!
        echo "   Flower PID: $FLOWER_PID (logs: $FLOWER_LOG)"

        sleep 3

        echo ""
        echo "✅ All services started!"
        echo ""
        echo "📊 Flower Web UI: http://localhost:5555"
        echo "📝 Worker logs: tail -f $WORKER_LOG"
        echo "⏰ Beat logs: tail -f $BEAT_LOG"
        echo "🌸 Flower logs: tail -f $FLOWER_LOG"
        echo ""
        echo "To stop all services: ./celery_control.sh stop"
        ;;

    stop)
        echo "🛑 Stopping Celery infrastructure..."

        # Kill all celery processes
        pkill -f "celery.*worker" || echo "   No worker found"
        pkill -f "celery.*beat" || echo "   No beat found"
        pkill -f "celery.*flower" || echo "   No flower found"

        echo "✅ All Celery processes stopped"
        echo ""
        echo "Note: Redis is still running. To stop:"
        echo "  brew services stop redis"
        ;;

    restart)
        echo "🔄 Restarting Celery infrastructure..."
        $0 stop
        sleep 2
        $0 start
        ;;

    status)
        echo "📊 Celery Infrastructure Status:"
        echo ""

        # Check Redis
        if redis-cli ping > /dev/null 2>&1; then
            echo "✅ Redis: RUNNING"
        else
            echo "❌ Redis: STOPPED"
        fi

        # Check Worker
        if pgrep -f "celery.*worker" > /dev/null; then
            echo "✅ Celery Worker: RUNNING (PID: $(pgrep -f 'celery.*worker'))"
        else
            echo "❌ Celery Worker: STOPPED"
        fi

        # Check Beat
        if pgrep -f "celery.*beat" > /dev/null; then
            echo "✅ Celery Beat: RUNNING (PID: $(pgrep -f 'celery.*beat'))"
        else
            echo "❌ Celery Beat: STOPPED"
        fi

        # Check Flower
        if pgrep -f "celery.*flower" > /dev/null; then
            echo "✅ Flower: RUNNING (PID: $(pgrep -f 'celery.*flower'))"
            echo "   URL: http://localhost:5555"
        else
            echo "❌ Flower: STOPPED"
        fi

        echo ""
        echo "Active tasks:"
        uv run celery -A celery_app inspect active 2>/dev/null || echo "   (No worker running)"
        ;;

    logs)
        case "$2" in
            worker)
                tail -f "$WORKER_LOG"
                ;;
            beat)
                tail -f "$BEAT_LOG"
                ;;
            flower)
                tail -f "$FLOWER_LOG"
                ;;
            *)
                echo "Usage: $0 logs [worker|beat|flower]"
                echo "Example: $0 logs worker"
                ;;
        esac
        ;;

    test)
        echo "🧪 Testing Celery setup..."
        uv run python3 -c "from celery_app import test_task; result = test_task.delay(); print(f'✅ Test task submitted: {result.id}')"
        echo ""
        echo "Check Flower UI to see the task: http://localhost:5555"
        ;;

    *)
        echo "Celery + Flower Control Script for Ztrade"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|test}"
        echo ""
        echo "Commands:"
        echo "  start   - Start Celery worker, beat, and Flower"
        echo "  stop    - Stop all Celery processes"
        echo "  restart - Restart all Celery processes"
        echo "  status  - Show status of all services"
        echo "  logs    - View logs (logs worker|beat|flower)"
        echo "  test    - Send a test task"
        echo ""
        echo "Quick links:"
        echo "  Flower UI: http://localhost:5555"
        echo "  Worker logs: $WORKER_LOG"
        echo "  Beat logs: $BEAT_LOG"
        echo "  Flower logs: $FLOWER_LOG"
        exit 1
        ;;
esac
