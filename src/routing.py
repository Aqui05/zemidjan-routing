"""
Modele de congestion et routage.

La fonction de cout utilisee est la fonction BPR (Bureau of Public Roads),
un standard en ingenierie du trafic pour relier le flux sur un axe a son
temps de parcours reel :

    temps(flux) = temps_libre * (1 + ALPHA * (flux / capacite) ** BETA)

Plus un axe est proche (ou au-dela) de sa capacite, plus le temps de
parcours augmente rapidement (effet non-lineaire, BETA=4 dans la
litterature). C'est ce qui permet de modeliser un embouteillage de facon
realiste plutot qu'une simple penalite lineaire.
"""
from __future__ import annotations

import networkx as nx

ALPHA = 0.15
BETA = 4


def travel_time(graph: nx.Graph, u, v, flow: float) -> float:
    data = graph.edges[u, v]
    free_flow = data["free_flow_time"]
    capacity = data["capacity"]
    return free_flow * (1 + ALPHA * (flow / capacity) ** BETA)


def static_shortest_path(graph: nx.Graph, source, target) -> list:
    """Itineraire fige, calcule une seule fois sur les temps a vitesse
    libre -- ignore totalement l'etat reel du trafic. C'est la baseline
    "sans coordination" : chaque zemidjan suit toujours le meme trajet
    habituel, quelle que soit la congestion du moment.
    """
    return nx.shortest_path(graph, source, target, weight="free_flow_time")


def adaptive_shortest_path(graph: nx.Graph, source, target, current_flows: dict) -> list:
    """Itineraire recalcule a partir de l'etat de congestion COURANT et
    LOCALEMENT observable (le flux actuel sur chaque axe). Chaque trajet
    est une decision autonome et independante -- il n'y a pas de
    controleur central qui impose un plan de circulation global, chaque
    "agent-trajet" reagit simplement a ce qu'il observe sur le reseau au
    moment ou il part.
    """
    def weight(u, v, _data):
        flow = current_flows.get(frozenset((u, v)), 0.0)
        return travel_time(graph, u, v, flow)

    return nx.shortest_path(graph, source, target, weight=weight)


def path_travel_time(graph: nx.Graph, path: list, flows: dict) -> float:
    total = 0.0
    for u, v in zip(path, path[1:]):
        flow = flows.get(frozenset((u, v)), 0.0)
        total += travel_time(graph, u, v, flow)
    return total
