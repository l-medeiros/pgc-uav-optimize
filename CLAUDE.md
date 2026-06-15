# pgc-uav-optimize

## Project Overview

Academic research project (PGC - Projeto de Graduacao em Computacao) implementing a **Mixed Integer Linear Program (MILP)** for UAV flight plan optimization in IoT sensor data collection networks. The goal is to simultaneously maximize Age of Information (AoI) collected and minimize UAV energy consumption across discrete time slots.

The optimization model is implemented in **Python** using the **Gurobi** solver (`gurobipy`). Experiments are run across multiple scenarios varying sensor count and map size, and results are plotted with matplotlib/pandas.

Language: predominantly **Portuguese** (variable names in English in code, comments and docs in Portuguese).

---

## Architecture

```
pgc-uav-optimize/
├── main.py                          # MILP model: build, solve, post-process
├── plot_experiments_posicao.py      # Aggregate + plot results (posicao experiments)
├── plot_anafi.py                    # Aggregate + plot results (Parrot Anafi USA experiments)
├── run_experiments.sh               # Run 30 rounds with default sensors.csv
├── run_all_experiments.sh           # Run all scenarios (sensor counts x map sizes), battery 50k
├── requirements.txt                 # Python dependencies (pinned)
├── venv/                            # Python virtualenv
├── setup/
│   ├── sensors.py                   # Domain dataclasses: Sensor, Base, NodesMap; CSV reader
│   ├── sensors.csv                  # Default sensors file (ad-hoc layout, 10 sensors)
│   ├── posicao/                     # Experiment data: sensor_count/{sensors, resultados}
│   │   └── <n>/                     # n in {5, 10, 15, 20, 25, 30}
│   │       ├── sensors_<L>x<L>.csv  # L in {100, 200, 400, 600, 800, 1000}
│   │       └── resultados/          # aoi_history_*.csv, round_summary_*.csv
│   ├── bateria_50k/                 # Same structure, battery cap = 50,000 J
│   ├── anafi_usa/                   # Same structure, Parrot Anafi USA parameters
│   ├── aoi_state.csv                # Persistent AoI state between rounds (default)
│   └── cenários.txt                 # Scenario naming convention
├── plots/                           # Output plots from plot_experiments_posicao.py
└── text/                            # LaTeX thesis document
    ├── main.tex
    ├── introdução.tex, metodologia.tex, objetivos.tex, trabalhos_relacionados.tex
    └── figs/                        # Plots for the thesis (from plot_anafi.py)
```

### Key Modules

- **`setup/sensors.py`**: Frozen dataclasses `Sensor`, `Base`, `NodesMap`. Builds full Euclidean distance matrix. `DEFAULT_SENSORS_CSV` path is hardcoded for the original dev machine (must be overridden via `--sensors-csv`).

- **`main.py`**: All MILP logic in a single file, organized into clear functional sections:
  1. Physical UAV parameters (DJI Matrice 300 RTK energy model)
  2. AoI state I/O (load/save CSV)
  3. Problem data construction (time horizon, energy costs)
  4. Decision variable creation
  5. Constraint groups (AoI dynamics, flow, energy, visit, linearization)
  6. Multi-objective definition (lexicographic: maximize AoI priority 2, minimize energy priority 1)
  7. Solve + post-process + persist results

---

## Decision Variables

| Variable | Meaning |
|----------|---------|
| `p[n,t]` | Binary: UAV at node `n` at slot `t` |
| `x[i,j,t]` | Binary: move from `i` to `j` at slot `t` |
| `E[t]` | Continuous: cumulative energy at slot `t` |
| `y[j]` | Binary: sensor `j` visited at least once |
| `v[j,t]` | Binary: data collected at sensor `j` at slot `t` (hover = self-loop `x[j,j,t]`) |
| `A[j,t]` | Continuous: AoI of sensor `j` at start of slot `t` |
| `w[j,t]` | Continuous: linearized product `A[j,t] * v[j,t]` (AoI gain) |

---

## Key Constants (in `main.py`)

