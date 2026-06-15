# Heurística Nearest Neighbor — Como Rodar

Baseline guloso para comparação com o MILP (`main.py`). A cada rodada, o VANT
parte da base e visita repetidamente o sensor não-visitado mais próximo do nó
atual, parando quando o orçamento de bateria (`BATTERY_MAX`) ou o número de
slots de tempo (`TIME_SLOTS`) se esgota. O estado de AoI é persistido entre
rodadas, igual ao MILP.

## Scripts

| Arquivo | Função |
|---------|--------|
| `heuristic_nn.py` | Executa **uma** rodada da heurística para um cenário |
| `run_nn_experiments.sh` | Executa **todos** os 36 cenários (6 contagens de sensor × 6 tamanhos de mapa) com 30 rodadas cada, sobre `setup/anafi_usa/` |

## Pré-requisitos

```bash
source venv/bin/activate          # ou use venv/bin/python diretamente
pip install -r requirements.txt   # apenas na primeira vez
```

A heurística NN **não** usa Gurobi — só `numpy`/stdlib — então roda sem licença.

## Rodar um único cenário (uma rodada)

```bash
python heuristic_nn.py \
  --sensors-csv   setup/anafi_usa/5/sensors_100x100.csv \
  --aoi-state     /tmp/aoi_state_nn.csv \
  --aoi-history   /tmp/aoi_history_nn.csv \
  --round-summary /tmp/round_summary_nn.csv
```

Cada execução avança **uma** rodada: lê o AoI de `--aoi-state`, simula o voo,
imprime o resumo e regrava o estado/histórico. Para simular N rodadas
encadeadas, chame o comando N vezes apontando para o mesmo `--aoi-state`.

| Argumento | Default | Descrição |
|-----------|---------|-----------|
| `--sensors-csv` | `DEFAULT_SENSORS_CSV` | CSV de sensores do cenário |
| `--aoi-state` | `setup/aoi_state_nn.csv` | Estado de AoI persistido entre rodadas |
| `--aoi-history` | `setup/aoi_history_nn.csv` | Log por sensor por rodada |
| `--round-summary` | `setup/round_summary_nn.csv` | Métricas agregadas por rodada |

## Rodar todos os cenários (36 × 30 rodadas)

```bash
bash run_nn_experiments.sh
```

O script:
- itera sobre `SENSOR_COUNTS=(5 10 15 20 25 30)` × `MAP_SIZES=(100 200 400 600 800 1000)`;
- grava em `setup/anafi_usa/<n>/resultados_nn/{aoi_history,round_summary}_<L>x<L>.csv`;
- usa um `aoi_state_*.tmp.csv` temporário por cenário, removido ao final;
- **pula** automaticamente cenários cujo `round_summary_*.csv` já tem ≥ 30 rodadas.

### Reexecutar do zero

Como o script pula cenários já completos, para refazer um cenário apague seus
resultados antes:

```bash
# um cenário específico
rm setup/anafi_usa/5/resultados_nn/round_summary_100x100.csv

# todos os resultados NN
rm -rf setup/anafi_usa/*/resultados_nn/
```

## Status atual

Os 36 cenários já estão completos (30 rodadas cada) em
`setup/anafi_usa/*/resultados_nn/`. Reexecutar `run_nn_experiments.sh` sem
apagar nada apenas reporta `[SKIP]` para todos.
