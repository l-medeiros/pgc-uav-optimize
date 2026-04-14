from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import csv
import math

@dataclass(frozen=True)
class Sensor:
    id: int
    x: float
    y: float

@dataclass(frozen=True)
class Base:
    id: int = 0
    x: float = 0.0
    y: float = 0.0

Coordinates = Dict[int, Tuple[float, float]]
DistanceMatrix  = Dict[Tuple[int, int], float]

@dataclass(frozen=True)
class NodesMap:
    coordinates: Coordinates
    distances: DistanceMatrix


DEFAULT_SENSORS_CSV = "/home/lucas/workspace/pgc/uav_optimize/setup/posicao/30/sensors_1000x1000.csv"

def read_sensors_csv(path: str = DEFAULT_SENSORS_CSV) -> List[Sensor]:
    sensors: List[Sensor] = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            sensors.append(Sensor(int(row["id"]), float(row["x"]), float(row["y"])))
    return sensors

def build_nodes_map(sensors: List[Sensor], base: Base = Base()) -> NodesMap:
    node_ids: List[int] = [base.id] + [s.id for s in sensors]
    coords: Dict[int, Tuple[float, float]] = {base.id: (base.x, base.y)}
    for s in sensors:
        coords[s.id] = (s.x, s.y)

    distances: Dict[Tuple[int, int], float] = {}
    T: Dict[Tuple[int, int], float] = {}

    for i in node_ids:
        xi, yi = coords[i]

        for j in node_ids:
            if j < i:
                continue

            if i == j:
                distance_ij = 0.0
            else:
                xj, yj = coords[j]
                distance_ij = math.hypot(xi - xj, yi - yj)

            distances[(i, j)] = distance_ij
            distances[(j, i)] = distance_ij

    return NodesMap(coordinates=coords, distances=distances)