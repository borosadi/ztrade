#!/bin/bash

# Ztrade Dashboard Launch Script
# Starts the Streamlit dashboard on http://localhost:8501

echo "🚀 Starting Ztrade Dashboard..."
echo "📊 Dashboard will be available at: http://localhost:8501"
echo "⏹️  Press Ctrl+C to stop"
echo ""

uv run streamlit run dashboard.py
