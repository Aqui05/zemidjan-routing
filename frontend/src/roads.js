// Recupere le trace routier reel entre deux points via l'API publique OSRM,
// appelee depuis le navigateur (pas depuis un serveur) -- ce module ne fait
// que mettre en forme des requetes fetch() standard.
//
// Le serveur de demo public OSRM n'offre aucune garantie de disponibilite
// ou de debit : convient pour une demo, pas pour de la production (voir
// le README pour une alternative auto-hebergee).
const ROUTING_API = "https://router.project-osrm.org/route/v1/driving";

export async function fetchRoadGeometry(posU, posV) {
  const coordsStr = `${posU.lon},${posU.lat};${posV.lon},${posV.lat}`;
  const res = await fetch(`${ROUTING_API}/${coordsStr}?overview=full&geometries=geojson`);
  if (!res.ok) throw new Error(`OSRM HTTP ${res.status}`);
  const data = await res.json();
  const coords = data.routes?.[0]?.geometry?.coordinates;
  if (!coords || coords.length < 2) throw new Error("Pas de tracé retourné");
  return coords.map(([lon, lat]) => [lat, lon]);
}

/**
 * Charge les traces reels pour une liste d'aretes, une par une (par
 * courtoisie envers le service gratuit), et appelle onEdgeLoaded(edge,
 * latlngs) a chaque succes. Les echecs individuels sont silencieux : la
 * ligne droite reste affichee pour cette arete-la.
 */
export async function loadRealRoadsSequentially(edges, nodes, onEdgeLoaded, onProgress) {
  let done = 0;
  for (const edge of edges) {
    try {
      const latlngs = await fetchRoadGeometry(nodes[edge.u], nodes[edge.v]);
      onEdgeLoaded(edge, latlngs);
    } catch (e) {
      console.warn(`Tracé réel indisponible pour ${edge.u} ↔ ${edge.v}, ligne droite conservée.`, e);
    }
    done += 1;
    onProgress?.(done, edges.length);
  }
}
