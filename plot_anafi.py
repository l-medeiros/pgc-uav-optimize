import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import re
import argparse

MAP_PATTERN = re.compile(r"round_summary_(\d+)x(\d+)\.csv")


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


def load_all_results(root_dir):
    records = []

    csv_files = list(Path(root_dir).rglob("round_summary_*.csv"))

    for file in csv_files:
        meta = extract_metadata(file)
        if meta is None:
            continue

        map_n, sensor_count = meta

        df = pd.read_csv(file)
        df["map_n"] = map_n
        df["sensor_count"] = sensor_count

        records.append(df)

    if not records:
        raise Exception("Nenhum CSV encontrado")

    return pd.concat(records, ignore_index=True)


def aggregate_results(df):
    agg = (
        df.groupby(["map_n", "sensor_count"])
        .agg(
            energy_mean=("energy_final", "mean"),
            aoi_mean=("avg_final_aoi", "mean"),
            distance_mean=("total_distance", "mean"),
        )
        .reset_index()
    )
    return agg


def plot_metric(df, metric, ylabel, filename, output_dir):
    plt.figure()
    sensors = sorted(df.sensor_count.unique())

    for s in sensors:
        subset = df[df.sensor_count == s].sort_values("map_n")
        plt.plot(subset.map_n, subset[metric], marker="o", label=f"{s} sensores")

    plt.xlabel("Tamanho do mapa (n x n)")
    plt.ylabel(ylabel)
    plt.title(ylabel + " vs tamanho do mapa")
    plt.legend()
    plt.grid(True)
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
    plt.savefig(output_dir / filename)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root_dir", help="Diretório raiz dos experimentos (anafi_usa)")
    parser.add_argument("--output-dir", default="text/figs")

    args = parser.parse_args()

    root_dir = Path(args.root_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    print("Carregando CSVs...")
    df = load_all_results(root_dir)

    print("Agregando resultados...")
    agg = aggregate_results(df)
    agg.to_csv(output_dir / "anafi_summary_aggregated.csv", index=False)

    print("Gerando gráficos...")

    plot_metric(agg, "energy_mean", "Energia final", "anafi_energy_vs_map.png", output_dir)
    plot_metric(agg, "aoi_mean", "AoI média final", "anafi_aoi_vs_map.png", output_dir)
    plot_metric(agg, "distance_mean", "Distância total", "anafi_distance_vs_map.png", output_dir)

    plot_heatmap(agg, "energy_mean", "Energia média (Anafi)", "anafi_heatmap_energy.png", output_dir)
    plot_heatmap(agg, "aoi_mean", "AoI média (Anafi)", "anafi_heatmap_aoi.png", output_dir)
    plot_heatmap(agg, "distance_mean", "Distância média (Anafi)", "anafi_heatmap_distance.png", output_dir)

    print("Concluído! Gráficos em:", output_dir)


if __name__ == "__main__":
    main()
