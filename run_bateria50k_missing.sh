#!/usr/bin/env bash
# Roda os cenários faltantes do experimento bateria_50k (BATTERY_MAX = 50_000 J).
# Troca o valor em setup/common.py antes de iniciar e restaura ao sair.

set -e

REPO="$(dirname "$0")"
COMMON="$REPO/setup/common.py"
PYTHON="$REPO/venv/bin/python"
BASE_DIR="$REPO/setup/bateria_50k"
RUNS=30

SENSOR_COUNTS=(20 25 30)
MAP_SIZES=(100 200 400 600 800 1000)

# --- troca e restauração de BATTERY_MAX ---
swap_battery() {
    sed -i \
        -e 's|^BATTERY_MAX = 141_372\.0.*|# BATTERY_MAX = 141_372.0 # (PARROT ANAFI USA)|' \
        -e 's|^# BATTERY_MAX = 50_000\.0|BATTERY_MAX = 50_000.0|' \
        "$COMMON"
}

restore_battery() {
    sed -i \
        -e 's|^# BATTERY_MAX = 141_372\.0.*|BATTERY_MAX = 141_372.0 # (PARROT ANAFI USA)|' \
        -e 's|^BATTERY_MAX = 50_000\.0|# BATTERY_MAX = 50_000.0|' \
        "$COMMON"
    echo "[INFO] BATTERY_MAX restaurado para 141_372.0"
}

trap restore_battery EXIT

echo "=============================="
echo "UAV Experiments — bateria_50k (missing)"
echo "BATTERY_MAX = 50_000 J"
echo "=============================="

swap_battery
echo "[INFO] BATTERY_MAX definido para 50_000.0"

DONE=0
SKIPPED=0

for n in "${SENSOR_COUNTS[@]}"; do
    for L in "${MAP_SIZES[@]}"; do

        SENSORS_CSV="$BASE_DIR/$n/sensors_${L}x${L}.csv"
        RESULTADOS_DIR="$BASE_DIR/$n/resultados"
        AOI_STATE="$BASE_DIR/$n/aoi_state_${L}x${L}.tmp.csv"
        AOI_HISTORY="$RESULTADOS_DIR/aoi_history_${L}x${L}.csv"
        ROUND_SUMMARY="$RESULTADOS_DIR/round_summary_${L}x${L}.csv"

        if [ -f "$ROUND_SUMMARY" ]; then
            EXISTING=$(( $(wc -l < "$ROUND_SUMMARY") - 1 ))
            if [ "$EXISTING" -ge "$RUNS" ]; then
                echo "[SKIP] B${n}-${L}: já tem $EXISTING rodadas"
                SKIPPED=$(( SKIPPED + 1 ))
                continue
            fi
        fi

        mkdir -p "$RESULTADOS_DIR"
        rm -f "$AOI_STATE"

        echo ""
        echo "------------------------------"
        echo "[RUN] B${n}-${L} ($n sensores, ${L}x${L} m)"
        echo "------------------------------"

        START=$(date +%s)

        for ((i=1; i<=RUNS; i++)); do
            echo "  Rodada $i / $RUNS"
            "$PYTHON" "$REPO/main.py" \
                --sensors-csv   "$SENSORS_CSV" \
                --aoi-state     "$AOI_STATE" \
                --aoi-history   "$AOI_HISTORY" \
                --round-summary "$ROUND_SUMMARY"
        done

        rm -f "$AOI_STATE"

        END=$(date +%s)
        echo "[OK] B${n}-${L} concluído em $(( END - START ))s"
        DONE=$(( DONE + 1 ))

    done
done

echo ""
echo "=============================="
echo "Concluído!"
echo "Executados: $DONE | Pulados: $SKIPPED"
echo "=============================="
