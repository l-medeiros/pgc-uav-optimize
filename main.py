from gurobipy import Model, GRB, quicksum
from setup.sensors import read_sensors_csv, build_nodes_map, Base, DEFAULT_SENSORS_CSV
from typing import Dict, Tuple, List
import argparse
import csv
import os
import math

# -------------------------------------------------
# Parâmetros físicos do UAV (DJI Matrice 300 RTK)
# Modelo de potência baseado em Zeng/Mu (referência [11] do Arthur)
# -------------------------------------------------

# Duração de cada slot de tempo (em segundos)
SLOT_DURATION = 10.0

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

AOI_STATE_PATH     = "/home/lucas/workspace/pgc/uav_optimize/setup/aoi_state.csv"
AOI_HISTORY_PATH   = "/home/lucas/workspace/pgc/uav_optimize/setup/posicao/30/resultados/aoi_history_1000x1000.csv"
ROUND_SUMMARY_PATH = "/home/lucas/workspace/pgc/uav_optimize/setup/posicao/30/resultados/round_summary_1000x1000.csv"


# ---------------------------------------------------------------------------
# Dividir cada tópico em arquivos diferentes
# ---------------------------------------------------------------------------

### Tópicos:

# ---------------------------------------------------------------------------
# Leitura / escrita de estado de AoI e histórico
# ---------------------------------------------------------------------------

