# pgc-uav-optimize

## Visão Geral

Projeto de pesquisa acadêmica (PGC - Projeto de Graduação em Computação) que implementa um
**Programa Linear Inteiro Misto (MILP)** para a otimização do plano de voo de VANTs na coleta de
dados de redes de sensores IoT. O objetivo é, simultaneamente, maximizar a Age of Information (AoI)
coletada e minimizar o consumo de energia do VANT ao longo de intervalos de tempo discretos.

O modelo de otimização é implementado em **Python** com o solver **Gurobi** (`gurobipy`). Os
experimentos são executados em múltiplos cenários que variam a quantidade de sensores e o tamanho do
mapa, e os resultados são plotados com matplotlib/pandas.

Idioma: predominantemente **português** (nomes de variáveis em inglês no código, comentários e
documentação em português).

---

## Arquitetura

```
pgc-uav-optimize/
├── main.py                          # Modelo MILP: construção, resolução, pós-processamento
├── plot_experiments_posicao.py      # Agrega e plota resultados (experimentos de posição)
├── plot_anafi.py                    # Agrega e plota resultados (Parrot Anafi USA)
├── plot_nn_comparison.py            # Comparação MILP vs heurísticas (NN, AoI-Greedy, Score-Greedy)
├── plot_revisit_comparison.py       # Comparação do modelo base com a variante com revisitas
├── heuristic_nn.py                  # Heurística Nearest Neighbor
├── heuristic_aoi_greedy.py          # Heurística AoI-Greedy
├── heuristic_score_greedy.py        # Heurística Score-Greedy (AoI/distância)
├── run_experiments.sh               # Roda 30 rodadas com o sensors.csv padrão
├── run_all_experiments.sh           # Roda todos os cenários (sensores x tamanhos de mapa)
├── requirements.txt                 # Dependências Python (fixadas)
├── setup/
│   ├── sensors.py                   # Dataclasses de domínio: Sensor, Base, NodesMap; leitor de CSV
│   ├── common.py                    # Constantes físicas, modelo de energia e I/O de AoI
│   ├── posicao/                     # Dados de experimentos: contagem_de_sensores/{sensors, resultados}
│   ├── bateria_50k/                 # Mesma estrutura, bateria = 50.000 J
│   ├── anafi_usa/                   # Mesma estrutura, parâmetros do Parrot Anafi USA
│   └── revisit/                     # Resultados da variante com revisitas
├── plots/                           # Gráficos de saída
└── text/                            # Documento da tese e apresentação (LaTeX)
    ├── main.tex                     # Tese
    ├── slides.tex                   # Apresentação (Beamer)
    └── figs/                        # Figuras
```

### Módulos principais

- **`setup/sensors.py`**: dataclasses `Sensor`, `Base`, `NodesMap`. Constrói a matriz de distâncias
  euclidianas.

- **`setup/common.py`**: parâmetros físicos do VANT, modelo de potência de asa rotativa
  (`compute_energy_cost`) e leitura/escrita do estado de AoI. `SLOT_DURATION` pode ser sobrescrito
  pela variável de ambiente `SLOT_DURATION` (padrão 10 s).

- **`main.py`**: toda a lógica do MILP em um único arquivo, organizada em seções:
  1. Parâmetros físicos do VANT (modelo de energia DJI Matrice 300 RTK)
  2. I/O do estado de AoI
  3. Construção dos dados do problema (horizonte temporal, custos de energia)
  4. Criação das variáveis de decisão
  5. Grupos de restrições (dinâmica de AoI, fluxo, energia, visita, linearização)
  6. Objetivo multiobjetivo (lexicográfico: maximizar AoI, depois minimizar energia)
  7. Resolução, pós-processamento e persistência dos resultados

---

## Variáveis de decisão

