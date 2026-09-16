<template>
  <div class="relative w-full h-full">
    <div ref="mapEl" class="w-full h-full rounded-lg overflow-hidden"></div>
    <div
      class="absolute bottom-2 left-2 z-[1000] bg-white/95 rounded px-2 py-1 text-[10px] text-gray-500 flex items-center gap-1.5 shadow"
    >
      <span
        class="w-1.5 h-1.5 rounded-full"
        :class="roadsLoaded ? 'bg-primary' : 'bg-warning'"
      ></span>
      {{ roadStatusText }}
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, watch, ref } from "vue";
import L from "leaflet";
import { loadRealRoadsSequentially } from "../roads.js";

const props = defineProps({
  network: { type: Object, required: true },
  flows: { type: Object, default: () => ({}) },
  paths: { type: Array, default: () => [] },
});

const mapEl = ref(null);
const roadsLoaded = ref(false);
const roadStatusText = ref("Tracé des routes en ligne droite (provisoire)");
let map = null;
const edgeLayers = {}; // "u|v" -> { line, capacity, isBridge }
const vehicleMarkers = [];
let animGeneration = 0;
let vehicleAnimHandle = null;

function edgeKey(u, v) {
  return [u, v].sort().join("|");
}

function congestionColor(ratio) {
  const r = Math.max(0, Math.min(1, ratio));
  const stops = [
    [0.0, [26, 152, 80]],
    [0.5, [254, 224, 139]],
    [1.0, [215, 48, 39]],
  ];
  for (let i = 0; i < stops.length - 1; i++) {
    const [p0, c0] = stops[i], [p1, c1] = stops[i + 1];
    if (r >= p0 && r <= p1) {
      const t = (r - p0) / (p1 - p0);
      const c = c0.map((v, idx) => Math.round(v + t * (c1[idx] - v)));
      return `rgb(${c[0]},${c[1]},${c[2]})`;
    }
  }
  return "rgb(215,48,39)";
}

function initMap() {
  map = L.map(mapEl.value, { zoomControl: false }).setView([6.375, 2.41], 12.3);
  L.control.zoom({ position: "topright" }).addTo(map);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors &middot; itinéraires via OSRM",
    maxZoom: 18,
  }).addTo(map);

  const bounds = [];
  for (const [name, pos] of Object.entries(props.network.nodes)) {
    bounds.push([pos.lat, pos.lon]);
    L.circleMarker([pos.lat, pos.lon], {
      radius: 5, color: "#fff", weight: 1.5, fillColor: "#1A1F1D", fillOpacity: 1,
    }).addTo(map).bindTooltip(
      name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      { direction: "top" },
    );
  }
  map.fitBounds(bounds, { padding: [30, 30] });

  const [bu, bv] = props.network.bridge_edge;
  for (const edge of props.network.edges) {
    const posU = props.network.nodes[edge.u], posV = props.network.nodes[edge.v];
    const isBridge = (edge.u === bu && edge.v === bv) || (edge.v === bu && edge.u === bv);
    const line = L.polyline(
      [[posU.lat, posU.lon], [posV.lat, posV.lon]],
      { color: "#1a9850", weight: isBridge ? 5 : 2.5, opacity: 0.75, lineCap: "round" },
    ).addTo(map);
    if (isBridge) line.bindTooltip("Pont Ganhi ↔ Akpakpa (goulot d'étranglement)");
    edgeLayers[edgeKey(edge.u, edge.v)] = { line, capacity: edge.capacity, isBridge };
  }

  loadRealRoadsSequentially(
    props.network.edges,
    props.network.nodes,
    (edge, latlngs) => edgeLayers[edgeKey(edge.u, edge.v)].line.setLatLngs(latlngs),
    (done, total) => {
      roadStatusText.value = done < total
        ? `Chargement des tracés routiers réels… (${done}/${total})`
        : "Tracés routiers réels chargés (via OSRM)";
      if (done === total) roadsLoaded.value = true;
    },
  );
}

function updateEdgeColors() {
  for (const [key, entry] of Object.entries(edgeLayers)) {
    const flow = props.flows[key] || 0;
    const ratio = flow / entry.capacity;
    entry.line.setStyle({
      color: congestionColor(ratio),
      weight: (entry.isBridge ? 5 : 2.5) + Math.min(3, ratio * 3),
      opacity: 0.75 + Math.min(0.2, ratio * 0.2),
    });
  }
}

function animatePaths() {
  const myGeneration = ++animGeneration;
  vehicleMarkers.forEach((m) => map.removeLayer(m));
  vehicleMarkers.length = 0;
  if (vehicleAnimHandle) { cancelAnimationFrame(vehicleAnimHandle); vehicleAnimHandle = null; }

  const sample = (props.paths || []).slice(0, 12);
  if (sample.length === 0) return;

  const runners = sample.map((path) => {
    // Suit le trace routier reel de chaque troncon (deja charge ou non),
    // pour que les marqueurs animes restent visuellement colles aux routes
    // affichees plutot que de couper au plus court entre les noeuds.
    const latlngs = [];
    for (let i = 0; i < path.length - 1; i++) {
      const entry = edgeLayers[edgeKey(path[i], path[i + 1])];
      const nodeStart = props.network.nodes[path[i]];
      if (!entry) {
        latlngs.push([nodeStart.lat, nodeStart.lon]);
        continue;
      }
      const segment = entry.line.getLatLngs();
      const distToFirst = L.latLng(nodeStart.lat, nodeStart.lon).distanceTo(segment[0]);
      const distToLast = L.latLng(nodeStart.lat, nodeStart.lon).distanceTo(segment[segment.length - 1]);
      const ordered = distToFirst <= distToLast ? segment : [...segment].reverse();
      latlngs.push(...ordered.map((p) => [p.lat, p.lng]));
    }

    const marker = L.circleMarker(latlngs[0], {
      radius: 5, color: "#fff", weight: 1.5, fillColor: "#ff7f0e", fillOpacity: 1,
    }).addTo(map);
    vehicleMarkers.push(marker);
    return { latlngs, marker, idx: 0, t: 0 };
  });

  const POINT_DURATION = 220;
  let lastTs = null;

  function step(ts) {
    if (myGeneration !== animGeneration) return;
    if (lastTs === null) lastTs = ts;
    const dt = ts - lastTs;
    lastTs = ts;

    let anyActive = false;
    for (const r of runners) {
      if (r.latlngs.length < 2 || r.idx >= r.latlngs.length - 1) continue;
      anyActive = true;
      r.t += dt / POINT_DURATION;
      if (r.t >= 1) {
        r.t = 0;
        r.idx += 1;
        if (r.idx >= r.latlngs.length - 1) { r.marker.setLatLng(r.latlngs[r.latlngs.length - 1]); continue; }
      }
      const a = r.latlngs[r.idx], b = r.latlngs[r.idx + 1];
      r.marker.setLatLng([a[0] + (b[0] - a[0]) * r.t, a[1] + (b[1] - a[1]) * r.t]);
    }
    if (anyActive) {
      vehicleAnimHandle = requestAnimationFrame(step);
    } else {
      setTimeout(() => { if (myGeneration === animGeneration) animatePaths(); }, 600);
    }
  }
  vehicleAnimHandle = requestAnimationFrame(step);
}

onMounted(() => {
  initMap();
  updateEdgeColors();
  animatePaths();
});

onBeforeUnmount(() => {
  animGeneration += 1;
  if (vehicleAnimHandle) cancelAnimationFrame(vehicleAnimHandle);
  if (map) map.remove();
});

watch(() => props.flows, updateEdgeColors);
watch(() => props.paths, animatePaths);
</script>
