#!/bin/bash

# Stop all Legal Multi-Agent System services

PORTS=(10000 10100 10101 10102 10103)
stopped=false

for port in "${PORTS[@]}"; do
  pids=$(lsof -ti :"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    stopped=true
    echo "Stopping process on port $port..."
    echo "$pids" | xargs kill -9 2>/dev/null || true
  fi
done

if [ "$stopped" = true ]; then
  echo "All services stopped."
else
  echo "No services were running on ports ${PORTS[*]}."
fi
