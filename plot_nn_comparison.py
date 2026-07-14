import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re
import argparse

MAP_PATTERN = re.compile(r"round_summary_(\d+)x(\d+)\.csv")

# (chave, pasta de resultados, rótulo, cor, rótulo curto p/ barras)
ALGOS = [
    ("milp", "resultados", "MILP (Gurobi)", "tab:blue", "MILP"),
    ("nn", "resultados_nn", "Nearest Neighbor", "tab:orange", "NN"),
    ("aoi_greedy", "resultados_aoi_greedy", "AoI-Greedy", "tab:green", "AoI-G"),
    ("score_greedy", "resultados_score_greedy", "Score-Greedy (AoI/dist)", "tab:red", "Score-G"),
]

METRICS = [
    ("collected_aoi", "AoI coletada por rodada", "comparison_collected_aoi.png"),
    ("avg_final_aoi", "AoI média final dos sensores", "comparison_avg_final_aoi.png"),
    ("energy_final", "Energia final (J)", "comparison_energy.png"),
    ("total_distance", "Distância total (m)", "comparison_distance.png"),
    ("visited_count", "Sensores visitados", "comparison_visited.png"),
]


def extract_metadata(path: Path):
    match = MAP_PATTERN.search(path.name)
    if not match:
        return None

    map_n = int(match.group(1))
    parts = path.parts
    sensor_count = None
    for i, p in enumerate(parts):
        if p == "anafi_usa":
            sensor_count = int(parts[i + 1])
            break
    if sensor_count is None:
        return None
    return map_n, sensor_count


def load_results(root_dir, results_dirname, algo):
    records = []
    for file in Path(root_dir).rglob("round_summary_*.csv"):
        if file.parent.name != results_dirname:
            continue
        meta = extract_metadata(file)
        if meta is None:
            continue
        map_n, sensor_count = meta
        df = pd.read_csv(file)
        df["map_n"] = map_n
        df["sensor_count"] = sensor_count
        df["algo"] = algo
        records.append(df)
    if not records:
        raise Exception(f"Nenhum CSV encontrado em {results_dirname}")
    return pd.concat(records, ignore_index=True)


def aggregate(df):
    return (
        df.groupby(["algo", "sensor_count", "map_n"])
        .agg(
            collected_aoi=("collected_aoi", "mean"),
            avg_final_aoi=("avg_final_aoi", "mean"),
            energy_final=("energy_final", "mean"),
            total_distance=("total_distance", "mean"),
            visited_count=("visited_count", "mean"),
        )
        .reset_index()
    )


def plot_metric_facets(agg, metric, ylabel, filename, output_dir):
    sensors = sorted(agg.sensor_count.unique())
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True)
    axes = axes.flatten()

    for ax, s in zip(axes, sensors):
        for key, _, label, color, _short in ALGOS:
            sub = agg[(agg.algo == key) & (agg.sensor_count == s)].sort_values("map_n")
            ax.plot(sub.map_n, sub[metric], marker="o", color=color, label=label)
        ax.set_title(f"{s} sensores")
        ax.grid(True, alpha=0.3)

    for ax in axes[len(sensors):]:
        ax.set_visible(False)

    titulo = " vs ".join(short for _k, _d, _l, _c, short in ALGOS)
    fig.supxlabel("Tamanho do mapa (L x L, metros)")
    fig.supylabel(ylabel)
    fig.suptitle(f"{ylabel}: {titulo}")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right")
    fig.tight_layout()
    fig.savefig(output_dir / filename, dpi=120)
    plt.close(fig)


SENSOR_PAIRS = [(5, 10), (15, 20), (25, 30)]

PAIR_METRICS = [
    ("collected_aoi", "AoI coletada por rodada", "cmp_all_collected_aoi"),
    ("avg_final_aoi", "AoI média final dos sensores", "cmp_all_avg_final_aoi"),
    ("energy_final", "Energia final (J)", "cmp_all_energy"),
]


def plot_metric_pairs(agg, metric, ylabel, base_name, output_dir):
    for idx, pair in enumerate(SENSOR_PAIRS, start=1):
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharex=True)
        for ax, s in zip(axes, pair):
            for key, _, label, color, _short in ALGOS:
                sub = agg[(agg.algo == key) & (agg.sensor_count == s)].sort_values("map_n")
                ax.plot(sub.map_n, sub[metric], marker="o", color=color, label=label)
            ax.set_title(f"{s} sensores")
            ax.set_xlabel("Tamanho do mapa (L x L, metros)")
            ax.grid(True, alpha=0.3)
        axes[0].set_ylabel(ylabel)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.tight_layout(rect=[0, 0, 1, 0.90])
        fig.legend(handles, labels, loc="upper center", ncol=len(ALGOS), bbox_to_anchor=(0.5, 1.00))
        fig.savefig(output_dir / f"{base_name}_p{idx}.png", dpi=140, bbox_inches="tight")
        plt.close(fig)


def plot_overall_bars(agg, output_dir):
    overall = agg.groupby("algo")[
        ["collected_aoi", "avg_final_aoi", "energy_final", "total_distance", "visited_count"]
    ].mean()

    shorts = [short for _k, _d, _l, _c, short in ALGOS]
    colors = [c for _k, _d, _l, c, _s in ALGOS]
    keys = [k for k, _d, _l, _c, _s in ALGOS]

    fig, axes = plt.subplots(1, len(METRICS), figsize=(18, 4))
    for ax, (metric, ylabel, _) in zip(axes, METRICS):
        vals = [overall.loc[k, metric] for k in keys]
        ax.bar(shorts, vals, color=colors)
        ax.set_title(ylabel, fontsize=9)
        ax.grid(True, axis="y", alpha=0.3)
    fig.suptitle("Média geral entre todos os cenários (36 cenários x 30 rodadas)")
    fig.tight_layout()
    fig.savefig(output_dir / "comparison_overall_bars.png", dpi=120)
    plt.close(fig)
    return overall


def main():
    global ALGOS
    parser = argparse.ArgumentParser()
    parser.add_argument("root_dir", help="Diretório raiz dos experimentos (anafi_usa)")
    parser.add_argument("--output-dir", default="plots/comparison")
    parser.add_argument(
        "--algos",
        default=",".join(k for k, *_ in ALGOS),
        help="Chaves separadas por vírgula (ex.: milp,nn). Default: todas.",
    )
    args = parser.parse_args()

    selected = [a.strip() for a in args.algos.split(",")]
    ALGOS = [a for a in ALGOS if a[0] in selected]

    root_dir = Path(args.root_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Carregando resultados...")
    frames = [load_results(root_dir, dirname, key) for key, dirname, _l, _c, _s in ALGOS]
    df = pd.concat(frames, ignore_index=True)

    print("Agregando...")
    agg = aggregate(df)
    agg.to_csv(output_dir / "comparison_aggregated.csv", index=False)

    print("Gerando gráficos...")
    for metric, ylabel, filename in METRICS:
        plot_metric_facets(agg, metric, ylabel, filename, output_dir)
    for metric, ylabel, base in PAIR_METRICS:
        plot_metric_pairs(agg, metric, ylabel, base, output_dir)
    overall = plot_overall_bars(agg, output_dir)

    print("\n=== Média geral (todos os cenários) ===")
    print(overall.round(2).to_string())
    print("\nGráficos salvos em:", output_dir)


if __name__ == "__main__":
    main()
