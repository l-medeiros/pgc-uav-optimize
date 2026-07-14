import os
import subprocess
import sys
import time
from statistics import median
from typing import List

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(ROOT, "setup", "slot_duration")

SLOT_DURATIONS: List[int] = [10, 20, 30, 40, 50]
SENSOR_COUNTS: List[int] = [50, 100, 200]
MAP_SIZES: List[int] = [600, 800, 1000, 2000, 4000]
RUNS = 30

HEURISTICS = [
    ("nn", "heuristic_nn.py"),
    ("aoi_greedy", "heuristic_aoi_greedy.py"),
    ("score_greedy", "heuristic_score_greedy.py"),
]


def run_scenario(script, sensors_csv, res_dir, dt, n, L) -> None:
    os.makedirs(res_dir, exist_ok=True)
    aoi_state = os.path.join(res_dir, f"aoi_state_{L}x{L}.tmp.csv")
    aoi_history = os.path.join(res_dir, f"aoi_history_{L}x{L}.csv")
    round_summary = os.path.join(res_dir, f"round_summary_{L}x{L}.csv")
    for p in (aoi_state, aoi_history, round_summary):
        if os.path.exists(p):
            os.remove(p)

    env = dict(os.environ, SLOT_DURATION=str(dt))
    for _ in range(RUNS):
        proc = subprocess.run(
            [
                sys.executable, os.path.join(ROOT, script),
                "--sensors-csv", sensors_csv,
                "--aoi-state", aoi_state,
                "--aoi-history", aoi_history,
                "--round-summary", round_summary,
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stderr.decode(errors="replace"))
            raise RuntimeError(f"falha {script} dt={dt} n={n} L={L}")

    if os.path.exists(aoi_state):
        os.remove(aoi_state)


def main() -> None:
    for dt in SLOT_DURATIONS:
        for key, script in HEURISTICS:
            for n in SENSOR_COUNTS:
                for L in MAP_SIZES:
                    sensors_csv = os.path.join(BASE_DIR, str(n), f"sensors_{L}x{L}.csv")
                    res_dir = os.path.join(BASE_DIR, str(n), f"resultados_{key}_dt{dt}")
                    print(f"[RUN] dt={dt:>2}s {key:>12} n={n:>3} L={L:>4}", flush=True)
                    run_scenario(script, sensors_csv, res_dir, dt, n, L)
    print("\nConcluído.")


if __name__ == "__main__":
    main()
