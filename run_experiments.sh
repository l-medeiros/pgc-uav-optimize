#!/usr/bin/env bash

set -e

RUNS=30

echo "=============================="
echo "Running UAV experiments"
echo "Total runs: $RUNS"
echo "=============================="

START_TIME=$(date +%s)

for ((i=1; i<=RUNS; i++))
do
    echo ""
    echo "------------------------------"
    echo "Run $i / $RUNS"
    echo "------------------------------"

    python main.py

done

END_TIME=$(date +%s)

ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "=============================="
echo "Experiments finished"
echo "Total time: ${ELAPSED}s"
echo "==============================" 

rm /home/lucas/workspace/pgc/uav_optimize/setup/aoi_state.csv