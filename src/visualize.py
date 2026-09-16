"""
Genere :
  - une carte schematique du reseau de Cotonou (noeuds positionnes a leurs
    vraies coordonnees GPS), avec la congestion de chaque axe en couleur
  - les graphiques de comparaison statique vs adaptatif

Pas de fond de carte satellite/tuiles (pas d'acces reseau dans cet
environnement) -- les noeuds sont places directement a leurs coordonnees
(longitude, latitude) reelles, ce qui donne deja une carte fidele a la
geographie relative de Cotonou.
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import networkx as nx

from network import EAST_BANK, LOCATIONS


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _node_positions() -> dict:
    return {name: (lon, lat) for name, (lat, lon) in LOCATIONS.items()}


def plot_network_map(graph: nx.Graph, flows: dict, out_path: str, title: str) -> None:
    """Carte du reseau avec la congestion de chaque axe en couleur
    (vert = fluide, rouge = sature) et l'epaisseur proportionnelle a la
    capacite. Le pont et la route de contournement sont annotes.
    """
    pos = _node_positions()
    fig, ax = plt.subplots(figsize=(9, 8))

    cmap = plt.get_cmap("RdYlGn_r")
    for u, v, data in graph.edges(data=True):
        flow = flows.get(frozenset((u, v)), 0.0)
        ratio = min(flow / data["capacity"], 1.5)
        color = cmap(min(ratio, 1.0))
        width = 1.5 + 3 * (data["capacity"] / 120)
        x = [pos[u][0], pos[v][0]]
        y = [pos[u][1], pos[v][1]]
        ax.plot(x, y, color=color, linewidth=width, solid_capstyle="round", zorder=1)

    for name, (lon, lat) in pos.items():
        is_east = name in EAST_BANK
        ax.scatter(lon, lat, s=90, color="#1A1F1D", zorder=3)
        ax.annotate(
            name.replace("_", " "), (lon, lat),
            textcoords="offset points", xytext=(6, 4), fontsize=8,
            color="#2E7DD1" if is_east else "#1A1F1D",
        )

    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    legend_elements = [
        Line2D([0], [0], color=cmap(0.05), lw=3, label="Fluide"),
        Line2D([0], [0], color=cmap(0.6), lw=3, label="Chargé"),
        Line2D([0], [0], color=cmap(1.0), lw=3, label="Saturé / embouteillé"),
    ]
    ax.legend(handles=legend_elements, loc="lower left")

    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_blockage_comparison(history: dict, blockage_start: int, blockage_end: int, out_path: str) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    ax1 = axes[0]
    ax1.plot(range(1, len(history["static"]["avg_time"]) + 1), history["static"]["avg_time"],
              label="Statique (itinéraire figé)", color="#D34C4C")
    ax1.plot(range(1, len(history["adaptive"]["avg_time"]) + 1), history["adaptive"]["avg_time"],
              label="Adaptatif (routage réactif)", color="#1B8A5A")
    ax1.axvspan(blockage_start, blockage_end, color="#E0A100", alpha=0.15, label="Pont bloqué")
    ax1.set_ylabel("Temps de trajet moyen (min)")
    ax1.set_title("Impact du blocage du pont sur le temps de trajet moyen")
    ax1.legend()

    ax2 = axes[1]
    ax2.plot(range(1, len(history["static"]["bridge_flow"]) + 1), history["static"]["bridge_flow"],
              label="Statique", color="#D34C4C")
    ax2.plot(range(1, len(history["adaptive"]["bridge_flow"]) + 1), history["adaptive"]["bridge_flow"],
              label="Adaptatif", color="#1B8A5A")
    ax2.axvspan(blockage_start, blockage_end, color="#E0A100", alpha=0.15)
    ax2.set_xlabel("Round (vague de trajets)")
    ax2.set_ylabel("Trajets empruntant le pont")
    ax2.set_title("Trafic sur le pont pendant l'incident")
    ax2.legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
