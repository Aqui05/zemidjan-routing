import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import networkx as nx

from network import EAST_BANK, WEST_BANK, build_cotonou_graph
from routing import adaptive_shortest_path, static_shortest_path


def test_graph_is_connected():
    graph = build_cotonou_graph()
    assert nx.is_connected(graph)


def test_bridge_is_sole_crossing_in_normal_conditions():
    """Verifie que la lagune ne peut etre traversee que par le pont explicite
    ou la route de contournement -- pas de raccourci 'a vol d'oiseau'."""
    graph = build_cotonou_graph()
    cross_edges = [
        (u, v) for u, v in graph.edges
        if (u in EAST_BANK) != (v in EAST_BANK)
    ]
    assert set(cross_edges) <= {("ganhi", "akpakpa"), ("akpakpa", "ganhi"),
                                 ("godomey", "akpakpa"), ("akpakpa", "godomey")}


def test_static_path_ignores_congestion():
    graph = build_cotonou_graph()
    path_before = static_shortest_path(graph, "godomey", "akpakpa")
    # meme si le pont est totalement bloque, le chemin statique ne change pas
    graph.edges[("ganhi", "akpakpa")]["capacity"] = 0.01
    path_after = static_shortest_path(graph, "godomey", "akpakpa")
    assert path_before == path_after


def test_adaptive_path_reacts_to_congestion():
    graph = build_cotonou_graph()
    heavy_flows = {frozenset(("ganhi", "akpakpa")): 500.0}  # pont tres charge
    path_normal = adaptive_shortest_path(graph, "godomey", "akpakpa", {})
    path_congested = adaptive_shortest_path(graph, "godomey", "akpakpa", heavy_flows)
    assert "ganhi" in path_normal  # en temps normal, on passe par le pont (plus court)
    assert ("ganhi" not in path_congested) or (path_congested != path_normal)


if __name__ == "__main__":
    test_graph_is_connected()
    test_bridge_is_sole_crossing_in_normal_conditions()
    test_static_path_ignores_congestion()
    test_adaptive_path_reacts_to_congestion()
    print("Tous les tests passent.")
