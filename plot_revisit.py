"""
plot_revisit.py — gera gráficos dos experimentos com revisita e comparativos
com os experimentos sem revisita (anafi_usa).

Uso:
    python plot_revisit.py \
        --revisit-dir  setup/revisit \
        --baseline-dir setup/anafi_usa \
        --output-dir   text/figs
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re
import argparse

MAP_PATTERN = re.compile(r"round_summary_(\d+)x(\d+)\.csv")


def extract_metadata(path: Path, root_dir: Path):
    """Extrai (map_n, sensor_count) do caminho do arquivo."""
    match = MAP_PATTERN.search(path.name)
    if not match:
        return None

    map_n = int(match.group(1))

    # sensor_count é o diretório imediatamente abaixo da raiz
    try:
        relative = path.relative_to(root_dir)
        sensor_count = int(relative.parts[0])
    except (ValueError, IndexError):
        return None

    return map_n, sensor_count


def load_results(root_dir: Path, max_rounds: int = 30):
    """Carrega todos os round_summary_*.csv de um diretório raiz."""
    records = []
    for file in root_dir.rglob("round_summary_*.csv"):
        meta = extract_metadata(file, root_dir)
        if meta is None:
            continue
        map_n, sensor_count = meta
        df = pd.read_csv(file).head(max_rounds)
        df["map_n"] = map_n
        df["sensor_count"] = sensor_count
        records.append(df)

    if not records:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {root_dir}")

    return pd.concat(records, ignore_index=True)


def aggregate(df):
    return (
        df.groupby(["map_n", "sensor_count"])
        .agg(
            energy_mean=("energy_final", "mean"),
            aoi_mean=("avg_final_aoi", "mean"),
            distance_mean=("total_distance", "mean"),
        )
        .reset_index()
    )


# ---------------------------------------------------------------------------
# Plots individuais (mesmo estilo de plot_anafi.py)
# ---------------------------------------------------------------------------

def plot_metric(df, metric, ylabel, filename, output_dir, title_suffix=""):
    plt.figure()
    for s in sorted(df.sensor_count.unique()):
        subset = df[df.sensor_count == s].sort_values("map_n")
        plt.plot(subset.map_n, subset[metric], marker="o", label=f"{s} sensores")
    plt.xlabel("Tamanho do mapa (n x n metros)")
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} vs tamanho do mapa{title_suffix}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_dir / filename)
    plt.close()


def plot_heatmap(df, metric, title, filename, output_dir):
    pivot = df.pivot(index="sensor_count", columns="map_n", values=metric)
    plt.figure()
    plt.imshow(pivot, aspect="auto")
    plt.colorbar()
    plt.xticks(range(len(pivot.columns)), pivot.columns)
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.xlabel("Tamanho do mapa")
    plt.ylabel("Quantidade de sensores")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_dir / filename)
    plt.close()


# ---------------------------------------------------------------------------
# Plots comparativos revisit vs baseline
# ---------------------------------------------------------------------------

def plot_comparison(agg_baseline, agg_revisit, metric, ylabel, filename, output_dir):
    """
    Para cada quantidade de sensores, plota duas curvas:
    linha sólida = sem revisita (baseline), tracejada = com revisita.
    """
    sensors = sorted(set(agg_baseline.sensor_count.unique()) &
                     set(agg_revisit.sensor_count.unique()))

    fig, ax = plt.subplots()
    prop_cycle = plt.rcParams["axes.prop_cycle"]
    colors = [p["color"] for p in prop_cycle]

    for i, s in enumerate(sensors):
        color = colors[i % len(colors)]

        b = agg_baseline[agg_baseline.sensor_count == s].sort_values("map_n")
        r = agg_revisit[agg_revisit.sensor_count == s].sort_values("map_n")

        ax.plot(b.map_n, b[metric], marker="o", color=color,
                linestyle="-", label=f"{s} s — sem revisita")
        ax.plot(r.map_n, r[metric], marker="s", color=color,
                linestyle="--", label=f"{s} s — com revisita")

    ax.set_xlabel("Tamanho do mapa (n x n metros)")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{ylabel}: com vs sem revisita")
    ax.legend(fontsize="x-small", ncol=2)
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(output_dir / filename)
    plt.close(fig)


def plot_comparison_heatmap(agg_baseline, agg_revisit, metric, title, filename, output_dir):
    """
    Heatmap da diferença (revisit - baseline) normalizada pelo baseline.
    Valores positivos = revisita melhorou, negativos = piorou.
    """
    merged = agg_baseline[["map_n", "sensor_count", metric]].merge(
        agg_revisit[["map_n", "sensor_count", metric]],
        on=["map_n", "sensor_count"],
        suffixes=("_base", "_revisit"),
    )
    merged["delta_pct"] = (
        (merged[f"{metric}_revisit"] - merged[f"{metric}_base"])
        / merged[f"{metric}_base"].abs().replace(0, float("nan"))
        * 100
    )
    pivot = merged.pivot(index="sensor_count", columns="map_n", values="delta_pct")

    plt.figure()
    im = plt.imshow(pivot, aspect="auto", cmap="RdYlGn")
    plt.colorbar(im, label="Variação (%)")
    plt.xticks(range(len(pivot.columns)), pivot.columns)
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.xlabel("Tamanho do mapa")
    plt.ylabel("Quantidade de sensores")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_dir / filename)
    plt.close()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Plots dos experimentos com revisita")
    parser.add_argument("--revisit-dir",  default="setup/revisit",
                        help="Diretório raiz dos experimentos com revisita")
    parser.add_argument("--baseline-dir", default="setup/anafi_usa",
                        help="Diretório raiz dos experimentos sem revisita (baseline)")
    parser.add_argument("--output-dir",   default="text/figs",
                        help="Diretório de saída dos gráficos")
    parser.add_argument("--max-rounds",   type=int, default=30,
                        help="Número máximo de rodadas a considerar por cenário")
    args = parser.parse_args()

    revisit_dir  = Path(args.revisit_dir)
    baseline_dir = Path(args.baseline_dir)
    output_dir   = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Carregando dados de revisita...")
    df_r = load_results(revisit_dir, max_rounds=args.max_rounds)
    agg_r = aggregate(df_r)
    agg_r.to_csv(output_dir / "revisit_summary_aggregated.csv", index=False)

    print("Carregando dados baseline (sem revisita)...")
    df_b = load_results(baseline_dir, max_rounds=args.max_rounds)
    agg_b = aggregate(df_b)

    print("Gerando gráficos individuais (revisita)...")
    plot_metric(agg_r, "energy_mean",   "Energia final (J)",     "revisit_energy_vs_map.png",   output_dir, " — com revisita")
    plot_metric(agg_r, "aoi_mean",      "AoI média final",       "revisit_aoi_vs_map.png",      output_dir, " — com revisita")
    plot_metric(agg_r, "distance_mean", "Distância total (m)",   "revisit_distance_vs_map.png", output_dir, " — com revisita")
    plot_heatmap(agg_r, "energy_mean",   "Energia média — com revisita",   "revisit_heatmap_energy.png",   output_dir)
    plot_heatmap(agg_r, "aoi_mean",      "AoI média — com revisita",       "revisit_heatmap_aoi.png",      output_dir)
    plot_heatmap(agg_r, "distance_mean", "Distância média — com revisita", "revisit_heatmap_distance.png", output_dir)

    print("Gerando gráficos comparativos (revisita vs sem revisita)...")
    plot_comparison(agg_b, agg_r, "energy_mean",   "Energia final (J)",   "cmp_energy_vs_map.png",   output_dir)
    plot_comparison(agg_b, agg_r, "aoi_mean",      "AoI média final",     "cmp_aoi_vs_map.png",      output_dir)
    plot_comparison(agg_b, agg_r, "distance_mean", "Distância total (m)", "cmp_distance_vs_map.png", output_dir)
    plot_comparison_heatmap(agg_b, agg_r, "energy_mean",   "Variação de energia (revisita vs baseline, %)",   "cmp_heatmap_energy.png",   output_dir)
    plot_comparison_heatmap(agg_b, agg_r, "aoi_mean",      "Variação de AoI (revisita vs baseline, %)",      "cmp_heatmap_aoi.png",      output_dir)
    plot_comparison_heatmap(agg_b, agg_r, "distance_mean", "Variação de distância (revisita vs baseline, %)", "cmp_heatmap_distance.png", output_dir)

    print(f"\nConcluído! Gráficos em: {output_dir}")
    print("  - revisit_*.png    : métricas do experimento com revisita")
    print("  - cmp_*.png        : comparativos com vs sem revisita")


if __name__ == "__main__":
    main()