def load_aoi_state(sensor_ids: List[int]) -> Dict[int, int]:
    """
    Lê o estado atual de AoI dos sensores a partir de um CSV.
    Se o arquivo não existir, inicializa com AoI = 0 para todos.
    """
    aoi: Dict[int, int] = {sid: 0 for sid in sensor_ids}
    if not os.path.exists(AOI_STATE_PATH):
        return aoi

    with open(AOI_STATE_PATH, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            sid = int(row["sensor_id"])
            if sid in aoi:
                aoi[sid] = int(float(row["aoi"]))
    return aoi


def save_aoi_state(aoi: Dict[int, int]) -> None:
    """
    Persiste o estado de AoI atual em disco.
    """
    with open(AOI_STATE_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sensor_id", "aoi"])
        for sid, val in sorted(aoi.items()):
            w.writerow([sid, val])


def next_round_index() -> int:
    """
    Retorna o índice da próxima rodada para o histórico de AoI.
    """
    if not os.path.exists(AOI_HISTORY_PATH):
        return 1

    last = 0
    with open(AOI_HISTORY_PATH, newline="", encoding="utf-8") as f:
        r = csv.DictReader(line.replace("\x00", "") for line in f)
        for row in r:
            val = row.get("round", "").strip()
            if val:
                last = max(last, int(val))
    return last + 1


def append_aoi_history(
    round_idx: int,
    aoi_before: Dict[int, int],
    aoi_after: Dict[int, int],
    visited: Dict[int, int],
) -> None:
    """
    Acrescenta uma linha por sensor ao histórico de AoI, contendo:
    rodada, AoI antes, AoI depois e se foi visitado.
    """
    file_exists = os.path.exists(AOI_HISTORY_PATH)
    with open(AOI_HISTORY_PATH, "a", newline="", encoding="utf-8") as f:
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
    file_exists = os.path.exists(ROUND_SUMMARY_PATH)

    with open(ROUND_SUMMARY_PATH, "a", newline="", encoding="utf-8") as f:
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


def compute_big_m_aoi(aoi_before: Dict[int, int]) -> float:
    """
    Retorna um Big-M seguro para AoI:
    M_A >= max_j A_j^0 + TIME_SLOTS.
    """
    return max([aoi_before[j] for j in aoi_before] + [0]) + TIME_SLOTS

# ---------------------------------------------------------------------------
# Criação do modelo e variáveis
# ---------------------------------------------------------------------------

def create_decision_variables(
    m: Model,
    node_ids: List[int],
    sensor_ids: List[int],
    T_slots: List[int],
    energy_cost: Dict[Tuple[int, int], float],
    aoi_before: Dict[int, int],
):
    """
    Cria todas as variáveis de decisão do modelo:
    p, x, E, y, v, A, w.
    A inicial é configurada aqui com A[j,0] = aoi_before[j].
    """
    # p[n,t] = 1 se o UAV está no nó n no slot t
    p = m.addVars(node_ids, T_slots, vtype=GRB.BINARY, name="on_node_at_slot")

    # x[i,j,t] = 1 se move de i -> j no slot t
    x = m.addVars(energy_cost.keys(), T_slots[:-1], vtype=GRB.BINARY, name="move_i_j_at_slot")

    # E[t] = energia acumulada até o slot t
    E = m.addVars(T_slots, lb=0.0, ub=BATTERY_MAX, vtype=GRB.CONTINUOUS, name="energy_cum")

    # y[j] = 1 se visitou o sensor j alguma vez no voo
    y = m.addVars(sensor_ids, vtype=GRB.BINARY, name="visited_sensor")

    # v[j,t] = 1 se coletou no sensor j no slot t
    v = m.addVars(sensor_ids, T_slots[:-1], vtype=GRB.BINARY, name="collect_at_j_t")

    # A[j,t] = AoI do sensor j no início do slot t
    A = m.addVars(sensor_ids, T_slots, lb=0.0, vtype=GRB.CONTINUOUS, name="AoI_state")

    # Inicialização de AoI
    for j in sensor_ids:
        m.addConstr(A[j, 0] == aoi_before[j], name=f"aoi_init_{j}")

    # M_A para linearização de w = A * v
    M_A = compute_big_m_aoi(aoi_before)

    # w[j,t] ~ A[j,t] * v[j,t]
    w = m.addVars(
        sensor_ids,
        T_slots[:-1],
        lb=0.0,
        ub=M_A,
        vtype=GRB.CONTINUOUS,
        name="aoi_gain"
    )

    return p, x, E, y, v, A, w, M_A


# ---------------------------------------------------------------------------
# Adição de restrições
# ---------------------------------------------------------------------------

def add_aoi_dynamics_constraints(
    m: Model,
    sensor_ids: List[int],
    T_slots: List[int],
    A,
    v,
):
    """
    Adiciona as restrições de evolução da AoI usando restrições indicadoras:
    - v=1 => A[j,t+1] = 0
    - v=0 => A[j,t+1] = A[j,t] + 1
    """
    for j in sensor_ids:
        for t in T_slots[:-1]:
            # v=1 => A[j,t+1] == 0
            m.addGenConstrIndicator(
                v[j, t], True,
                A[j, t+1] <= 0.0,
                name=f"v1_aoi_up_{j}_{t}",
            )
            m.addGenConstrIndicator(
                v[j, t], True,
                A[j, t+1] >= 0.0,
                name=f"v1_aoi_lo_{j}_{t}",
            )

            # v=0 => A[j,t+1] - A[j,t] == 1
            m.addGenConstrIndicator(
                v[j, t], False,
                A[j, t+1] - A[j, t] <= 1.0,
                name=f"v0_aoi_up_{j}_{t}",
            )
            m.addGenConstrIndicator(
                v[j, t], False,
                A[j, t+1] - A[j, t] >= 1.0,
                name=f"v0_aoi_lo_{j}_{t}",
            )


def add_start_end_constraints(
    m: Model,
    base_id: int,
    node_ids: List[int],
    sensor_ids: List[int],
    T_slots: List[int],
    p,
):
    """
    Garante que o UAV começa e termina na base,
    e não está em sensores no slot 0.
    """
    first_t = T_slots[0]
    last_t = T_slots[-1]

    # Início na base
    m.addConstr(p[base_id, first_t] == 1, name="start_at_base")
    for n in sensor_ids:
        m.addConstr(p[n, first_t] == 0, name=f"not_at_sensor_t0_{n}")

    # Retorno à base no fim
    m.addConstr(p[base_id, last_t] == 1, name="end_at_base")


def add_unique_position_constraints(
    m: Model,
    node_ids: List[int],
    T_slots: List[int],
    p,
):
    """
    Em cada slot, exatamente uma posição: sum_n p[n,t] = 1.
    """
    for t in T_slots:
        m.addConstr(
            quicksum(p[n, t] for n in node_ids) == 1,
            name=f"unique_position_t{t}",
        )


def add_flow_constraints(
    m: Model,
    node_ids: List[int],
    T_slots: List[int],
    p,
    x,
):
    """
    Fluxo temporal:
    - sum_j x[i,j,t] = p[i,t]
    - sum_i x[i,j,t] = p[j,t+1]
    Inclui self-loops.
    """
    for t in T_slots[:-1]:
        for i in node_ids:
            m.addConstr(
                quicksum(x[i, j, t] for j in node_ids) == p[i, t],
                name=f"leave_from_{i}_t{t}",
            )
        for j in node_ids:
            m.addConstr(
                quicksum(x[i, j, t] for i in node_ids) == p[j, t + 1],
                name=f"arrive_to_{j}_t{t+1}",
            )


def add_energy_constraints(
    m: Model,
    T_slots: List[int],
    E,
    x,
    energy_cost: Dict[Tuple[int, int], float],
):
    """
    Adiciona:
    - Energia inicial: E[0] = 0
    - Evolução: E[t+1] = E[t] + sum_{i,j} c_ij * x[i,j,t]
    - Capacidade: E[last_t] <= BATTERY_MAX
    """
    first_t = T_slots[0]
    last_t = T_slots[-1]

    m.addConstr(E[first_t] == 0.0, name="energy_initial_zero")

    for t in T_slots[:-1]:
        consumo_t = quicksum(
            energy_cost[i, j] * x[i, j, t] for (i, j) in energy_cost.keys()
        )
        m.addConstr(
            E[t + 1] == E[t] + consumo_t,
            name=f"energy_accum_t{t+1}",
        )

    m.addConstr(E[last_t] <= BATTERY_MAX, name="battery_capacity")


def add_visit_constraints(
    m: Model,
    node_ids: List[int],
    sensor_ids: List[int],
    T_slots: List[int],
    x,
    v,
    y,
    allow_revisit: bool = False,
):
    """
    Relaciona movimentos com visitas:
    - v[j,t] = 1 se o UAV paira (hover) no sensor j durante o slot t (j->j).
    - y[j] = 1 se o sensor j foi visitado ao menos uma vez.
    - y[j] = min(1, sum_t v[j,t]).
    - Se allow_revisit=False (padrão), cada sensor é visitado no máximo uma vez.
    """
    for j in sensor_ids:
        for t in T_slots[:-1]:
            m.addConstr(
                v[j, t] == x[j, j, t],
                name=f"collect_is_hover_{j}_{t}",
            )

    for j in sensor_ids:
        if not allow_revisit:
            m.addConstr(
                quicksum(v[j, t] for t in T_slots[:-1]) <= 1,
                name=f"visit_at_most_once_{j}",
            )
        # y[j] >= v[j,t] para todo t  →  y[j] = 1 se visitou ao menos uma vez
        for t in T_slots[:-1]:
            m.addConstr(
                y[j] >= v[j, t],
                name=f"visit_lb_{j}_{t}",
            )
        m.addConstr(
            y[j] <= quicksum(v[j, t] for t in T_slots[:-1]),
            name=f"visit_ub_{j}",
        )



def add_aoi_gain_linearization(
    m: Model,
    sensor_ids: List[int],
    T_slots: List[int],
    A,
    v,
    w,
    M_A: float,
):
    """
    Lineariza w[j,t] = A[j,t] * v[j,t] usando Big-M.
    """
    for j in sensor_ids:
        for t in T_slots[:-1]:
            m.addConstr(
                w[j, t] <= A[j, t],
                name=f"w_le_A_{j}_{t}",
            )
            m.addConstr(
                w[j, t] <= M_A * v[j, t],
                name=f"w_le_Mv_{j}_{t}",
            )
            m.addConstr(
                w[j, t] >= A[j, t] - M_A * (1 - v[j, t]),
                name=f"w_ge_A_minus_M1v_{j}_{t}",
            )


# ---------------------------------------------------------------------------
# Função objetivo
# ---------------------------------------------------------------------------

def set_multiobjective(
    m: Model,
    sensor_ids: List[int],
    T_slots: List[int],
    w,
    E,
):
    """
    Define objetivos múltiplos:
    - max AoI coletada -> min -sum w
    - min energia total E[last_t]
    Usa prioridades lexicográficas (AoI com prioridade 2, energia 1).
    """
    last_t = T_slots[-1]

    m.ModelSense = GRB.MINIMIZE

    # 1) Maximizar AoI (multiplas w's)
    m.setObjectiveN(
        -quicksum(w[j, t] for j in sensor_ids for t in T_slots[:-1]),
        index=0,
        priority=2,
    )

    # 2) Minimizar energia total no final
    m.setObjectiveN(
        E[last_t],
        index=1,
        priority=1,
    )


# ---------------------------------------------------------------------------
# Montagem do modelo completo
# ---------------------------------------------------------------------------

def build_optimization_model(
    nodes_map,
    node_ids: List[int],
    sensor_ids: List[int],
    base: Base,
    aoi_before: Dict[int, int],
    allow_revisit: bool = False,
):
    """
    Cria e retorna o modelo Gurobi e todos os componentes relevantes.
    """
    T_slots = build_time_horizon()
    energy_cost = compute_energy_cost(nodes_map, node_ids)

    m = Model("uav_optimize_aoi")

    # Variáveis
    p, x, E, y, v, A, w, M_A = create_decision_variables(
        m, node_ids, sensor_ids, T_slots, energy_cost, aoi_before
    )

    # Restrições
    add_aoi_dynamics_constraints(m, sensor_ids, T_slots, A, v)
    add_start_end_constraints(m, base.id, node_ids, sensor_ids, T_slots, p)
    add_unique_position_constraints(m, node_ids, T_slots, p)
    add_flow_constraints(m, node_ids, T_slots, p, x)
    add_energy_constraints(m, T_slots, E, x, energy_cost)
    add_visit_constraints(m, node_ids, sensor_ids, T_slots, x, v, y, allow_revisit)
    add_aoi_gain_linearization(m, sensor_ids, T_slots, A, v, w, M_A)

    # Objetivo
    set_multiobjective(m, sensor_ids, T_slots, w, E)

    return {
        "model": m,
        "nodes_map": nodes_map,
        "T_slots": T_slots,
        "node_ids": node_ids,
        "sensor_ids": sensor_ids,
        "base_id": base.id,
        "energy_cost": energy_cost,
        "p": p,
        "x": x,
        "E": E,
        "y": y,
        "v": v,
        "A": A,
        "w": w,
        "M_A": M_A,
    }


# ---------------------------------------------------------------------------
# Otimização e pós-processamento
# ---------------------------------------------------------------------------

def solve_model(m: Model) -> None:
    """
    Configura parâmetros do solver e executa a otimização.

    Parâmetros de memória:
    - Threads: limita paralelismo; menos threads = menos nós simultâneos na RAM.
    - NodefileStart: quando o uso de RAM atingir este valor (GB), Gurobi derrama
      os nós da árvore B&B para disco em vez de travar o sistema.
    - SoftMemLimit: se ultrapassar este valor (GB), encerra graciosamente e
      retorna a melhor solução encontrada até ali (evita desligar o computador).
    """
    m.setParam("TimeLimit", 60)
    m.setParam("MIPGap", 0.01)
    m.setParam("Threads", 2)
    m.setParam("NodefileStart", 0.5)
    m.setParam("SoftMemLimit", 4)
    m.optimize()


def print_status(m: Model) -> None:
    """
    Imprime o status do modelo em formato legível.
    """
    status_map = {
        GRB.OPTIMAL: "Ótimo",
        GRB.TIME_LIMIT: "TimeLimit",
        GRB.SUBOPTIMAL: "Sub-ótimo",
        GRB.INFEASIBLE: "Inviável",
        GRB.INF_OR_UNBD: "Inf/Unbd",
        GRB.UNBOUNDED: "Deslimitado",
    }
    print("\nStatus:", status_map.get(m.status, m.status))


def handle_solution(
    model_components: Dict,
    aoi_before: Dict[int, int],
) -> None:
    """
    Trata a solução encontrada (se houver): imprime métricas,
    atualiza AoI e histórico.
    """
    m = model_components["model"]
    T_slots = model_components["T_slots"]
    node_ids = model_components["node_ids"]
    sensor_ids = model_components["sensor_ids"]
    p = model_components["p"]
    E = model_components["E"]
    y = model_components["y"]
    A = model_components["A"]
    w = model_components["w"]
    nodes_map = model_components["nodes_map"]

    last_t = T_slots[-1]

    has_solution = m.SolCount > 0
    if not has_solution:
        # Sem solução viável: envelhece a AoI por TIME_SLOTS slots (UAV não voou)
        # e registra a rodada com zeros para manter o histórico consistente.
        print("Modelo não encontrou solução viável. Registrando rodada sem voo.")
        aoi_after = {sid: aoi_before[sid] + TIME_SLOTS for sid in sensor_ids}
        visited = {sid: 0 for sid in sensor_ids}
        save_aoi_state(aoi_after)
        r = next_round_index()
        append_aoi_history(r, aoi_before, aoi_after, visited)
        append_round_summary(
            round_idx=r,
            energy_final=0.0,
            collected_aoi=0.0,
            avg_final_aoi=sum(aoi_after.values()) / len(sensor_ids),
            visited_count=0,
            total_distance=0.0,
            path_taken=[],
        )
        return

    last_energy = E[last_t].X
    collected_aoi = sum(w[j, t].X for j in sensor_ids for t in T_slots[:-1])
    visited = {j: int(y[j].X > 0.5) for j in sensor_ids}
    visited_count = sum(visited.values())

    positions = []
    path_taken = []
    for t in T_slots:
        node_here = [n for n in node_ids if p[n, t].X > 0.5][0]
        positions.append((t, node_here))
        path_taken.append(node_here)

    total_distance = 0.0
    for idx in range(len(path_taken) - 1):
        i = path_taken[idx]
        j = path_taken[idx + 1]
        total_distance += nodes_map.distances[(i, j)]

    aoi_after: Dict[int, int] = {}
    for sid in sensor_ids:
        val = A[sid, last_t].X
        aoi_after[sid] = max(0, int(round(val)))

    avg_final_aoi = (
        sum(aoi_after.values()) / len(sensor_ids)
        if sensor_ids else 0.0
    )

    print(f"Energia total (E[{last_t}]): {last_energy:.4f}")
    print(f"AoI coletada nesta rodada (sum w[j,t]): {collected_aoi:.4f}")
    print(f"AoI média final dos sensores: {avg_final_aoi:.4f}")
    print(f"Sensores visitados: {visited_count}")
    print(f"Distância total percorrida: {total_distance:.4f}")
    print("Posições (t, nó):", positions)
    print("Caminho percorrido:", " -> ".join(map(str, path_taken)))

    save_aoi_state(aoi_after)

    r = next_round_index()
    append_aoi_history(r, aoi_before, aoi_after, visited)
    append_round_summary(
        round_idx=r,
        energy_final=last_energy,
        collected_aoi=collected_aoi,
        avg_final_aoi=avg_final_aoi,
        visited_count=visited_count,
        total_distance=total_distance,
        path_taken=path_taken,
    )

    print(f"Estado de AoI atualizado e historizado para a rodada {r}.")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    global AOI_STATE_PATH, AOI_HISTORY_PATH, ROUND_SUMMARY_PATH

    parser = argparse.ArgumentParser()
    parser.add_argument("--sensors-csv",   default=DEFAULT_SENSORS_CSV)
    parser.add_argument("--aoi-state",     default=AOI_STATE_PATH)
    parser.add_argument("--aoi-history",   default=AOI_HISTORY_PATH)
    parser.add_argument("--round-summary", default=ROUND_SUMMARY_PATH)
    parser.add_argument(
        "--allow-revisit",
        action="store_true",
        default=False,
        help="Remove a restrição de visita única: o UAV pode visitar cada sensor múltiplas vezes.",
    )
    args = parser.parse_args()

    AOI_STATE_PATH     = args.aoi_state
    AOI_HISTORY_PATH   = args.aoi_history
    ROUND_SUMMARY_PATH = args.round_summary

    # Carrega dados geométricos e de sensores
    sensores = read_sensors_csv(args.sensors_csv)
    base = Base()
    nodes_map = build_nodes_map(sensores, base)

    node_ids = sorted(nodes_map.coordinates.keys())
    sensor_ids = [sid for sid in node_ids if sid != base.id]

    # AoI estado ANTES do voo
    aoi_before = load_aoi_state(sensor_ids)

    # Constrói modelo
    model_components = build_optimization_model(
        nodes_map=nodes_map,
        node_ids=node_ids,
        sensor_ids=sensor_ids,
        base=base,
        aoi_before=aoi_before,
        allow_revisit=args.allow_revisit,
    )

    # Resolve
    solve_model(model_components["model"])
    print_status(model_components["model"])

    # Pós-processamento
    handle_solution(model_components, aoi_before)


if __name__ == "__main__":
    main()
