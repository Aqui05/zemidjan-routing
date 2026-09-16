"""
Exporte les donnees de la simulation (reseau + evolution round par round)
en JSON, consomme par web/index.html pour la carte interactive Leaflet.
"""
from __future__ import annotations

import json
import os

from network import LOCATIONS, build_cotonou_graph
from simulator import run_bridge_blockage_scenario

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web", "data.json")


def _edge_key(u: str, v: str) -> str:
    return "|".join(sorted((u, v)))


def export_demo_data(rounds: int = 40, blockage_start: int = 15, blockage_end: int = 25, seed: int = 7) -> None:
    graph = build_cotonou_graph()
    result = run_bridge_blockage_scenario(
        rounds=rounds, blockage_start=blockage_start, blockage_end=blockage_end, seed=seed,
    )

    edges = [
        {"u": u, "v": v, "capacity": data["capacity"], "free_flow_time": data["free_flow_time"]}
        for u, v, data in graph.edges(data=True)
    ]

    rounds_data = []
    for i in range(rounds):
        blocked = blockage_start <= (i + 1) <= blockage_end
        entry = {"round": i + 1, "blocked": blocked}
        for scenario in ("static", "adaptive"):
            flows = result[f"{scenario}_flows_by_round"][i]
            paths = result[f"{scenario}_paths_by_round"][i]
            entry[scenario] = {
                "flows": {_edge_key(*tuple(k)): v for k, v in flows.items()},
                "avg_time": result["history"][scenario]["avg_time"][i],
                "paths": paths,
            }
        rounds_data.append(entry)

    dataset = {
        "nodes": {name: {"lat": lat, "lon": lon} for name, (lat, lon) in LOCATIONS.items()},
        "edges": edges,
        "blockage_start": blockage_start,
        "blockage_end": blockage_end,
        "bridge_edge": ["ganhi", "akpakpa"],
        "rounds": rounds_data,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False)

    print(f"Donnees exportees vers {OUTPUT_PATH} ({os.path.getsize(OUTPUT_PATH) / 1024:.1f} Ko)")


if __name__ == "__main__":
    export_demo_data()
