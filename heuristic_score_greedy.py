from setup.sensors import read_sensors_csv, build_nodes_map, Base, DEFAULT_SENSORS_CSV
from setup.common import (
    TIME_SLOTS,
    BATTERY_MAX,
    compute_energy_cost,
    load_aoi_state,
    save_aoi_state,
    next_round_index,
    append_aoi_history,
    append_round_summary,
)
from typing import Dict, List, Tuple
import argparse


def build_visit_order(
    nodes_map,
    base_id: int,
    sensor_ids: List[int],
    energy_cost: Dict[Tuple[int, int], float],
    aoi_before: Dict[int, int],
) -> List[int]:
    e_hover = energy_cost[(base_id, base_id)]
    max_transitions = TIME_SLOTS - 1

    unvisited = set(sensor_ids)
    visit_order: List[int] = []
    current = base_id
    energy = 0.0
    slots_used = 0

    while unvisited:
        slots_after = slots_used + 2
        if slots_after + 1 > max_transitions:
            break

        idle_after = max_transitions - (slots_after + 1)

        best_key = None
        best_node = None
        best_move_cost = None

        for j in unvisited:
            move_cost = energy_cost[(current, j)]
            return_cost = energy_cost[(j, base_id)]
            projected = energy + move_cost + e_hover + return_cost + idle_after * e_hover
            if projected > BATTERY_MAX:
                continue

            dist = nodes_map.distances[(current, j)]
            score = aoi_before[j] / dist if dist > 0 else 0.0
            key = (-score, dist, j)
            if best_key is None or key < best_key:
                best_key = key
                best_node = j
                best_move_cost = move_cost

        if best_node is None:
            break

        energy += best_move_cost + e_hover
        slots_used = slots_after
        visit_order.append(best_node)
        unvisited.discard(best_node)
        current = best_node

    return visit_order


def build_path(base_id: int, visit_order: List[int]) -> List[int]:
    max_transitions = TIME_SLOTS - 1

    path: List[int] = [base_id]
    for j in visit_order:
        path.append(j)
        path.append(j)

    if path[-1] != base_id:
        path.append(base_id)

    while len(path) - 1 < max_transitions:
        path.append(base_id)

    return path


def simulate_flight(
    path: List[int],
    sensor_ids: List[int],
    aoi_before: Dict[int, int],
    nodes_map,
    energy_cost: Dict[Tuple[int, int], float],
):
    A = {sid: aoi_before[sid] for sid in sensor_ids}
    collected_aoi = 0.0
    visited = {sid: 0 for sid in sensor_ids}
    energy_final = 0.0
    total_distance = 0.0

    for t in range(len(path) - 1):
        i = path[t]
        j = path[t + 1]
        energy_final += energy_cost[(i, j)]
        total_distance += nodes_map.distances[(i, j)]

        collecting = i if (i == j and i in A) else None
        for sid in sensor_ids:
            if sid == collecting:
                collected_aoi += A[sid]
                A[sid] = 0
                visited[sid] = 1
            else:
                A[sid] += 1

    aoi_after = {sid: int(A[sid]) for sid in sensor_ids}
    return energy_final, total_distance, collected_aoi, aoi_after, visited


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sensors-csv",   default=DEFAULT_SENSORS_CSV)
    parser.add_argument("--aoi-state",     default="setup/aoi_state_score_greedy.csv")
    parser.add_argument("--aoi-history",   default="setup/aoi_history_score_greedy.csv")
    parser.add_argument("--round-summary", default="setup/round_summary_score_greedy.csv")
    args = parser.parse_args()

    sensores = read_sensors_csv(args.sensors_csv)
    base = Base()
    nodes_map = build_nodes_map(sensores, base)

    node_ids = sorted(nodes_map.coordinates.keys())
    sensor_ids = [sid for sid in node_ids if sid != base.id]

    aoi_before = load_aoi_state(sensor_ids, args.aoi_state)
    energy_cost = compute_energy_cost(nodes_map, node_ids)

    visit_order = build_visit_order(nodes_map, base.id, sensor_ids, energy_cost, aoi_before)
    path = build_path(base.id, visit_order)

    energy_final, total_distance, collected_aoi, aoi_after, visited = simulate_flight(
        path, sensor_ids, aoi_before, nodes_map, energy_cost
    )

    visited_count = sum(visited.values())
    avg_final_aoi = (
        sum(aoi_after.values()) / len(sensor_ids)
        if sensor_ids else 0.0
    )

    print(f"Energia total: {energy_final:.4f}")
    print(f"AoI coletada nesta rodada: {collected_aoi:.4f}")
    print(f"AoI média final dos sensores: {avg_final_aoi:.4f}")
    print(f"Sensores visitados: {visited_count}")
    print(f"Distância total percorrida: {total_distance:.4f}")
    print("Caminho percorrido:", " -> ".join(map(str, path)))

    save_aoi_state(aoi_after, args.aoi_state)

    r = next_round_index(args.aoi_history)
    append_aoi_history(args.aoi_history, r, aoi_before, aoi_after, visited)
    append_round_summary(
        path=args.round_summary,
        round_idx=r,
        energy_final=energy_final,
        collected_aoi=collected_aoi,
        avg_final_aoi=avg_final_aoi,
        visited_count=visited_count,
        total_distance=total_distance,
        path_taken=path,
    )

    print(f"Estado de AoI atualizado e historizado para a rodada {r}.")


if __name__ == "__main__":
    main()
