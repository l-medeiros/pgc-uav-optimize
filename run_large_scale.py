import os
import subprocess
import sys
import time
from statistics import mean, median
from typing import List

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(ROOT, "setup", "larga_escala")
TIMING_CSV = os.path.join(BASE_DIR, "timing.csv")

SENSOR_COUNTS: List[int] = [50, 75, 100, 150, 200]
MAP_SIZES: List[int] = [600, 800, 1000]
RUNS = 30

HEURISTICS = [
    ("nn", "heuristic_nn.py"),
    ("aoi_greedy", "heuristic_aoi_greedy.py"),
    ("score_greedy", "heuristic_score_greedy.py"),
]


def run_scenario(script: str, sensors_csv: str, res_dir: str, n: int, L: int) -> List[float]:
    os.makedirs(res_dir, exist_ok=True)
    aoi_state = os.path.join(res_dir, f"aoi_state_{L}x{L}.tmp.csv")
    aoi_history = os.path.join(res_dir, f"aoi_history_{L}x{L}.csv")
    round_summary = os.path.join(res_dir, f"round_summary_{L}x{L}.csv")
    for p in (aoi_state, aoi_history, round_summary):
        if os.path.exists(p):
            os.remove(p)

    per_round: List[float] = []
    for _ in range(RUNS):
        t0 = time.perf_counter()
        proc = subprocess.run(
            [
                sys.executable,
                os.path.join(ROOT, script),
                "--sensors-csv", sensors_csv,
                "--aoi-state", aoi_state,
                "--aoi-history", aoi_history,
                "--round-summary", round_summary,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        per_round.append(time.perf_counter() - t0)
        if proc.returncode != 0:
            sys.stderr.write(proc.stderr.decode(errors="replace"))
            raise RuntimeError(f"falha em {script} n={n} L={L}")

    if os.path.exists(aoi_state):
        os.remove(aoi_state)
    return per_round


def main() -> None:
    rows = ["heuristic,n,L,rounds,total_sec,mean_sec_round,median_sec_round"]
    for key, script in HEURISTICS:
        for n in SENSOR_COUNTS:
            for L in MAP_SIZES:
                sensors_csv = os.path.join(BASE_DIR, str(n), f"sensors_{L}x{L}.csv")
                res_dir = os.path.join(BASE_DIR, str(n), f"resultados_{key}")
                print(f"[RUN] {key:>12} | n={n:>3} L={L:>4} ...", flush=True)
                pr = run_scenario(script, sensors_csv, res_dir, n, L)
                total = sum(pr)
                rows.append(
                    f"{key},{n},{L},{RUNS},{total:.3f},{mean(pr):.4f},{median(pr):.4f}"
                )
                print(
                    f"      total={total:.1f}s | mediana/rodada={median(pr)*1000:.0f} ms",
                    flush=True,
                )

    with open(TIMING_CSV, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
    print(f"\nTiming salvo em {TIMING_CSV}")


if __name__ == "__main__":
    main()
