from typing import Dict, Tuple, List
import csv
import os
import math

# -------------------------------------------------
# Parâmetros físicos do UAV (DJI Matrice 300 RTK)
# Modelo de potência baseado em Zeng/Mu (referência [11] do Arthur)
# -------------------------------------------------

# Duração de cada slot de tempo (em segundos)
SLOT_DURATION = float(os.environ.get("SLOT_DURATION", "10.0"))

# Parâmetros do modelo de potência de asa rotativa
#  P0 = 79.86 W (blade profile power)
#  Pi = 88.63 W (induced power)
#  Utip = 120 m/s (velocidade da ponta da hélice)
#  v0 = 4.03 m/s (velocidade induzida em hover)
#  ρ = 1.225 kg/m³ (densidade do ar)
#  d0 = 0.6 (fator de arrasto do fuselagem)
#  s = 0.05 (razão de área do rotor)
#  A = 0.503 m² (área do disco do rotor)
P0 = 79.86        # W
Pi = 88.63        # W
v0 = 4.03         # m/s
U_TIP = 120.0     # m/s
RHO = 1.225       # kg/m³
CDS = 0.01509     # d0 * s * A

# Capacidade total de energia da bateria (duas TB60)
# Arthur chega a 616,2 Wh convertendo para Joules: 616.2 * 3600 ≈ 2_218_320 J
BATTERY_MAX = 141_372.0 # (PARROT ANAFI USA)
# BATTERY_MAX = 50_000.0

TIME_SLOTS = 20  # número de slots discretos


# ---------------------------------------------------------------------------
# Leitura / escrita de estado de AoI e histórico
# ---------------------------------------------------------------------------

def load_aoi_state(sensor_ids: List[int], path: str) -> Dict[int, int]:
    """
    Lê o estado atual de AoI dos sensores a partir de um CSV.
    Se o arquivo não existir, inicializa com AoI = 0 para todos.
    """
    aoi: Dict[int, int] = {sid: 0 for sid in sensor_ids}
    if not os.path.exists(path):
        return aoi

    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            sid = int(row["sensor_id"])
            if sid in aoi:
                aoi[sid] = int(float(row["aoi"]))
    return aoi


def save_aoi_state(aoi: Dict[int, int], path: str) -> None:
    """
    Persiste o estado de AoI atual em disco.
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sensor_id", "aoi"])
        for sid, val in sorted(aoi.items()):
            w.writerow([sid, val])


def next_round_index(path: str) -> int:
    """
    Retorna o índice da próxima rodada para o histórico de AoI.
    """
    if not os.path.exists(path):
        return 1

    last = 0
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(line.replace("\x00", "") for line in f)
        for row in r:
            val = row.get("round", "").strip()
            if val:
                last = max(last, int(val))
    return last + 1


def append_aoi_history(
    path: str,
    round_idx: int,
    aoi_before: Dict[int, int],
    aoi_after: Dict[int, int],
    visited: Dict[int, int],
) -> None:
    """
    Acrescenta uma linha por sensor ao histórico de AoI, contendo:
    rodada, AoI antes, AoI depois e se foi visitado.
    """
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(["round", "sensor_id", "aoi_before", "aoi_after", "visited"])
        for sid in sorted(aoi_before.keys()):
            w.writerow([
                round_idx,
                sid,
                aoi_before[sid],
                aoi_after[sid],
                visited.get(sid, 0)
            ])


def append_round_summary(
    path: str,
    round_idx: int,
    energy_final: float,
    collected_aoi: float,
    avg_final_aoi: float,
    visited_count: int,
    total_distance: float,
    path_taken: List[int],
) -> None:
    """
    Acrescenta uma linha de resumo por rodada.
    """
    file_exists = os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)

        if not file_exists:
            w.writerow([
                "round",
                "energy_final",
                "collected_aoi",
                "avg_final_aoi",
                "visited_count",
                "total_distance",
                "path_taken",
            ])

        w.writerow([
            round_idx,
            f"{energy_final:.4f}",
            f"{collected_aoi:.4f}",
            f"{avg_final_aoi:.4f}",
            visited_count,
            f"{total_distance:.4f}",
            " -> ".join(map(str, path_taken)),
        ])


# ---------------------------------------------------------------------------
# Construção dos dados do problema
# ---------------------------------------------------------------------------

def build_time_horizon() -> List[int]:
    """
    Constrói a lista de índices de slots de tempo: T = {0, ..., TIME_SLOTS-1}.
    """
    return list(range(TIME_SLOTS))


def uav_power_rotary(v: float) -> float:
    """
    Modelo de potência P(V) para VANT de asa rotativa,
    baseado em Energy Minimization for Wireless Communication With Rotary-Wing UAV.

    v: velocidade de voo (m/s)
    retorna: potência em Watts (J/s)
    """
    # Termo blade profile
    term_blade = P0 * (1.0 + 3.0 * (v ** 2) / (U_TIP ** 2))

    # Termo induced
    inside_sqrt = 1.0 + (v ** 4) / (4.0 * (v0 ** 4))
    inner = math.sqrt(inside_sqrt) - (v ** 2) / (2.0 * (v0 ** 2))
    inner = max(inner, 0.0)  # só por segurança numérica
    term_induced = Pi * math.sqrt(inner)

    # Termo parasite (CDS = C_d * s * A)
    term_parasite = 0.5 * RHO * CDS * (v ** 3)

    return term_blade + term_induced + term_parasite


def compute_energy_cost(
    nodes_map,
    node_ids: List[int],
) -> Dict[Tuple[int, int], float]:
    """
    Computa o custo de energia por aresta (i, j) em um slot:
    - Se i == j: hover por 1 slot -> P(0) * SLOT_DURATION
    - Se i != j: deslocamento de i para j em 1 slot a velocidade constante v = d_ij / SLOT_DURATION
    E = P(v) * SLOT_DURATION
    """
    energy_cost: Dict[Tuple[int, int], float] = {}

    # Potência em hover (v=0)
    p_hover = uav_power_rotary(0.0)
    e_hover = p_hover * SLOT_DURATION

    for i in node_ids:
        for j in node_ids:
            if i == j:
                # Pairando em i durante todo o slot
                energy_cost[(i, j)] = e_hover
            else:
                d_ij = nodes_map.distances[(i, j)]
                v_ij = d_ij / SLOT_DURATION
                p_ij = uav_power_rotary(v_ij)
                e_ij = p_ij * SLOT_DURATION
                energy_cost[(i, j)] = e_ij

    return energy_cost
