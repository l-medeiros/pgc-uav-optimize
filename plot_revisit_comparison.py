import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path
import re
import argparse

MAP_PATTERN = re.compile(r"round_summary_(\d+)x(\d+)\.csv")
SENSOR_COUNTS = [5, 10, 15, 20, 25, 30]
MAP_SIZES = [100, 200, 400, 600, 800, 1000]


def load_results(root_dir, label):
    records = []
    for path in Path(root_dir).rglob("round_summary_*.csv"):
        m = MAP_PATTERN.search(path.name)
        if not m:
            continue
        map_n = int(m.group(1))
        parts = path.parts
        sensor_count = None
        for i, p in enumerate(parts):
            if p in (Path(root_dir).name,):
                sensor_count = int(parts[i + 1])
                break
        if sensor_count is None:
            # fallback: numeric directory just above resultados/
            for i, p in enumerate(parts):
                if p == "resultados":
                    try:
                        sensor_count = int(parts[i - 1])
                    except (ValueError, IndexError):
                        pass
                    break
        if sensor_count is None:
            continue
        df = pd.read_csv(path)
        df["map_n"] = map_n
        df["sensor_count"] = sensor_count
        df["variant"] = label
        records.append(df)
    return pd.concat(records, ignore_index=True)


def aggregate(df):
    return (
        df.groupby(["sensor_count", "map_n", "variant"])
        .agg(
            energy_mean=("energy_final", "mean"),
            aoi_mean=("avg_final_aoi", "mean"),
            distance_mean=("total_distance", "mean"),
            visited_mean=("visited_count", "mean"),
            collected_mean=("collected_aoi", "mean"),
        )
        .reset_index()
    )


def plot_comparison_lines(agg, metric, ylabel, filename, output_dir):
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharey=False)
    axes = axes.flatten()

    for idx, n in enumerate(SENSOR_COUNTS):
        ax = axes[idx]
        for variant, style in [("base", dict(linestyle="-", marker="o")),
                                ("revisit", dict(linestyle="--", marker="s"))]:
            sub = agg[(agg.sensor_count == n) & (agg.variant == variant)].sort_values("map_n")
            ax.plot(sub.map_n, sub[metric], label=variant, **style)
        ax.set_title(f"{n} sensores")
        ax.set_xlabel("Tamanho do mapa (m)")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=8)
        ax.grid(True)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}"))
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)

    fig.suptitle(f"{ylabel} — comparativo base vs revisit (máx. 3 revisitas)")
    fig.tight_layout()
    fig.savefig(output_dir / filename, dpi=150)
    plt.close()


def plot_delta_heatmap(agg, metric, title, filename, output_dir):
    base_df = agg[agg.variant == "base"].set_index(["sensor_count", "map_n"])[metric]
    rev_df  = agg[agg.variant == "revisit"].set_index(["sensor_count", "map_n"])[metric]
    delta = ((rev_df - base_df) / base_df * 100).reset_index()
    delta.columns = ["sensor_count", "map_n", "delta_pct"]

    pivot = delta.pivot(index="sensor_count", columns="map_n", values="delta_pct")
    pivot = pivot.reindex(index=SENSOR_COUNTS, columns=MAP_SIZES)

    fig, ax = plt.subplots(figsize=(8, 5))
    vmax = max(abs(pivot.values.min()), abs(pivot.values.max()))
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn_r", vmin=-vmax, vmax=vmax)
    plt.colorbar(im, ax=ax, label="Δ% (revisit − base) / base")

    ax.set_xticks(range(len(MAP_SIZES)))
    ax.set_xticklabels(MAP_SIZES)
    ax.set_yticks(range(len(SENSOR_COUNTS)))
    ax.set_yticklabels(SENSOR_COUNTS)
    ax.set_xlabel("Tamanho do mapa (m)")
    ax.set_ylabel("Quantidade de sensores")
    ax.set_title(title)

    for i in range(len(SENSOR_COUNTS)):
        for j in range(len(MAP_SIZES)):
            val = pivot.values[i, j]
            ax.text(j, i, f"{val:+.1f}%", ha="center", va="center", fontsize=7,
                    color="black")

    fig.tight_layout()
    fig.savefig(output_dir / filename, dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir",    default="setup/anafi_usa")
    parser.add_argument("--revisit-dir", default="setup/revisit")
    parser.add_argument("--output-dir",  default="text/figs")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    print("Carregando resultados base...")
    df_base   = load_results(args.base_dir,    "base")
    print("Carregando resultados revisit...")
    df_rev    = load_results(args.revisit_dir, "revisit")

    df = pd.concat([df_base, df_rev], ignore_index=True)
    agg = aggregate(df)
    agg.to_csv(output_dir / "revisit_comparison_aggregated.csv", index=False)

    print("Gerando gráficos de linha comparativos...")
    plot_comparison_lines(agg, "energy_mean",    "Energia final (J)",      "cmp_energy_vs_map.png",    output_dir)
    plot_comparison_lines(agg, "aoi_mean",       "AoI média final (slots)", "cmp_aoi_vs_map.png",       output_dir)
    plot_comparison_lines(agg, "distance_mean",  "Distância total (m)",    "cmp_distance_vs_map.png",  output_dir)
    plot_comparison_lines(agg, "visited_mean",   "Sensores visitados",     "cmp_visited_vs_map.png",   output_dir)

    print("Gerando mapas de calor de variação percentual...")
    plot_delta_heatmap(agg, "energy_mean",   "Δ% Energia (revisit vs base)",   "delta_energy_heatmap.png",   output_dir)
    plot_delta_heatmap(agg, "aoi_mean",      "Δ% AoI média (revisit vs base)", "delta_aoi_heatmap.png",      output_dir)
    plot_delta_heatmap(agg, "visited_mean",  "Δ% Sensores visitados",          "delta_visited_heatmap.png",  output_dir)

    print("Concluído! Gráficos em:", output_dir)


if __name__ == "__main__":
    main()