| Variável | Significado |
|----------|-------------|
| `p[n,t]` | Binária: VANT no nó `n` no slot `t` |
| `x[i,j,t]` | Binária: move de `i` para `j` no slot `t` |
| `E[t]` | Contínua: energia acumulada no slot `t` |
| `y[j]` | Binária: sensor `j` visitado ao menos uma vez |
| `v[j,t]` | Binária: coleta no sensor `j` no slot `t` (hover = self-loop `x[j,j,t]`) |
| `A[j,t]` | Contínua: AoI do sensor `j` no início do slot `t` |
| `w[j,t]` | Contínua: produto linearizado `A[j,t] * v[j,t]` (ganho de AoI) |

---

## Constantes principais (em `main.py`)

```python
SLOT_DURATION = 10.0     # segundos por slot
TIME_SLOTS    = 20       # slots discretos por rodada
BATTERY_MAX   = 50_000.0 # Joules (cenário com duas baterias TB60 usa 2_218_320 J)
```

Os parâmetros do modelo de potência correspondem ao DJI Matrice 300 RTK (modelo de asa rotativa de
Zeng et al.). Os parâmetros do Parrot Anafi USA são usados no conjunto de experimentos `anafi_usa`.

---

## Comandos

### Preparação

```bash
source venv/bin/activate
pip install -r requirements.txt
```

O Gurobi requer licença válida. O projeto usa `gurobipy==12.0.3`.

### Execução única (sensores padrão)

```bash
python main.py
```

### Execução única (cenário customizado)

```bash
python main.py \
  --sensors-csv  setup/posicao/5/sensors_100x100.csv \
  --aoi-state    /tmp/aoi_state.csv \
  --aoi-history  /tmp/aoi_history.csv \
  --round-summary /tmp/round_summary.csv
```

### Rodar todos os cenários

```bash
bash run_all_experiments.sh
```

Cenários são pulados automaticamente se `round_summary_*.csv` já tiver >= 30 linhas de dados.

### Gerar gráficos

```bash
python plot_experiments_posicao.py setup/posicao --output-dir plots
python plot_anafi.py setup/anafi_usa --output-dir text/figs
```

---

## Cenários de experimento

**Nomenclatura:** `P<n>-<L>`, onde `n` = número de sensores e `L` = lado do mapa (metros).

| Dimensão | Valores |
|----------|---------|
| Contagem de sensores | 5, 10, 15, 20, 25, 30 |
| Tamanhos de mapa | 100, 200, 400, 600, 800, 1000 (metros) |
| Rodadas por cenário | 30 |

Os dados de experimento ficam em `setup/posicao/<n>/`, `setup/bateria_50k/<n>/` e
`setup/anafi_usa/<n>/`. Cada pasta de cenário tem arquivos `sensors_<L>x<L>.csv` de entrada e um
diretório `resultados/` com `aoi_history_*.csv` e `round_summary_*.csv`.

---

## Arquivos de saída

| Arquivo | Colunas | Descrição |
|---------|---------|-----------|
| `aoi_state.csv` | `sensor_id, aoi` | Estado de AoI persistido entre rodadas |
| `aoi_history_*.csv` | `round, sensor_id, aoi_before, aoi_after, visited` | Log de AoI por sensor por rodada |
| `round_summary_*.csv` | `round, energy_final, collected_aoi, avg_final_aoi, visited_count, total_distance, path_taken` | Métricas agregadas por rodada |

---

## Notas técnicas

- Parâmetros do solver Gurobi: `TimeLimit=60s`, `MIPGap=1%`.
- A dinâmica de AoI usa restrições indicadoras (`addGenConstrIndicator`); apenas a linearização
  `w = A * v` usa Big-M.
- O VANT só coleta dados pairando (self-loop `x[j,j,t]`) sobre o nó; movimentos de trânsito não
  coletam.
- Cada sensor é visitado no máximo uma vez por rodada (no modelo base).

---

## Convenções de código

- Python 3.12, com type hints (`Dict`, `List`, `Tuple` de `typing`).
- Dataclasses para objetos de domínio (`Sensor`, `Base`, `NodesMap`).
- Funções de responsabilidade única, agrupadas por assunto dentro de `main.py`.
- Português em comentários, prints e colunas de CSV; inglês em nomes de variáveis/funções.
