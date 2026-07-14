import csv
import os
from statistics import mean
from typing import Dict, List, Tuple

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(ROOT, "setup", "larga_escala")
OUT_MD = os.path.join(ROOT, "text", "comparacao_larga_escala_rascunho.md")

SENSOR_COUNTS = [50, 75, 100, 150, 200]
MAP_SIZES = [600, 800, 1000]
HEURS = [("nn", "NN"), ("aoi_greedy", "AoI-Greedy"), ("score_greedy", "Score-Greedy")]
METRICS = ["collected_aoi", "avg_final_aoi", "energy_final", "visited_count", "total_distance"]


def load_summary(key: str, n: int, L: int) -> Dict[str, float]:
    path = os.path.join(BASE_DIR, str(n), f"resultados_{key}", f"round_summary_{L}x{L}.csv")
    cols: Dict[str, List[float]] = {m: [] for m in METRICS}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for m in METRICS:
                cols[m].append(float(row[m]))
    return {m: mean(v) for m, v in cols.items()}


def load_timing() -> Dict[Tuple[str, int, int], float]:
    t: Dict[Tuple[str, int, int], float] = {}
    with open(os.path.join(BASE_DIR, "timing.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t[(row["heuristic"], int(row["n"]), int(row["L"]))] = float(row["median_sec_round"]) * 1000
    return t


def fmt(x: float, dec: int = 1) -> str:
    return f"{x:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def metric_table(data, metric: str, dec: int, better: str) -> str:
    arrow = "menor = melhor" if better == "low" else "maior = melhor"
    lines = [f"### {metric} ({arrow})", ""]
    lines.append("| Cenário | NN | AoI-Greedy | Score-Greedy |")
    lines.append("|---|---|---|---|")
    for n in SENSOR_COUNTS:
        for L in MAP_SIZES:
            vals = {k: data[(k, n, L)][metric] for k, _ in HEURS}
            best = min(vals.values()) if better == "low" else max(vals.values())
            cells = []
            for k, _ in HEURS:
                s = fmt(vals[k], dec)
                if abs(vals[k] - best) < 1e-9:
                    s = f"**{s}**"
                cells.append(s)
            lines.append(f"| P{n}-{L} | {cells[0]} | {cells[1]} | {cells[2]} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    data = {(k, n, L): load_summary(k, n, L) for k, _ in HEURS for n in SENSOR_COUNTS for L in MAP_SIZES}
    timing = load_timing()

    md: List[str] = []
    md.append("# Comparação em larga escala — heurísticas onde o MILP não é tratável (rascunho)")
    md.append("")
    md.append("> Rascunho de trabalho. Ainda **não** incorporado ao texto da tese.")
    md.append("")
    md.append("## Contexto")
    md.append("")
    md.append(
        "Cenários de larga escala gerados para avaliar as heurísticas construtivas em instâncias "
        "nas quais o modelo exato (MILP/Gurobi) deixa de ser tratável. O número de variáveis binárias "
        "do MILP cresce com N²·T (N = sensores + base, T = slots), e observou-se que a partir de "
        "**30 sensores em mapa 1000×1000 m** o solver já fica muito lento / trava dentro do "
        "`TimeLimit` de 60 s. Toda a grade abaixo está, portanto, além da região viável do MILP e é "
        "resolvida apenas pelas heurísticas."
    )
    md.append("")
    md.append("**Parâmetros:** Parrot Anafi USA; `SLOT_DURATION = 10 s`; `TIME_SLOTS = 20`; "
              "`BATTERY_MAX = 141.372 J`; 30 rodadas por cenário (AoI encadeada entre rodadas).")
    md.append("")
    md.append("**Grade:** n ∈ {50, 75, 100, 150, 200} sensores × L ∈ {600, 800, 1000} m "
              "(posições uniformes, seed fixa — ver `generate_large_scenarios.py`).")
    md.append("")
    md.append("## Tempo de execução")
    md.append("")
    md.append("Tempo de parede por rodada (mediana das 30), **incluindo a inicialização do "
              "interpretador Python (~25–30 ms)** — ou seja, é um teto; o algoritmo em si é mais rápido. "
              "Comparar com o MILP, que nessas escalas não retorna solução dentro dos 60 s.")
    md.append("")
    md.append("| Cenário | NN | AoI-Greedy | Score-Greedy |")
    md.append("|---|---|---|---|")
    for n in SENSOR_COUNTS:
        for L in MAP_SIZES:
            c = [f"{timing[(k, n, L)]:.0f} ms" for k, _ in HEURS]
            md.append(f"| P{n}-{L} | {c[0]} | {c[1]} | {c[2]} |")
    md.append("")
    md.append("Todas as heurísticas resolvem cada rodada em algumas dezenas de milissegundos até "
              "n = 200, contra o MILP que não conclui em 60 s a partir de ~30 sensores.")
    md.append("")

    md.append("## Métricas médias (30 rodadas)")
    md.append("")
    md.append(metric_table(data, "collected_aoi", 1, "high"))
    md.append(metric_table(data, "avg_final_aoi", 2, "low"))
    md.append(metric_table(data, "energy_final", 0, "low"))
    md.append(metric_table(data, "total_distance", 0, "high"))

    md.append("### Sensores visitados por rodada")
    md.append("")
    md.append(
        "Constante em **9** para as três heurísticas em todos os 15 cenários. O gargalo não é o "
        "número de sensores, e sim `TIME_SLOTS = 20`: cada coleta consome cerca de 2 slots "
        "(deslocamento + *hover*), mais o retorno à base, o que limita o número de visitas por "
        "rodada independentemente de haver 50 ou 200 sensores disponíveis. Aumentar `n` amplia o "
        "*pool* de sensores desatualizados que uma heurística sensível à AoI pode explorar, mas "
        "não aumenta quantas coletas cabem na janela de tempo."
    )
    md.append("")

    # Observações automáticas
    wins = {k: {"collected_aoi": 0, "avg_final_aoi": 0, "energy_final": 0} for k, _ in HEURS}
    for n in SENSOR_COUNTS:
        for L in MAP_SIZES:
            for m, better in [("collected_aoi", "high"), ("avg_final_aoi", "low"), ("energy_final", "low")]:
                vals = {k: data[(k, n, L)][m] for k, _ in HEURS}
                winner = min(vals, key=vals.get) if better == "low" else max(vals, key=vals.get)
                wins[winner][m] += 1
    md.append("## Observações (contagem de melhores por cenário, de 15)")
    md.append("")
    md.append("| Heurística | AoI coletada | AoI final (frescor) | Energia |")
    md.append("|---|---|---|---|")
    for k, label in HEURS:
        md.append(f"| {label} | {wins[k]['collected_aoi']} | {wins[k]['avg_final_aoi']} | {wins[k]['energy_final']} |")
    md.append("")

    md.append("## Leitura dos resultados")
    md.append("")
    md.append(
        "- **Tempo:** todas as heurísticas concluem cada rodada em dezenas de milissegundos até "
        "n = 200, enquanto o MILP não retorna solução dentro dos 60 s nessas escalas. Esse é o ponto "
        "central: as heurísticas viabilizam instâncias fora do alcance do modelo exato."
    )
    md.append(
        "- **NN não escala em qualidade:** por ignorar a AoI e revisitar sempre os sensores mais "
        "próximos, coleta uma AoI praticamente constante (~159) e mantém a pior AoI final, "
        "independentemente de `n`. Em compensação, é sempre o de menor energia (visita vizinhos)."
    )
    md.append(
        "- **AoI-Greedy domina a coleta e o frescor:** vence a AoI coletada em 13/15 e a AoI final em "
        "14/15, e o ganho cresce com `n` (mais sensores desatualizados para priorizar). O custo é a "
        "maior energia, pois busca sensores distantes de alta AoI sem ponderar deslocamento."
    )
    md.append(
        "- **Score-Greedy é o equilíbrio:** fica próximo do AoI-Greedy em coleta, porém com energia "
        "sensivelmente menor (pondera AoI por distância), ao custo de um frescor um pouco pior."
    )
    md.append(
        "- **Gargalo de slots:** com `TIME_SLOTS = 20`, o número de coletas por rodada satura em ~9. "
        "Aumentar a densidade de sensores beneficia apenas as heurísticas sensíveis à AoI, que passam "
        "a ter mais alvos relevantes para escolher dentro do mesmo orçamento de visitas."
    )
    md.append("")

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"Rascunho escrito em {OUT_MD}")


if __name__ == "__main__":
    main()
