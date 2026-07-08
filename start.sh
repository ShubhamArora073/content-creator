#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

echo "Fetching latest news..."
python fetch_news.py

echo ""
echo "Starting ADK Web UI at http://localhost:8000"
python -m google.adk.cli web --port 8000 .
