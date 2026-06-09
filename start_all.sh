#!/bin/bash
set -e

# Start all Legal Multi-Agent System services
# Registry must be first, then leaf agents, then orchestrators

cd "$(dirname "$0")"

PORTS=(10000 10102 10103 10101 10100)

if command -v uv >/dev/null 2>&1; then
  PYTHON="uv run python"
elif [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  echo "ERROR: No Python found. Install uv (https://docs.astral.sh/uv/) or create a .venv."
  exit 1
fi

stop_existing_services() {
  local found=false
  for port in "${PORTS[@]}"; do
    local pids
    pids=$(lsof -ti :"$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
      found=true
      echo "Stopping existing process on port $port..."
      echo "$pids" | xargs kill -9 2>/dev/null || true
    fi
  done
  if [ "$found" = true ]; then
    sleep 1
  fi
}

wait_for_port() {
  local port=$1
  local name=$2
  local i
  for i in $(seq 1 10); do
    if lsof -ti :"$port" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  echo "ERROR: $name failed to start on port $port"
  exit 1
}

stop_existing_services

echo "Using: $PYTHON"
echo "Starting Registry service on port 10000..."
$PYTHON -m registry &
REGISTRY_PID=$!
wait_for_port 10000 "Registry"

echo "Starting Tax Agent on port 10102..."
$PYTHON -m tax_agent &
TAX_PID=$!

echo "Starting Compliance Agent on port 10103..."
$PYTHON -m compliance_agent &
COMPLIANCE_PID=$!
sleep 2
wait_for_port 10102 "Tax Agent"
wait_for_port 10103 "Compliance Agent"

echo "Starting Law Agent on port 10101..."
$PYTHON -m law_agent &
LAW_PID=$!
sleep 2
wait_for_port 10101 "Law Agent"

echo "Starting Customer Agent on port 10100..."
$PYTHON -m customer_agent &
CUSTOMER_PID=$!
sleep 2
wait_for_port 10100 "Customer Agent"

echo ""
echo "All services started:"
echo "  Registry:         http://localhost:10000"
echo "  Customer Agent:   http://localhost:10100"
echo "  Law Agent:        http://localhost:10101"
echo "  Tax Agent:        http://localhost:10102"
echo "  Compliance Agent: http://localhost:10103"
echo ""
echo "Run test_client.py to send a query:"
echo "  uv run python test_client.py"
echo ""
echo "To stop all services: ./stop_all.sh  (or Ctrl+C in this terminal)"
echo ""

# Wait for all background processes
wait $REGISTRY_PID $TAX_PID $COMPLIANCE_PID $LAW_PID $CUSTOMER_PID
