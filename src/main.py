from __future__ import annotations

import os
import statistics

from network import build_cotonou_graph
from simulator import run_bridge_blockage_scenario, run_static_vs_adaptive
from visualize import plot_blockage_comparison, plot_network_map

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
BRIDGE_EDGE = ("ganhi", "akpakpa")
PEAK_ROUND = 23  # round ou le temps de trajet statique explose le plus dans nos runs (seed=7)


def main() -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("=== Scenario 1 : statique vs adaptatif en regime normal ===")
    result = run_static_vs_adaptive(rounds=30, trips_per_round=60, seed=42)
    static_times = [h["avg_travel_time"] for h in result["history"]["static"]]
    adaptive_times = [h["avg_travel_time"] for h in result["history"]["adaptive"]]
    print(f"Temps de trajet moyen (statique)  : {statistics.mean(static_times):.1f} min")
    print(f"Temps de trajet moyen (adaptatif) : {statistics.mean(adaptive_times):.1f} min")
    print("-> En trafic fluide, rien a eviter : les deux strategies se valent.")
    print("   La difference apparait sous stress (voir scenario 2).")

    normal_graph = build_cotonou_graph()
    plot_network_map(
        normal_graph, result["final_adaptive_flows"], f"{RESULTS_DIR}/network_map_normal.png",
        "Réseau routier de Cotonou — trafic en régime normal",
    )

    print("\n=== Scenario 2 : blocage du pont (accident), statique vs adaptatif ===")
    blockage = run_bridge_blockage_scenario(
        rounds=40, trips_per_round=60, blockage_start=15, blockage_end=25, seed=7,
    )
    hist = blockage["history"]

    plot_blockage_comparison(
        hist, blockage["blockage_start"], blockage["blockage_end"],
        f"{RESULTS_DIR}/blockage_comparison.png",
    )

    during_static = statistics.mean(hist["static"]["avg_time"][14:25])
    during_adaptive = statistics.mean(hist["adaptive"]["avg_time"][14:25])
    reduction_pct = (1 - during_adaptive / during_static) * 100

    print(f"Temps de trajet moyen pendant l'incident (statique)  : {during_static:.1f} min")
    print(f"Temps de trajet moyen pendant l'incident (adaptatif) : {during_adaptive:.1f} min")
    print(f"Reduction du temps de trajet grace au routage adaptatif : {reduction_pct:.1f}%")

    # Cartes "instantane" au pic de l'incident, statique vs adaptatif, avec
    # les flux reellement obtenus a ce round precis (pas de recalcul).
    blocked_graph_static = build_cotonou_graph()
    blocked_graph_adaptive = build_cotonou_graph()
    blocked_capacity = blockage["normal_capacity"] * 0.15
    blocked_graph_static.edges[BRIDGE_EDGE]["capacity"] = blocked_capacity
    blocked_graph_adaptive.edges[BRIDGE_EDGE]["capacity"] = blocked_capacity

    peak_static_flows = blockage["static_flows_by_round"][PEAK_ROUND - 1]
    peak_adaptive_flows = blockage["adaptive_flows_by_round"][PEAK_ROUND - 1]

    plot_network_map(
        blocked_graph_static, peak_static_flows, f"{RESULTS_DIR}/network_map_blockage_static.png",
        f"Pont bloqué (round {PEAK_ROUND}) — routage statique",
    )
    plot_network_map(
        blocked_graph_adaptive, peak_adaptive_flows, f"{RESULTS_DIR}/network_map_blockage_adaptive.png",
        f"Pont bloqué (round {PEAK_ROUND}) — routage adaptatif",
    )

    print(f"\nCartes et graphiques sauvegardes dans {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
