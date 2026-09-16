const BASE = "/api";

async function getJSON(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status} on ${path}`);
  return res.json();
}

export function edgeKey(u, v) {
  return [u, v].sort().join("|");
}

export function fetchNetwork() {
  return getJSON("/network");
}

export function fetchBlockageScenario({
  rounds = 40, tripsPerRound = 60, blockageStart = 15, blockageEnd = 25, seed = 7, adoptionRate = 0.3,
} = {}) {
  const params = new URLSearchParams({
    rounds, trips_per_round: tripsPerRound, blockage_start: blockageStart,
    blockage_end: blockageEnd, seed, adoption_rate: adoptionRate,
  });
  return getJSON(`/scenario/blockage?${params}`);
}
