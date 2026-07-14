import argparse
import os
import random
from typing import List

SENSOR_COUNTS: List[int] = [50, 75, 100, 150, 200]
MAP_SIZES: List[int] = [600, 800, 1000]
BASE_SEED = 20250707


def generate_scenario(out_dir: str, n: int, L: int) -> str:
    rng = random.Random(BASE_SEED + n * 10_000 + L)
    scenario_dir = os.path.join(out_dir, str(n))
    os.makedirs(scenario_dir, exist_ok=True)
    path = os.path.join(scenario_dir, f"sensors_{L}x{L}.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("id,x,y\n")
        for i in range(1, n + 1):
            x = rng.uniform(0.0, float(L))
            y = rng.uniform(0.0, float(L))
            f.write(f"{i:03d},{x:.3f},{y:.3f}\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera cenários de larga escala (posições de sensores) para as heurísticas."
    )
    parser.add_argument(
        "--out-dir",
        default=os.path.join(os.path.dirname(__file__), "setup", "larga_escala"),
    )
    parser.add_argument(
        "--sensor-counts",
        default=",".join(str(x) for x in SENSOR_COUNTS),
    )
    parser.add_argument(
        "--map-sizes",
        default=",".join(str(x) for x in MAP_SIZES),
    )
    args = parser.parse_args()

    counts = [int(x) for x in args.sensor_counts.split(",")]
    maps = [int(x) for x in args.map_sizes.split(",")]

    total = 0
    for n in counts:
        for L in maps:
            path = generate_scenario(args.out_dir, n, L)
            print(f"[OK] n={n:>3} L={L:>4} -> {path}")
            total += 1
    print(f"\n{total} cenários gerados em {args.out_dir}")


if __name__ == "__main__":
    main()
