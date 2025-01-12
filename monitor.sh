#!/bin/bash

echo "Monitoring server and client processes and ports (e.g. 3000, 5173)"
while true; do
    echo "==== Server and Client Ports ===="
    lsof -i :3000 -i :5173 | grep LISTEN || echo "No active processes"
    echo "==== Node Processes ===="
    ps aux | grep -E "(node.*3000|node.*5173)" | grep -v grep
    sleep 2
done
