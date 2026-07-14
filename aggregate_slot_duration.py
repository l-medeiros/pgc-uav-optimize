import csv
import os
from statistics import mean
from typing import Dict, List

import setup.common as common

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(ROOT, "setup", "slot_duration")
OUT_MD = os.path.join(ROOT, "text", "comparacao_slot_duration_rascunho.md")

SLOT_DURATIONS = [10, 20, 30, 40, 50]
SENSOR_COUNTS = [50, 100, 200]
MAP_SIZES = [600, 800, 1000, 2000, 4000]
HEURS = [("aoi_greedy", "AoI-Greedy"), ("score_greedy", "Score-Greedy"), ("nn", "NN")]
BAT = common.BATTERY_MAX
P0 = common.uav_power_rotary(0.0)
TRANSITIONS = common.TIME_SLOTS - 1
CEILING = BAT / (TRANSITIONS * P0)


def load(key, dt, n, L, metric) -> float:
    path = os.path.join(BASE_DIR, str(n), f"resultados_{key}_dt{dt}", f"round_summary_{L}x{L}.csv")
    vals: List[float] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            vals.append(float(row[metric]))
    return mean(vals)


def num(x: float, dec: int = 1) -> str:
    return f"{x:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def main() -> None:
    md: List[str] = []
    md.append("# Efeito da duração do slot (Δt) em mapas grandes — heurísticas (rascunho)")
    md.append("")
    md.append("> Rascunho de trabalho. Ainda **não** incorporado ao texto da tese.")
    md.append("")
    md.append("## Contexto e mecanismo")
    md.append("")
    md.append(
        "O custo energético de um deslocamento é `P(V)·Δt` com `V = d/Δt`. O termo de arrasto "
        "parasita domina em alta velocidade e escala com `d³/Δt²`: **aumentar Δt reduz a energia de "
        "movimento** para uma mesma distância (voa-se mais devagar). Em contrapartida, o *hover* custa "
        "`P(0)·Δt` por slot, então **a energia de existência cresce linearmente com Δt**. Como a missão "
        "ocupa `TIME_SLOTS` slots (o UAV paira quando não se desloca), há um **teto de viabilidade**: "
        "se o simples pairar durante todos os slots já excede a bateria, nenhuma trajetória é viável."
    )
    md.append("")
    md.append(
        f"Para a configuração do Parrot Anafi USA (`P(0) ≈ {num(P0,1)} W`, "
        f"`TIME_SLOTS = {common.TIME_SLOTS}` → {TRANSITIONS} transições, `BATTERY_MAX = {num(BAT,0)} J`), "
        f"esse teto fica em **Δt ≈ {num(CEILING,1)} s**: acima disso, "
        "`(TIME_SLOTS−1)·P(0)·Δt > BATTERY_MAX` e a missão é inviável mesmo sem se mover."
    )
    md.append("")
    md.append("## Piso de energia (só hover) por Δt")
    md.append("")
    md.append(f"| Δt (s) | V p/ cruzar 1000 m | hover/slot (J) | piso ({TRANSITIONS} transições, kJ) | % bateria |")
    md.append("|---|---|---|---|---|")
    for dt in SLOT_DURATIONS:
        e_hover = P0 * dt
        floor = TRANSITIONS * e_hover
        flag = " ✗ inviável" if floor > BAT else ""
        md.append(
            f"| {dt} | {num(1000/dt,0)} m/s | {num(e_hover,0)} | {num(floor/1000,1)} | "
            f"{num(100*floor/BAT,0)}%{flag} |"
        )
    md.append("")

    md.append("## AoI-Greedy: métricas vs Δt (média de 30 rodadas)")
    md.append("")
    for n in SENSOR_COUNTS:
        for L in MAP_SIZES:
            md.append(f"### P{n}-{L}")
            md.append("")
            md.append("| Δt (s) | Visitados | AoI coletada | Energia (kJ) | % bateria |")
            md.append("|---|---|---|---|---|")
            for dt in SLOT_DURATIONS:
                vis = load("aoi_greedy", dt, n, L, "visited_count")
                aoi = load("aoi_greedy", dt, n, L, "collected_aoi")
                en = load("aoi_greedy", dt, n, L, "energy_final")
                flag = " ⚠️" if vis < 0.5 else ""
                md.append(
                    f"| {dt} | {num(vis,1)}{flag} | {num(aoi,1)} | {num(en/1000,1)} | {num(100*en/BAT,0)}% |"
                )
            md.append("")

    md.append("## Comparação entre heurísticas (energia em kJ, cenário P100-2000)")
    md.append("")
    md.append("| Δt (s) | NN | AoI-Greedy | Score-Greedy |")
    md.append("|---|---|---|---|")
    for dt in SLOT_DURATIONS:
        c = [num(load(k, dt, 100, 2000, "energy_final") / 1000, 1) for k, _ in [("nn", ""), ("aoi_greedy", ""), ("score_greedy", "")]]
        md.append(f"| {dt} | {c[0]} | {c[1]} | {c[2]} |")
    md.append("")

    md.append("## Leitura dos resultados")
    md.append("")
    md.append(
        "- **Δt reduz a energia de movimento:** para o mesmo caminho, subir de Δt=10 s para 20–30 s "
        "corta o consumo (voo mais lento, menos arrasto), e as velocidades ficam realistas "
        "(50–33 m/s para cruzar 1000 m, contra 100 m/s a Δt=10 s), atacando a limitação de "
        "velocidades irreais do modelo."
    )
    md.append(
        "- **Mas há um teto por causa do hover:** a energia de existência cresce com Δt e, acima de "
        f"**~{num(CEILING,0)} s**, pairar durante a missão já estoura a bateria. A Δt=50 s as "
        "heurísticas colapsam para 0 visitas."
    )
    md.append(
        "- **Existe um ponto ótimo intermediário** (em torno de Δt=20–30 s nesta configuração): "
        "energia de movimento já bastante reduzida e velocidades realistas, sem que o custo de hover "
        "domine. Δt é, portanto, uma alavanca útil para mapas grandes, porém limitada."
    )
    md.append(
        "- **Não altera a tratabilidade do MILP:** Δt muda apenas os coeficientes de energia, não o "
        "número de variáveis (≈ N²·T). O modelo exato continua intratável em alta contagem de sensores."
    )
    md.append("")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"Rascunho escrito em {OUT_MD}")


if __name__ == "__main__":
    main()
