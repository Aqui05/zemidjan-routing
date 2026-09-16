"""
API du backend Zemidjan Routing.

Expose les scenarios de simulation (deja utilises par main.py pour generer
des images statiques) sous forme d'endpoints JSON, consommes par le
frontend Vue. Le coeur de la simulation (network.py, routing.py,
simulator.py, metrics.py) n'est pas duplique : ce module l'importe
directement depuis src/, copie dans l'image Docker a cote de app/
(voir backend/Dockerfile).
"""
from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from network import LOCATIONS, build_cotonou_graph
from simulator import run_bridge_blockage_scenario, run_static_vs_adaptive

app = FastAPI(title="Zemidjan Routing API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo : a restreindre a l'origine du frontend en production
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serialize_flows(flows: dict) -> dict:
    """Les cles frozenset({u, v}) ne sont pas serialisables en JSON --
    on les convertit en chaine 'u|v' triee, meme convention que le
    frontend (voir src/api.js:edgeKey)."""
    return {"|".join(sorted(k)): v for k, v in flows.items()}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/network")
def get_network():
    graph = build_cotonou_graph()
    nodes = {name: {"lat": lat, "lon": lon} for name, (lat, lon) in LOCATIONS.items()}
    edges = [
        {"u": u, "v": v, "capacity": data["capacity"], "free_flow_time": data["free_flow_time"]}
        for u, v, data in graph.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges, "bridge_edge": ["ganhi", "akpakpa"]}


@app.get("/api/scenario/normal")
def scenario_normal(
    rounds: int = Query(30, ge=5, le=200),
    trips_per_round: int = Query(60, ge=5, le=300),
    seed: int = 42,
    adoption_rate: float = Query(0.3, ge=0.0, le=1.0),
):
    result = run_static_vs_adaptive(
        rounds=rounds, trips_per_round=trips_per_round, seed=seed, adoption_rate=adoption_rate,
    )
    return {"history": result["history"]}


@app.get("/api/scenario/blockage")
def scenario_blockage(
    rounds: int = Query(40, ge=10, le=200),
    trips_per_round: int = Query(60, ge=5, le=300),
    blockage_start: int = Query(15, ge=1),
    blockage_end: int = Query(25, ge=1),
    seed: int = 7,
    adoption_rate: float = Query(0.3, ge=0.0, le=1.0),
):
    result = run_bridge_blockage_scenario(
        rounds=rounds, trips_per_round=trips_per_round,
        blockage_start=blockage_start, blockage_end=blockage_end,
        seed=seed, adoption_rate=adoption_rate,
    )
    return {
        "history": result["history"],
        "blockage_start": result["blockage_start"],
        "blockage_end": result["blockage_end"],
        "normal_capacity": result["normal_capacity"],
        "static_flows_by_round": [_serialize_flows(f) for f in result["static_flows_by_round"]],
        "adaptive_flows_by_round": [_serialize_flows(f) for f in result["adaptive_flows_by_round"]],
        "static_paths_by_round": result["static_paths_by_round"],
        "adaptive_paths_by_round": result["adaptive_paths_by_round"],
    }
