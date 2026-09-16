"""
Scenarios :

1. `run_static_vs_adaptive` : sur plusieurs rounds (vagues de trajets
   successives, ex. tranches de 5 minutes en heure de pointe), on compare
   un routage statique (itineraire fige, jamais mis a jour) a un routage
   adaptatif ou chaque trajet choisit sa route en fonction de la
   congestion observee au round precedent (comme une appli de nav qui
   reagit a l'etat du trafic recent, sans autorite centrale qui decide a
   la place des usagers).

2. `run_bridge_blockage_scenario` : le pont reliant Akpakpa au reste de la
   ville voit sa capacite chuter brutalement (accident, blocage) pendant
   plusieurs rounds, puis revient a la normale -- on mesure la capacite du
   systeme adaptatif a s'en detourner de lui-meme.
"""
from __future__ import annotations

import random
from collections import defaultdict

import networkx as nx

from metrics import average_travel_time, congestion_stddev
from network import EAST_BANK, WEST_BANK, build_cotonou_graph
from routing import adaptive_shortest_path, path_travel_time, static_shortest_path


def _generate_trips(rng: random.Random, n_trips: int, cross_lagoon_bias: float = 0.35) -> list[tuple[str, str]]:
    """Genere des paires origine/destination. Biaise volontairement vers
    des trajets traversant la lagune : Akpakpa est un quartier residentiel
    tres peuple dont une grande partie des habitants travaillent de
    l'autre cote de la lagune -- un facteur reel de congestion du pont.
    """
    west = list(WEST_BANK)
    east = list(EAST_BANK)
    trips = []
    for _ in range(n_trips):
        if rng.random() < cross_lagoon_bias:
            source, target = rng.choice(east), rng.choice(west)
        else:
            pool = west if rng.random() < 0.85 else east
            source, target = rng.sample(pool, 2) if len(pool) >= 2 else (rng.choice(east), rng.choice(west))
        if source != target:
            trips.append((source, target))
    return trips


def _accumulate_flow(graph: nx.Graph, paths: list[list[str]]) -> dict:
    flows: dict[frozenset, float] = defaultdict(float)
    for path in paths:
        for u, v in zip(path, path[1:]):
            flows[frozenset((u, v))] += 1.0
    return flows


def _route_trip(
    graph: nx.Graph, source: str, target: str, previous_flows: dict,
    rng: random.Random, adoption_rate: float,
) -> list[str]:
    """Decision de routage d'un trajet individuel. Seule une fraction
    (adoption_rate) des conducteurs a une info trafic recente et accepte de
    devier de son trajet habituel ; les autres restent sur le trajet
    statique. Ca amortit la reaction collective : au lieu que 100% du trafic
    bascule d'un coup des qu'un axe semble charge (effet de troupeau), seule
    une partie se redirige a chaque round -- le meme principe que le taux de
    diffusion (ALPHA) utilise dans AgentBalance pour eviter les a-coups.
    """
    if rng.random() < adoption_rate:
        return adaptive_shortest_path(graph, source, target, previous_flows)
    return static_shortest_path(graph, source, target)


def run_static_vs_adaptive(
    rounds: int = 30, trips_per_round: int = 60, seed: int = 42, adoption_rate: float = 0.3,
) -> dict:
    graph = build_cotonou_graph()
    rng_static = random.Random(seed)
    rng_adaptive = random.Random(seed)  # meme graine -> memes trajets, comparaison equitable
    rng_adoption = random.Random(seed + 100)

    previous_flows: dict = {}
    history = {"static": [], "adaptive": []}
    last_static_flows: dict = {}
    last_adaptive_flows: dict = {}

    for _ in range(rounds):
        static_trips = _generate_trips(rng_static, trips_per_round)
        static_paths = [static_shortest_path(graph, s, t) for s, t in static_trips]
        last_static_flows = _accumulate_flow(graph, static_paths)
        static_times = [path_travel_time(graph, p, last_static_flows) for p in static_paths]
        history["static"].append({
            "avg_travel_time": average_travel_time(static_times),
            "congestion_stddev": congestion_stddev(graph, last_static_flows),
        })

        adaptive_trips = _generate_trips(rng_adaptive, trips_per_round)
        adaptive_paths = [
            _route_trip(graph, s, t, previous_flows, rng_adoption, adoption_rate)
            for s, t in adaptive_trips
        ]
        last_adaptive_flows = _accumulate_flow(graph, adaptive_paths)
        adaptive_times = [path_travel_time(graph, p, last_adaptive_flows) for p in adaptive_paths]
        history["adaptive"].append({
            "avg_travel_time": average_travel_time(adaptive_times),
            "congestion_stddev": congestion_stddev(graph, last_adaptive_flows),
        })
        previous_flows = last_adaptive_flows

    return {
        "graph": graph,
        "history": history,
        "final_static_flows": last_static_flows,
        "final_adaptive_flows": last_adaptive_flows,
    }