```python
SLOT_DURATION = 10.0     # seconds per time slot
TIME_SLOTS    = 20       # total discrete slots per round
BATTERY_MAX   = 50_000.0 # Joules (two TB60 batteries scenario uses 2_218_320 J)
```

UAV power model parameters correspond to DJI Matrice 300 RTK (Zeng/Mu rotary-wing model). Parrot Anafi USA parameters are used in the `anafi_usa` experiment set.

---

## Run Commands

### Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies (first time)
pip install -r requirements.txt
```

Gurobi requires a valid license. The project uses `gurobipy==12.0.3`.

### Single Run (default sensors)

```bash
python main.py
```

### Single Run (custom scenario)

```bash
python main.py \
  --sensors-csv  setup/posicao/5/sensors_100x100.csv \
  --aoi-state    /tmp/aoi_state.csv \
  --aoi-history  /tmp/aoi_history.csv \
  --round-summary /tmp/round_summary.csv
```

### Run 30 rounds with default sensors

```bash
bash run_experiments.sh
```

### Run all scenarios (6 sensor counts x 6 map sizes = 36 scenarios, 30 rounds each)

```bash
bash run_all_experiments.sh
```

Scenarios are skipped automatically if `round_summary_*.csv` already has >= 30 data rows.

### Generate plots

```bash
# posicao experiments
python plot_experiments_posicao.py setup/posicao --output-dir plots

# Anafi USA experiments
python plot_anafi.py setup/anafi_usa --output-dir text/figs
```

---

## Experiment Scenarios

**Scenario naming:** `P<n>-<L>` where `n` = sensor count, `L` = map side length (meters).

| Dimension | Values |
|-----------|--------|
| Sensor counts | 5, 10, 15, 20, 25, 30 |
| Map sizes | 100, 200, 400, 600, 800, 1000 (meters) |
| Rounds per scenario | 30 |

Experiment data lives under:
- `setup/posicao/<n>/` — position-based experiments
- `setup/bateria_50k/<n>/` — battery-limited (50k J) experiments
- `setup/anafi_usa/<n>/` — Parrot Anafi USA UAV experiments

Each scenario folder has `sensors_<L>x<L>.csv` input files and a `resultados/` output directory containing `aoi_history_*.csv` and `round_summary_*.csv`.

---

## Output Files

| File | Columns | Description |
|------|---------|-------------|
| `aoi_state.csv` | `sensor_id, aoi` | Persistent AoI state between rounds |
| `aoi_history_*.csv` | `round, sensor_id, aoi_before, aoi_after, visited` | Per-sensor per-round AoI log |
| `round_summary_*.csv` | `round, energy_final, collected_aoi, avg_final_aoi, visited_count, total_distance, path_taken` | Per-round aggregated metrics |

---

## Known Issues / Technical Notes

- **Hardcoded paths**: `setup/sensors.py` has `DEFAULT_SENSORS_CSV` and `main.py` has `AOI_STATE_PATH`, `AOI_HISTORY_PATH`, `ROUND_SUMMARY_PATH` pointing to the original developer's machine (`/home/lucas/workspace/pgc/...`). Always override via CLI arguments.
- **`run_experiments.sh`** also has a hardcoded `rm` path at the end pointing to `/home/lucas/...`.
- Gurobi solver parameters: `TimeLimit=60s`, `MIPGap=1%`.
- AoI dynamics use Gurobi's `addGenConstrIndicator` (indicator constraints), not Big-M for the dynamics branch — only the `w = A * v` linearization uses Big-M.
- The UAV is only allowed to hover (self-loop `x[j,j,t]`) at a sensor node to collect data; transit moves do not collect.
- Each sensor can be visited at most once per round.

---

## Coding Conventions

- Python 3.12, type hints throughout (`Dict`, `List`, `Tuple` from `typing`)
- Dataclasses used for domain objects (`Sensor`, `Base`, `NodesMap`)
- Functions are single-responsibility, grouped by concern within `main.py`
- No test suite present
- Portuguese is used for comments, print statements, CSV column names, and thesis text
- English is used for variable/function/parameter names in code
