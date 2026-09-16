"""
Reseau routier de Cotonou.

IMPORTANT : faute d'acces reseau a Overpass/OpenStreetMap dans cet
environnement, ce graphe est construit a la main a partir de coordonnees
GPS reelles de quartiers/carrefours connus de Cotonou, relies selon les
grands axes reels (dans la mesure du raisonnable). Ce n'est PAS un export
osmnx precis rue par rue -- c'est un graphe schematique mais geographiquement
fonde, suffisant pour demontrer l'algorithme. `load_from_graphml()` permet
de brancher un vrai export osmnx (fait chez soi, avec acces internet complet)
sans changer une ligne du reste du code.

Le point notable : la lagune de Cotonou separe Akpakpa (est) du reste de la
ville. Tout le trafic entre les deux doit passer par un nombre tres limite
de ponts -- un goulot d'etranglement reel et bien connu, utilise ici comme
scenario de blocage.
"""
from __future__ import annotations

import math

import networkx as nx

# (nom, latitude, longitude) -- coordonnees approximatives de quartiers/
# carrefours reels de Cotonou.
LOCATIONS = {
    "dantokpa": (6.3667, 2.4333),      # grand marche, rive ouest de la lagune
    "ganhi": (6.3620, 2.4280),
    "missebo": (6.3670, 2.4290),
    "etoile_rouge": (6.3628, 2.4183),
    "gare_jonquet": (6.3600, 2.4300),
    "camp_guezo": (6.3550, 2.4180),
    "zogbo": (6.3700, 2.4100),
    "sainte_rita": (6.3500, 2.4020),
    "cadjehoun": (6.3570, 2.3840),      # aeroport
    "fidjrosse": (6.3480, 2.3780),
    "vedoko": (6.3800, 2.3900),
    "agla": (6.3750, 2.3950),
    "godomey": (6.3950, 2.3450),
    "calavi": (6.4489, 2.3550),
    "akpakpa": (6.3650, 2.4550),        # rive est de la lagune
    "placodji": (6.3700, 2.4450),
}

# Les deux rives de la lagune : aucune route directe ne les relie hormis les
# ponts explicites (BRIDGE_EDGES) -- sans cette separation, le plus-proche-
# voisin connecterait des noeuds "a vol d'oiseau" en travers de la lagune,
# ce qui n'existe pas dans la realite.
EAST_BANK = {"akpakpa", "placodji"}
WEST_BANK = set(LOCATIONS) - EAST_BANK

# Pont(s) reliant les deux rives de la lagune -- LE goulot d'etranglement.
# Capacite volontairement faible par rapport aux autres axes.
BRIDGE_EDGES = [("ganhi", "akpakpa")]

# Alternative reelle mais tres longue : contourner la lagune/le lac Nokoue
# par le nord (axe Godomey/Calavi) plutot que de traverser directement.
# Personne ne l'emprunte en temps normal (bien trop long), mais elle existe
# et redevient interessante si le pont est bloque. Sans cette alternative,
# meme un algorithme "adaptatif" n'aurait strictement aucun choix a faire.
DETOUR_EDGES = [("godomey", "akpakpa", 55.0, 100)]  # (a, b, temps_libre_min, capacite)

K_NEAREST = 3  # chaque noeud est connecte a ses K voisins geographiques les plus proches (meme rive)


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def build_cotonou_graph(avg_speed_kmh: float = 25.0) -> nx.Graph:
    """Construit le graphe : chaque noeud relie a ses K plus proches voisins
    geographiques, plus les ponts explicites (goulot d'etranglement).
    Poids des aretes = temps de parcours a vitesse libre (minutes).
    """
    graph = nx.Graph()
    for name, (lat, lon) in LOCATIONS.items():
        graph.add_node(name, lat=lat, lon=lon)

    names = list(LOCATIONS.keys())
    for name in names:
        bank = EAST_BANK if name in EAST_BANK else WEST_BANK
        candidates = [n for n in bank if n != name]
        distances = sorted(
            ((other, haversine_km(LOCATIONS[name], LOCATIONS[other])) for other in candidates),
            key=lambda x: x[1],
        )
        for other, dist_km in distances[:K_NEAREST]:
            _add_road(graph, name, other, dist_km, avg_speed_kmh, capacity=120)

    for a, b in BRIDGE_EDGES:
        dist_km = haversine_km(LOCATIONS[a], LOCATIONS[b])
        # Le pont : plus lent (vitesse reduite, souvent a une voie dans chaque
        # sens) et surtout une capacite bien plus faible que les autres axes.
        _add_road(graph, a, b, dist_km, avg_speed_kmh=18.0, capacity=45)

    for a, b, free_flow_minutes, capacity in DETOUR_EDGES:
        graph.add_edge(a, b, length_km=None, free_flow_time=free_flow_minutes, capacity=capacity)

    return graph


def _add_road(graph: nx.Graph, a: str, b: str, dist_km: float, avg_speed_kmh: float, capacity: float) -> None:
    free_flow_minutes = (dist_km / avg_speed_kmh) * 60
    graph.add_edge(
        a, b,
        length_km=round(dist_km, 2),
        free_flow_time=round(free_flow_minutes, 2),
        capacity=capacity,
    )


def load_from_graphml(path: str) -> nx.Graph:
    """Charge un vrai reseau routier exporte via osmnx (ox.save_graphml).
    Attendu : aretes avec attributs 'free_flow_time' (minutes) et 'capacity'.
    A utiliser a la place de build_cotonou_graph() si on a un export osmnx
    reel de Cotonou (necessite un acces internet complet, indisponible ici).
    """
    return nx.read_graphml(path)