def run_bridge_blockage_scenario(
    rounds: int = 40,
    trips_per_round: int = 60,
    blockage_start: int = 15,
    blockage_end: int = 25,
    seed: int = 7,
    adoption_rate: float = 0.3,
) -> dict:
    """Meme incident (accident sur le pont) rejoue en parallele pour les
    deux strategies, avec le meme flux de trajets (graine partagee) --
    seule la strategie de routage differe. `adoption_rate` controle la part
    des trajets qui reagissent a la congestion observee a chaque round (le
    reste garde son trajet habituel) -- amortit l'effet de troupeau.
    """
    graph_static = build_cotonou_graph()
    graph_adaptive = build_cotonou_graph()
    bridge_edge = ("ganhi", "akpakpa")
    normal_capacity = graph_static.edges[bridge_edge]["capacity"]

    rng_static = random.Random(seed)
    rng_adaptive = random.Random(seed)
    rng_adoption = random.Random(seed + 100)
    previous_flows: dict = {}

    history = {"static": {"avg_time": [], "bridge_flow": []}, "adaptive": {"avg_time": [], "bridge_flow": []}}
    static_flows_by_round: list[dict] = []
    adaptive_flows_by_round: list[dict] = []
    static_paths_by_round: list[list] = []
    adaptive_paths_by_round: list[list] = []

    for round_idx in range(1, rounds + 1):
        blocked = blockage_start <= round_idx <= blockage_end
        capacity_now = normal_capacity * 0.15 if blocked else normal_capacity
        graph_static.edges[bridge_edge]["capacity"] = capacity_now
        graph_adaptive.edges[bridge_edge]["capacity"] = capacity_now

        static_trips = _generate_trips(rng_static, trips_per_round)
        static_paths = [static_shortest_path(graph_static, s, t) for s, t in static_trips]
        static_flows = _accumulate_flow(graph_static, static_paths)
        static_times = [path_travel_time(graph_static, p, static_flows) for p in static_paths]
        history["static"]["avg_time"].append(average_travel_time(static_times))
        history["static"]["bridge_flow"].append(static_flows.get(frozenset(bridge_edge), 0.0))
        static_flows_by_round.append(static_flows)
        static_paths_by_round.append(static_paths[:25])  # echantillon, suffisant pour l'animation

        adaptive_trips = _generate_trips(rng_adaptive, trips_per_round)
        adaptive_paths = [
            _route_trip(graph_adaptive, s, t, previous_flows, rng_adoption, adoption_rate)
            for s, t in adaptive_trips
        ]
        adaptive_flows = _accumulate_flow(graph_adaptive, adaptive_paths)
        adaptive_times = [path_travel_time(graph_adaptive, p, adaptive_flows) for p in adaptive_paths]
        history["adaptive"]["avg_time"].append(average_travel_time(adaptive_times))
        history["adaptive"]["bridge_flow"].append(adaptive_flows.get(frozenset(bridge_edge), 0.0))
        adaptive_flows_by_round.append(adaptive_flows)
        adaptive_paths_by_round.append(adaptive_paths[:25])
        previous_flows = adaptive_flows

    return {
        "history": history,
        "blockage_start": blockage_start,
        "blockage_end": blockage_end,
        "normal_capacity": normal_capacity,
        "static_flows_by_round": static_flows_by_round,
        "adaptive_flows_by_round": adaptive_flows_by_round,
        "static_paths_by_round": static_paths_by_round,
        "adaptive_paths_by_round": adaptive_paths_by_round,
    }
