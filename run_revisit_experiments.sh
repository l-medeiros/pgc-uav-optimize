#!/usr/bin/env bash

set -e

# Sensores reutilizados do conjunto anafi_usa (mesmas posições, comparação justa)
SENSORS_DIR="$(dirname "$0")/setup/anafi_usa"
RESULTS_DIR="$(dirname "$0")/setup/revisit"
RUNS=30

SENSOR_COUNTS=(5 10 15 20 25 30)
MAP_SIZES=(100 200 400 600 800 1000)

TOTAL=$(( ${#SENSOR_COUNTS[@]} * ${#MAP_SIZES[@]} ))
DONE=0
SKIPPED=0

echo "=============================="
echo "UAV Experiments — revisit"
echo "Cenários: $TOTAL | Rodadas por cenário: $RUNS"
echo "=============================="

for n in "${SENSOR_COUNTS[@]}"; do
    for L in "${MAP_SIZES[@]}"; do

        SENSORS_CSV="$SENSORS_DIR/$n/sensors_${L}x${L}.csv"
        RESULTADOS_DIR="$RESULTS_DIR/$n/resultados"
        AOI_STATE="$RESULTS_DIR/$n/aoi_state_${L}x${L}.tmp.csv"
        AOI_HISTORY="$RESULTADOS_DIR/aoi_history_${L}x${L}.csv"
        ROUND_SUMMARY="$RESULTADOS_DIR/round_summary_${L}x${L}.csv"

        # Verifica se cenário já foi concluído (30 linhas de dados = 31 linhas com header)
        if [ -f "$ROUND_SUMMARY" ]; then
            EXISTING=$(( $(wc -l < "$ROUND_SUMMARY") - 1 ))
            if [ "$EXISTING" -ge "$RUNS" ]; then
                echo "[SKIP] P${n}-${L}: já tem $EXISTING rodadas"
                SKIPPED=$(( SKIPPED + 1 ))
                continue
            fi
        fi

        if [ ! -f "$SENSORS_CSV" ]; then
            echo "[WARN] Arquivo de sensores não encontrado, pulando: $SENSORS_CSV"
            continue
        fi

        mkdir -p "$RESULTADOS_DIR"
        rm -f "$AOI_STATE"

        echo ""
        echo "------------------------------"
        echo "[RUN] P${n}-${L} ($n sensores, ${L}x${L} m)"
        echo "------------------------------"

        START=$(date +%s)

        for ((i=1; i<=RUNS; i++)); do
            echo "  Rodada $i / $RUNS"
            python main.py \
                --sensors-csv   "$SENSORS_CSV" \
                --aoi-state     "$AOI_STATE" \
                --aoi-history   "$AOI_HISTORY" \
                --round-summary "$ROUND_SUMMARY" \
                --allow-revisit \
                --max-revisits  3
        done

        rm -f "$AOI_STATE"

        END=$(date +%s)
        echo "[OK] P${n}-${L} concluído em $(( END - START ))s"
        DONE=$(( DONE + 1 ))

    done
done

echo ""
echo "=============================="
echo "Concluído!"
echo "Executados: $DONE | Pulados: $SKIPPED"
echo "=============================="
