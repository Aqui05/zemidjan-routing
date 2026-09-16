"""Metriques utilisees pour comparer routage statique et adaptatif."""
from __future__ import annotations

import statistics

import networkx as nx


def edge_congestion_ratios(graph: nx.Graph, flows: dict) -> list[float]:
    """Ratio flux/capacite pour chaque axe -- 1.0 = a capacite nominale,
    >1.0 = sur-sature (embouteillage)."""
    ratios = []
    for u, v, data in graph.edges(data=True):
        flow = flows.get(frozenset((u, v)), 0.0)
        ratios.append(flow / data["capacity"])
    return ratios


def congestion_stddev(graph: nx.Graph, flows: dict) -> float:
    """Ecart-type de la congestion entre axes : montre si la charge est
    bien repartie sur le reseau ou concentree sur quelques axes."""
    ratios = edge_congestion_ratios(graph, flows)
    return statistics.pstdev(ratios) if len(ratios) > 1 else 0.0


def critical_edges_ratio(graph: nx.Graph, flows: dict, threshold: float = 1.0) -> float:
    """Proportion d'axes en congestion critique (flux >= capacite)."""
    ratios = edge_congestion_ratios(graph, flows)
    if not ratios:
        return 0.0
    return sum(1 for r in ratios if r >= threshold) / len(ratios)


def average_travel_time(travel_times: list[float]) -> float:
    return statistics.mean(travel_times) if travel_times else 0.0
